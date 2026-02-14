from __future__ import annotations

import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.io import write_jsonl


def _git_short_head() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.stdout.strip() if proc.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def write_run_manifest(
    config: dict[str, Any],
    stage: str,
    outputs: dict[str, Any] | None = None,
) -> str:
    reports_dir = Path(config["paths"]["reports_dir"])
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "run_manifest.jsonl"
    row = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "git_head": _git_short_head(),
        "python": sys.version,
        "platform": platform.platform(),
        "seed": int(config["run"].get("seed", 20260215)),
        "n_eval": int(config["run"].get("n_eval", 300)),
        "config_paths": config.get("paths", {}),
    }
    if outputs is not None:
        row["outputs"] = outputs
    existing: list[dict[str, Any]] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                import json

                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                existing.append(obj)
    existing.append(row)
    write_jsonl(path, existing)
    return str(path)
