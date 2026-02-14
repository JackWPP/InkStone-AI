from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.cache import TranslationCache
from src.core.io import read_jsonl, write_jsonl


def _mock_translate(text_zh: str, system_id: str) -> str:
    base = text_zh.replace("（", "(").replace("）", ")")
    return f"[{system_id}] {base}"


def run(config: dict[str, Any]) -> dict[str, Any]:
    paths = config["paths"]
    systems = config["systems"]
    processed = Path(paths["data_processed"])
    eval_rows = read_jsonl(processed / "eval_set.jsonl")
    cache = TranslationCache(processed / "cache.sqlite3")

    out_rows: list[dict[str, Any]] = []
    for row in eval_rows:
        sid = row["sid"]
        text_zh = row["text_zh"]
        for system in systems:
            system_id = system["id"]
            prompt_version = system.get("prompt_version", "trans_v1")
            translated = cache.get(sid, system_id, prompt_version)
            if translated is None:
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
