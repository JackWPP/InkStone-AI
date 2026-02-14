from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.io import read_jsonl, write_jsonl
from src.core.schema import DIMENSIONS


def run(config: dict[str, Any]) -> dict[str, Any]:
    _ = config
    processed = Path(config["paths"]["data_processed"])
    persona_rows = read_jsonl(processed / "persona_gold.jsonl")
    trans_rows = read_jsonl(processed / "translations.jsonl")
    trans_map = {(r["sid"], r["system_id"]): r for r in trans_rows}

    bank: list[dict[str, Any]] = []
    for row in persona_rows:
        ranges = row["range"]
        if row["OV_gold"] < 4:
            continue
        if max(int(ranges[d]) for d in DIMENSIONS) > 1:
            continue
        trow = trans_map[(row["sid"], row["system_id"])]
        bank.append(
            {
                "sid": row["sid"],
                "system_id": row["system_id"],
                "text_zh": trow["text_zh"],
                "translation": trow["translation"],
                "scores_gold": row["scores_gold"],
                "OV_gold": row["OV_gold"],
                "gold_rationale": "High-consistency pseudo gold sample.",
            }
        )

    out_path = processed / "few_shot_bank.jsonl"
    write_jsonl(out_path, bank)
    return {"rows": len(bank), "few_shot_bank": str(out_path)}


if __name__ == "__main__":
    from src.pipeline.config import load_config

    cfg = load_config("configs/systems.yaml")
    print(run(cfg))
