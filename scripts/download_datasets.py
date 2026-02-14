from __future__ import annotations

import json
import importlib
import subprocess
import sys
from pathlib import Path


REPOS = [
    "https://github.com/NeuLab/CMDAG.git",
    "https://github.com/blcuicall/CMC.git",
]


def _clone(repo: str, target: Path) -> bool:
    try:
        subprocess.check_call(["git", "clone", "--depth", "1", repo, str(target)])
        return True
    except Exception:
        return False


def _hf_fallback(target: Path) -> bool:
    try:
        datasets_mod = importlib.import_module("datasets")
        load_dataset = getattr(datasets_mod, "load_dataset")
        dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="train[:1]")
        target.mkdir(parents=True, exist_ok=True)
        (target / "hf_fallback.json").write_text(
            json.dumps(
                {"rows": len(dataset), "note": "HF 备援元数据"},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return True
    except Exception:
        return False


def main() -> None:
    external = Path("data/external")
    external.mkdir(parents=True, exist_ok=True)
    clone_ok = False
    for repo in REPOS:
        name = repo.rsplit("/", 1)[-1].replace(".git", "")
        target = external / name
        if target.exists():
            clone_ok = True
            continue
        if _clone(repo, target):
            clone_ok = True

    if clone_ok:
        print("已通过 git clone 完成数据下载")
        return

    hf_ok = _hf_fallback(external / "hf_fallback")
    if hf_ok:
        print("已通过 HuggingFace 备援完成数据下载")
        return

    print(
        "数据下载失败：git clone 与 HF 备援均失败。"
        "请检查网络/代理后重试 scripts/download_datasets.py",
        file=sys.stderr,
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
