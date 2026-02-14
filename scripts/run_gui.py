from __future__ import annotations

import subprocess
import sys


def main() -> None:
    subprocess.check_call([sys.executable, "-m", "streamlit", "run", "src/gui/app.py"])


if __name__ == "__main__":
    main()
