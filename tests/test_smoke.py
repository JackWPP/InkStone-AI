from pathlib import Path

from src.pipeline.run_all import run_pipeline


def test_pipeline_smoke() -> None:
    outputs = run_pipeline("configs/systems.yaml")
    assert "report" in outputs
    assert Path(outputs["report"]).exists()
