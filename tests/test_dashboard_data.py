from pathlib import Path

from src.gui.dashboard import load_dashboard_data, run_pipeline_subprocess


def test_dashboard_data_loading() -> None:
    root = Path(__file__).resolve().parents[1]
    code, _, _ = run_pipeline_subprocess(root, enable_llm=False)
    assert code == 0

    data = load_dashboard_data(root)
    assert "summary" in data
    assert "figures" in data
    assert "files" in data
    assert (root / "reports" / "figures" / "fig1_data_distribution.png").exists()
