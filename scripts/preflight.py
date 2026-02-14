from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


REQUIRED_MODULES = [
    "yaml",
    "numpy",
    "matplotlib",
    "sacrebleu",
    "nltk",
    "scipy",
]


def _check_python() -> list[str]:
    if sys.version_info < (3, 10):
        return ["Python>=3.10 required. Fix: install Python 3.10+ and recreate venv."]
    return []


def _check_imports() -> list[str]:
    errors: list[str] = []
    for mod in REQUIRED_MODULES:
        try:
            importlib.import_module(mod)
        except Exception:
            errors.append(
                f"Missing dependency '{mod}'. Fix: pip install -r requirements.txt"
            )
    return errors


def _check_api_key() -> list[str]:
    if not os.getenv("OPENAI_API_KEY"):
        return [
            "OPENAI_API_KEY not set. Fix: export OPENAI_API_KEY=... (or set local provider key env)."
        ]
    return []


def _check_output_paths() -> list[str]:
    errors: list[str] = []
    for path in [Path("reports"), Path("docs/methodology"), Path("data/processed")]:
        try:
            path.mkdir(parents=True, exist_ok=True)
            test_file = path / ".write_test"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink()
        except Exception:
            errors.append(f"Cannot write to {path}. Fix: verify folder permissions.")
    return errors


def main() -> None:
    errors = []
    errors.extend(_check_python())
    errors.extend(_check_imports())
    errors.extend(_check_api_key())
    errors.extend(_check_output_paths())

    if errors:
        print("Preflight failed:")
        for e in errors:
            print(f"- {e}")
        raise SystemExit(1)
    print("Preflight passed")


if __name__ == "__main__":
    main()
