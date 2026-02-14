from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.io import read_jsonl, write_jsonl
from src.core.schema import DIMENSIONS


WEIGHTS = [0.25, 0.2, 0.25, 0.15, 0.15]


def _ov(scores: dict[str, int]) -> int:
    ordered = [scores[d] for d in DIMENSIONS]
    return int(round(sum(w * s for w, s in zip(WEIGHTS, ordered))))


def run(config: dict[str, Any]) -> dict[str, Any]:
    _ = config
    processed = Path(config["paths"]["data_processed"])
    persona_rows = read_jsonl(processed / "persona_gold.jsonl")

    out_rows: list[dict[str, Any]] = []
    for row in persona_rows:
        scores_gold = row["scores_gold"]
        # deterministic small perturbation to simulate model-judge behavior
        scores_model: dict[str, int] = {}
        for dim in DIMENSIONS:
            raw = int(scores_gold[dim])
            if raw < 5 and (sum(ord(c) for c in (row["sid"] + dim)) % 3 == 0):
                raw += 1
            scores_model[dim] = max(1, min(5, raw))
        out_rows.append(
            {
                "sid": row["sid"],
                "system_id": row["system_id"],
                "scores_model": scores_model,
                "OV_model": _ov(scores_model),
                "judge_prompt_version": config["judge"]["standard_model"].get(
                    "prompt_version", "judge_standard_v1_icl"
                ),
            }
        )

    out_path = processed / "judge_scores.jsonl"
    write_jsonl(out_path, out_rows)
    return {"rows": len(out_rows), "judge_scores": str(out_path)}


if __name__ == "__main__":
    from src.pipeline.config import load_config

    cfg = load_config("configs/systems.yaml")
    print(run(cfg))
