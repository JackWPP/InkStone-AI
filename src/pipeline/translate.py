from __future__ import annotations

import importlib
import os
import time
from pathlib import Path
from typing import Any

from src.core.cache import TranslationCache
from src.core.io import read_jsonl, write_jsonl
from src.core.llm_client import chat_text, llm_config_from_dict


_HF_MODEL_CACHE: dict[str, Any] = {}


def _load_hf_model(model_name: str) -> Any | None:
    if model_name in _HF_MODEL_CACHE:
        return _HF_MODEL_CACHE[model_name]
    try:
        transformers_mod = importlib.import_module("transformers")
        pipeline_fn = getattr(transformers_mod, "pipeline")
        translator = pipeline_fn(task="translation", model=model_name)
        _HF_MODEL_CACHE[model_name] = translator
        return translator
    except Exception:
        try:
            transformers_mod = importlib.import_module("transformers")
            pipeline_fn = getattr(transformers_mod, "pipeline")
            translator = pipeline_fn(task="text2text-generation", model=model_name)
            _HF_MODEL_CACHE[model_name] = translator
            return translator
        except Exception:
            return None


def _hf_translate(model_name: str, text_zh: str) -> str | None:
    translator = _load_hf_model(model_name)
    if translator is None:
        return None
    try:
        result = translator(text_zh, max_new_tokens=256)
        if isinstance(result, list) and result:
            first = result[0]
            if isinstance(first, dict):
                if "translation_text" in first:
                    return str(first["translation_text"]).strip()
                if "generated_text" in first:
                    return str(first["generated_text"]).strip()
    except Exception:
        return None
    return None


def _mock_translate(text_zh: str, system_id: str) -> str:
    base = text_zh.replace("（", "(").replace("）", ")")
    return f"[{system_id}] {base}"


def _load_prompt(prompt_dir: Path, prompt_version: str) -> str:
    prompt_path = prompt_dir / f"{prompt_version}.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return (
        "你是一个中译英翻译器，请输出自然、准确、保留修辞意象的英文译文，仅返回译文。"
    )


def run(config: dict[str, Any]) -> dict[str, Any]:
    paths = config["paths"]
    systems = config["systems"]
    processed = Path(paths["data_processed"])
    prompt_dir = Path(paths["prompts_dir"])
    eval_rows = read_jsonl(processed / "eval_set.jsonl")
    cache = TranslationCache(processed / "cache.sqlite3")
    llm_enabled = os.getenv("INKSTONE_ENABLE_LLM", "0") == "1"
    hf_enabled = os.getenv("INKSTONE_ENABLE_HF", "0") == "1"
    t0 = time.time()

    stats = {
        "cache_hit": 0,
        "hf_success": 0,
        "llm_success": 0,
        "fallback_mock": 0,
    }

    out_rows: list[dict[str, Any]] = []
    for row in eval_rows:
        sid = row["sid"]
        text_zh = row["text_zh"]
        for system in systems:
            system_id = system["id"]
            prompt_version = system.get("prompt_version", "trans_v1")
            translated = cache.get(sid, system_id, prompt_version)
            if translated is None:
                used_mode = "fallback_mock"
                if hf_enabled and str(system.get("kind")) == "hf_nmt":
                    hf_result = _hf_translate(str(system.get("model", "")), text_zh)
                    if hf_result:
                        translated = hf_result
                        used_mode = "hf_success"
                    else:
                        translated = _mock_translate(text_zh, system_id)
                elif llm_enabled and str(system.get("kind")) == "llm":
                    llm_cfg = llm_config_from_dict(system)
                    system_prompt = _load_prompt(prompt_dir, prompt_version)
                    user_prompt = f"请把下面中文翻译成英文：\n{text_zh}"
                    llm_result = chat_text(llm_cfg, system_prompt, user_prompt)
                    translated = (
                        llm_result
                        if llm_result
                        else _mock_translate(text_zh, system_id)
                    )
                    if llm_result:
                        used_mode = "llm_success"
                else:
                    translated = _mock_translate(text_zh, system_id)

                cache.set(sid, system_id, prompt_version, translated)
                stats[used_mode] += 1
            else:
                stats["cache_hit"] += 1
            out_rows.append(
                {
                    "sid": sid,
                    "system_id": system_id,
                    "text_zh": text_zh,
                    "translation": translated,
                    "prompt_version": prompt_version,
                }
            )

    out_path = processed / "translations.jsonl"
    write_jsonl(out_path, out_rows)
    stats_path = processed / "translation_stats.jsonl"
    write_jsonl(
        stats_path,
        [
            {
                "rows": len(out_rows),
                "elapsed_sec": round(time.time() - t0, 3),
                "hf_enabled": hf_enabled,
                "llm_enabled": llm_enabled,
                **stats,
            }
        ],
    )
    return {
        "rows": len(out_rows),
        "translations": str(out_path),
        "translation_stats": str(stats_path),
    }


if __name__ == "__main__":
    from src.pipeline.config import load_config

    cfg = load_config("configs/systems.yaml")
    print(run(cfg))
