from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path


REQUIRED_NLTK = ["wordnet", "omw-1.4", "punkt"]


def _run(cmd: list[str]) -> None:
    subprocess.check_call(cmd)


def install_dependencies() -> None:
    req = Path("requirements.txt")
    if req.exists():
        _run([sys.executable, "-m", "pip", "install", "-r", str(req)])


def download_nltk() -> None:
    nltk = importlib.import_module("nltk")
    for item in REQUIRED_NLTK:
        nltk.download(item, quiet=True)


def ensure_default_config() -> None:
    cfg = Path("configs/systems.yaml")
    if not cfg.exists():
        raise FileNotFoundError("缺少 configs/systems.yaml 配置文件")


def run_download_script() -> None:
    script = Path("scripts/download_datasets.py")
    if script.exists():
        _run([sys.executable, str(script)])


def main() -> None:
    install_dependencies()
    download_nltk()
    ensure_default_config()
    run_download_script()
    print("环境引导完成")


if __name__ == "__main__":
    main()
