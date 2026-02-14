from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def read_jsonl_safe(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def load_dashboard_data(root: Path) -> dict[str, Any]:
    processed = root / "data" / "processed"
    reports = root / "reports"
    figures = reports / "figures"
    logs = reports / "logs"
    docs = root / "docs" / "methodology"

    summary_rows = read_jsonl_safe(processed / "metrics_summary.jsonl")
    summary = summary_rows[0] if summary_rows else {}

    figure_map = {
        "fig1": figures / "fig1_data_distribution.png",
        "fig2": figures / "fig2_human_model_correlation.png",
        "fig3": figures / "fig3_radar_system_comparison.png",
        "fig4": figures / "fig4_metric_correlation_heatmap.png",
    }

    result: dict[str, Any] = {
        "summary": summary,
        "files": {
            "eval_set": processed / "eval_set.jsonl",
            "translations": processed / "translations.jsonl",
            "persona_gold": processed / "persona_gold.jsonl",
            "judge_scores": processed / "judge_scores.jsonl",
            "metrics_traditional": processed / "metrics_traditional.jsonl",
            "data_quality": processed / "data_quality.jsonl",
            "freeze_manifest": processed / "freeze_manifest.jsonl",
            "experiment_log": logs / "experiment_log.md",
            "report": reports / "report.md",
            "run_manifest": reports / "run_manifest.jsonl",
            "method_data": docs / "01_data_construction.md",
            "method_anno": docs / "02_annotation_guidelines.md",
            "method_metric": docs / "03_metric_definition.md",
        },
        "figures": figure_map,
    }
    return result


def run_pipeline_subprocess(
    root: Path, config_path: str = "configs/systems.yaml", enable_llm: bool = False
) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["INKSTONE_ENABLE_LLM"] = "1" if enable_llm else "0"
    cmd = [sys.executable, "-m", "src.pipeline.run_all", "--config", config_path]
    proc = subprocess.run(
        cmd,
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return int(proc.returncode), proc.stdout, proc.stderr
