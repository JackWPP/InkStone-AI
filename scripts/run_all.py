from __future__ import annotations

import subprocess
import sys


def main() -> None:
    subprocess.check_call([sys.executable, "scripts/bootstrap.py"])
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "src.pipeline.run_all",
            "--config",
            "configs/systems.yaml",
        ]
    )


if __name__ == "__main__":
    main()
