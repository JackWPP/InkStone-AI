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
        return ["需要 Python>=3.10。修复：安装 Python 3.10+ 并重建虚拟环境。"]
    return []


def _check_imports() -> list[str]:
    errors: list[str] = []
    for mod in REQUIRED_MODULES:
        try:
            importlib.import_module(mod)
        except Exception:
            errors.append(
                f"缺少依赖 '{mod}'。修复：执行 pip install -r requirements.txt"
            )
    return errors


def _check_api_key() -> list[str]:
    if not os.getenv("OPENAI_API_KEY"):
        return [
            "未设置 OPENAI_API_KEY。修复：设置 OPENAI_API_KEY（或改为本地供应商对应环境变量）。"
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
            errors.append(f"无法写入 {path}。修复：检查目录权限。")
    return errors


def main() -> None:
    errors = []
    errors.extend(_check_python())
    errors.extend(_check_imports())
    errors.extend(_check_api_key())
    errors.extend(_check_output_paths())

    if errors:
        print("预检失败：")
        for e in errors:
            print(f"- {e}")
        raise SystemExit(1)
    print("预检通过")


if __name__ == "__main__":
    main()
