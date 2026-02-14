from pathlib import Path

from src.pipeline.run_all import run_pipeline


def test_pipeline_smoke() -> None:
    outputs = run_pipeline("configs/systems.yaml")
    assert "report" in outputs
    assert Path(outputs["report"]).exists()
    assert Path("data/processed/data_quality.jsonl").exists()
    assert Path("data/processed/freeze_manifest.jsonl").exists()
    assert Path("data/processed/translation_stats.jsonl").exists()
    assert Path("reports/run_manifest.jsonl").exists()
