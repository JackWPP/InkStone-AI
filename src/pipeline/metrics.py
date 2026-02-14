from __future__ import annotations

from pathlib import Path
from statistics import mean
from typing import Any

from src.core.io import read_jsonl, write_jsonl
from src.core.metrics_traditional import compute_traditional_row
from src.core.schema import DIMENSIONS


def _pearson(x: list[float], y: list[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    den_x = sum((xi - mx) ** 2 for xi in x) ** 0.5
    den_y = sum((yi - my) ** 2 for yi in y) ** 0.5
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / (den_x * den_y)


def _rank(values: list[float]) -> list[float]:
    pairs = sorted(enumerate(values), key=lambda p: p[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][1] == pairs[i][1]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[pairs[k][0]] = avg_rank
        i = j + 1
    return ranks


def _spearman(x: list[float], y: list[float]) -> float:
    return _pearson(_rank(x), _rank(y))


def _system_means(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, float]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["system_id"], []).append(row)
    out: dict[str, dict[str, float]] = {}
    for system_id, grows in grouped.items():
        out[system_id] = {
            dim: float(mean(int(r[key][dim]) for r in grows)) for dim in DIMENSIONS
        }
    return out


def run(config: dict[str, Any]) -> dict[str, Any]:
    processed = Path(config["paths"]["data_processed"])
    reference_source = str(config["run"].get("reference_source", "writer"))

    trans_rows = read_jsonl(processed / "translations.jsonl")
    judge_rows = read_jsonl(processed / "judge_scores.jsonl")
    gold_rows = read_jsonl(processed / "persona_gold.jsonl")

    judge_map = {(r["sid"], r["system_id"]): r for r in judge_rows}
    gold_map = {(r["sid"], r["system_id"]): r for r in gold_rows}

    mt_rows: list[dict[str, Any]] = []
    ov_gold_vals: list[float] = []
    ov_model_vals: list[float] = []
    by_dim_scores: dict[str, list[int]] = {d: [] for d in DIMENSIONS}
    bleu_vals: list[float] = []
    meteor_vals: list[float] = []

    for row in trans_rows:
        key = (row["sid"], row["system_id"])
        if key not in judge_map or key not in gold_map:
            continue
        gold = gold_map[key]
        model = judge_map[key]
        reference = f"Reference({reference_source}): {row['text_zh']}"
        trad = compute_traditional_row(reference, row["translation"], reference_source)
        mt_rows.append(
            {
                "sid": row["sid"],
                "system_id": row["system_id"],
                "bleu": trad["bleu"],
                "meteor": trad["meteor"],
                "reference_source": reference_source,
            }
        )
        ov_gold_vals.append(float(gold["OV_gold"]))
        ov_model_vals.append(float(model["OV_model"]))
        bleu_vals.append(float(trad["bleu"]))
        meteor_vals.append(float(trad["meteor"]))
        for d in DIMENSIONS:
            by_dim_scores[d].append(int(model["scores_model"][d]))

    write_jsonl(processed / "metrics_traditional.jsonl", mt_rows)

    corr = _spearman(ov_gold_vals, ov_model_vals) if ov_gold_vals else 0.0
    dim_corr: dict[str, dict[str, float]] = {}
    for dim in DIMENSIONS:
        if by_dim_scores[dim]:
            dim_vals = [float(v) for v in by_dim_scores[dim]]
            rho_bleu = _spearman(dim_vals, bleu_vals)
            rho_meteor = _spearman(dim_vals, meteor_vals)
            dim_corr[dim] = {"bleu": float(rho_bleu), "meteor": float(rho_meteor)}

    summary = {
        "human_model_spearman": float(corr),
        "human_model_pvalue": 1.0,
        "system_means": _system_means(judge_rows, "scores_model"),
        "dim_correlation": dim_corr,
    }
    write_jsonl(processed / "metrics_summary.jsonl", [summary])
    return summary


if __name__ == "__main__":
    from src.pipeline.config import load_config

    cfg = load_config("configs/systems.yaml")
    print(run(cfg))
