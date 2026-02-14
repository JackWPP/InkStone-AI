from __future__ import annotations

import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.io import write_jsonl
from src.core.normalize import stable_sid
from src.core.schema import METAPHOR_TYPES


def _seed_rows() -> list[dict[str, str]]:
    return [
        {"text_zh": "她的笑容像春风一样温暖。", "metaphor_type": "simile"},
        {"text_zh": "时间在指缝间悄悄流走。", "metaphor_type": "implicit"},
        {"text_zh": "城市在夜里打了个哈欠。", "metaphor_type": "personification"},
        {"text_zh": "这声音是冰蓝色的。", "metaphor_type": "synesthesia"},
        {"text_zh": "他是我们团队的定海神针。", "metaphor_type": "cultural_allusion"},
        {"text_zh": "生活是一场旅行。", "metaphor_type": "dead_conventional"},
        {"text_zh": "她把忧伤揉成一杯苦茶。", "metaphor_type": "mixed_other"},
    ]


def run(config: dict[str, Any]) -> dict[str, Any]:
    paths = config["paths"]
    run_cfg = config["run"]
    output_dir = Path(paths["data_processed"])
    output_dir.mkdir(parents=True, exist_ok=True)

    seed = int(run_cfg.get("seed", 20260215))
    target_n = int(run_cfg.get("n_eval", 300))
    random.seed(seed)

    rows: list[dict[str, Any]] = []
    base = _seed_rows()
    for i in range(target_n):
        template = base[i % len(base)]
        text_zh = f"{template['text_zh']}（样本{i + 1}）"
        metaphor_type = template["metaphor_type"]
        if metaphor_type not in METAPHOR_TYPES:
            metaphor_type = "mixed_other"
        sid = stable_sid(text_zh, "seed_builtin", str(i + 1))
        rows.append(
            {
                "sid": sid,
                "text_zh": text_zh,
                "source_meta": {
                    "source": "seed_builtin",
                    "local_id": str(i + 1),
                    "license_tag": "internal_seed",
                },
                "metaphor_meta": {
                    "metaphor_type": metaphor_type,
                    "cultural_load": "unknown",
                },
                "meta": {
                    "len_char": len(text_zh),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            }
        )

    eval_path = output_dir / "eval_set.jsonl"
    source_path = output_dir / "source_items.jsonl"
    pool_path = output_dir / "pool.jsonl"
    write_jsonl(source_path, rows)
    write_jsonl(eval_path, rows)
    write_jsonl(pool_path, [])
    return {"rows": len(rows), "eval_set": str(eval_path)}


if __name__ == "__main__":
    from src.pipeline.config import load_config

    cfg = load_config("configs/systems.yaml")
    print(run(cfg))
