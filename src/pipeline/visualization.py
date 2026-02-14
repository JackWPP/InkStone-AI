from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.core.io import read_jsonl
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


def _save_fig(fig: plt.Figure, base: Path) -> None:
    base.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(base.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def _fig1(eval_rows: list[dict[str, Any]], fig_dir: Path) -> None:
    counts: dict[str, int] = {}
    for row in eval_rows:
        mtype = row["metaphor_meta"]["metaphor_type"]
        counts[mtype] = counts.get(mtype, 0) + 1
    labels = list(counts.keys())
    sizes = [counts[l] for l in labels]
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title("Fig1 Data Distribution")
    _save_fig(fig, fig_dir / "fig1_data_distribution")


def _fig2(
    persona_rows: list[dict[str, Any]], judge_rows: list[dict[str, Any]], fig_dir: Path
) -> tuple[float, float]:
    jmap = {(r["sid"], r["system_id"]): r for r in judge_rows}
    x, y = [], []
    for row in persona_rows:
        key = (row["sid"], row["system_id"])
        if key in jmap:
            x.append(float(row["OV_gold"]))
            y.append(float(jmap[key]["OV_model"]))
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(x, y, alpha=0.5)
    if len(x) >= 2 and len(set(x)) >= 2:
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        ax.plot(x, p(x), "r--", linewidth=1.5)
        r = _pearson(x, y)
        rho = _spearman(x, y)
    else:
        r, rho = 0.0, 0.0
    ax.set_xlabel("OV_gold")
    ax.set_ylabel("OV_model")
    ax.set_title(
        f"Fig2 Human-Model Correlation (Pearson r={r:.3f}, Spearman ρ={rho:.3f})"
    )
    _save_fig(fig, fig_dir / "fig2_human_model_correlation")
    return float(r), float(rho)


def _fig3(metrics_summary: dict[str, Any], fig_dir: Path) -> None:
    systems = metrics_summary.get("system_means", {})
    labels = DIMENSIONS
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"polar": True})
    for system_id, dims in systems.items():
        values = [float(dims[d]) for d in labels]
        values += values[:1]
        ax.plot(angles, values, label=system_id)
        ax.fill(angles, values, alpha=0.1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(1, 5)
    ax.set_title("Fig3 Radar System Comparison")
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1))
    _save_fig(fig, fig_dir / "fig3_radar_system_comparison")


def _fig4(metrics_summary: dict[str, Any], fig_dir: Path) -> None:
    corr = metrics_summary.get("dim_correlation", {})
    mat = np.array(
        [
            [corr.get(d, {}).get("bleu", 0.0), corr.get(d, {}).get("meteor", 0.0)]
            for d in DIMENSIONS
        ]
    )
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(mat, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_yticks(range(len(DIMENSIONS)))
    ax.set_yticklabels(DIMENSIONS)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["BLEU", "METEOR"])
    ax.set_title("Fig4 Metric Correlation Heatmap (Spearman)")
    fig.colorbar(im, ax=ax)
    _save_fig(fig, fig_dir / "fig4_metric_correlation_heatmap")


def run(config: dict[str, Any]) -> dict[str, Any]:
    plt.style.use("seaborn-v0_8")
    processed = Path(config["paths"]["data_processed"])
    fig_dir = Path(config["paths"]["reports_dir"]) / "figures"
    eval_rows = read_jsonl(processed / "eval_set.jsonl")
    persona_rows = read_jsonl(processed / "persona_gold.jsonl")
    judge_rows = read_jsonl(processed / "judge_scores.jsonl")
    summary_rows = read_jsonl(processed / "metrics_summary.jsonl")
    summary = summary_rows[0] if summary_rows else {}

    _fig1(eval_rows, fig_dir)
    r, rho = _fig2(persona_rows, judge_rows, fig_dir)
    _fig3(summary, fig_dir)
    _fig4(summary, fig_dir)
    return {"pearson_r": r, "spearman_rho": rho}


if __name__ == "__main__":
    from src.pipeline.config import load_config

    cfg = load_config("configs/systems.yaml")
    print(run(cfg))
