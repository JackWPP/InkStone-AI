from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.io import read_jsonl, write_jsonl
from src.core.schema import DIMENSIONS


PERSONAS = ["professor", "writer", "reader"]
WEIGHTS = [0.25, 0.2, 0.25, 0.15, 0.15]


def _score_seed(sid: str, system_id: str, persona: str) -> dict[str, int]:
    seed = sum(ord(c) for c in f"{sid}:{system_id}:{persona}")
    values: dict[str, int] = {}
    for i, dim in enumerate(DIMENSIONS):
        values[dim] = 1 + ((seed + i * 7) % 5)
    return values


def _ov(scores: dict[str, int]) -> int:
    ordered = [scores[d] for d in DIMENSIONS]
    return int(round(sum(w * s for w, s in zip(WEIGHTS, ordered))))


def run(config: dict[str, Any]) -> dict[str, Any]:
    _ = config
    processed = Path(config["paths"]["data_processed"])
    rows = read_jsonl(processed / "translations.jsonl")

    out_rows: list[dict[str, Any]] = []
    for row in rows:
        sid = row["sid"]
        system_id = row["system_id"]
        persona_scores = []
        for persona in PERSONAS:
            scores = _score_seed(sid, system_id, persona)
            persona_scores.append(scores)
        gold_scores: dict[str, int] = {}
        ranges: dict[str, int] = {}
        for dim in DIMENSIONS:
            vals = sorted(item[dim] for item in persona_scores)
            gold_scores[dim] = vals[1]
            ranges[dim] = vals[-1] - vals[0]
        out_rows.append(
            {
                "sid": sid,
                "system_id": system_id,
                "scores_gold": gold_scores,
                "OV_gold": _ov(gold_scores),
                "range": ranges,
            }
        )

    out_path = processed / "persona_gold.jsonl"
    write_jsonl(out_path, out_rows)
    return {"rows": len(out_rows), "persona_gold": str(out_path)}


if __name__ == "__main__":
    from src.pipeline.config import load_config

    cfg = load_config("configs/systems.yaml")
    print(run(cfg))
