from __future__ import annotations

import argparse
from pathlib import Path

from src.pipeline import (
    build_dataset,
    icl_builder,
    judge_persona,
    judge_standard,
    metrics,
    report,
    translate,
    visualization,
)
from src.pipeline.config import load_config


def run_pipeline(config_path: str) -> dict[str, str]:
    config = load_config(config_path)
    Path(config["paths"]["data_processed"]).mkdir(parents=True, exist_ok=True)
    Path(config["paths"]["reports_dir"]).mkdir(parents=True, exist_ok=True)
    Path(config["paths"]["methodology_dir"]).mkdir(parents=True, exist_ok=True)

    build_dataset.run(config)
    translate.run(config)
    judge_persona.run(config)
    icl_builder.run(config)
    judge_standard.run(config)
    metric_summary = metrics.run(config)
    viz_stats = visualization.run(config)
    report_paths = report.run(config, metric_summary, viz_stats)
    return report_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Run INKSTONE-AI full pipeline")
    parser.add_argument("--config", required=True, help="Path to systems yaml")
    args = parser.parse_args()
    outputs = run_pipeline(args.config)
    print(outputs)


if __name__ == "__main__":
    main()
