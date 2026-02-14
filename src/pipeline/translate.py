from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from src.core.cache import TranslationCache
from src.core.io import read_jsonl, write_jsonl
from src.core.llm_client import chat_text, llm_config_from_dict


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

    out_rows: list[dict[str, Any]] = []
    for row in eval_rows:
        sid = row["sid"]
        text_zh = row["text_zh"]
        for system in systems:
            system_id = system["id"]
            prompt_version = system.get("prompt_version", "trans_v1")
            translated = cache.get(sid, system_id, prompt_version)
            if translated is None:
                if llm_enabled and str(system.get("kind")) == "llm":
                    llm_cfg = llm_config_from_dict(system)
                    system_prompt = _load_prompt(prompt_dir, prompt_version)
                    user_prompt = f"请把下面中文翻译成英文：\n{text_zh}"
                    llm_result = chat_text(llm_cfg, system_prompt, user_prompt)
                    translated = (
                        llm_result
                        if llm_result
                        else _mock_translate(text_zh, system_id)
                    )
                else:
                    translated = _mock_translate(text_zh, system_id)
                cache.set(sid, system_id, prompt_version, translated)
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
    return {"rows": len(out_rows), "translations": str(out_path)}


if __name__ == "__main__":
    from src.pipeline.config import load_config

    cfg = load_config("configs/systems.yaml")
    print(run(cfg))
