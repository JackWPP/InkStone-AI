from __future__ import annotations

import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.io import read_jsonl
from src.core.io import write_jsonl
from src.core.normalize import normalize_text
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


def _dedup_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = normalize_text(str(row["text_zh"]))
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _stratified_sample(
    rows: list[dict[str, Any]], target_n: int, seed: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    random.seed(seed)
    by_type: dict[str, list[dict[str, Any]]] = {m: [] for m in METAPHOR_TYPES}
    for row in rows:
        mtype = str(row["metaphor_meta"]["metaphor_type"])
        by_type.setdefault(mtype, []).append(row)

    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    for mtype in METAPHOR_TYPES:
        bucket = by_type.get(mtype, [])
        if not bucket:
            continue
        random.shuffle(bucket)
        take = min(20, len(bucket))
        for row in bucket[:take]:
            selected.append(row)
            used.add(row["sid"])

    if len(selected) < target_n:
        remaining = [r for r in rows if r["sid"] not in used]
        random.shuffle(remaining)
        selected.extend(remaining[: max(0, target_n - len(selected))])
        used.update(r["sid"] for r in selected)

    selected = selected[:target_n]
    pool = [r for r in rows if r["sid"] not in used]
    return selected, pool


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
    source_target = max(target_n * 3, 900)
    for i in range(source_target):
        template = base[i % len(base)]
        text_zh = f"{template['text_zh']}（候选{i + 1}）"
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

    # 可选 books 管线（若用户放置 data/raw/books/*.txt）
    books_dir = Path(paths.get("data_raw_books", "data/raw/books"))
    if books_dir.exists():
        txt_files = sorted(books_dir.glob("*.txt"))
        for fp in txt_files:
            text = fp.read_text(encoding="utf-8", errors="ignore")
            chunks = [
                s.strip() for s in text.replace("\n", "").split("。") if s.strip()
            ]
            for idx, sent in enumerate(chunks[:300]):
                text_zh = sent + "。"
                mtype = METAPHOR_TYPES[idx % len(METAPHOR_TYPES)]
                sid = stable_sid(text_zh, "books", f"{fp.name}:{idx + 1}")
                rows.append(
                    {
                        "sid": sid,
                        "text_zh": text_zh,
                        "source_meta": {
                            "source": "books",
                            "local_id": f"{fp.name}:{idx + 1}",
                            "doc": fp.name,
                            "license_tag": "internal_books",
                        },
                        "metaphor_meta": {
                            "metaphor_type": mtype,
                            "cultural_load": "unknown",
                        },
                        "meta": {
                            "len_char": len(text_zh),
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        },
                    }
                )

    rows = _dedup_rows(rows)
    eval_rows, pool_rows = _stratified_sample(rows, target_n, seed)

    eval_path = output_dir / "eval_set.jsonl"
    source_path = output_dir / "source_items.jsonl"
    pool_path = output_dir / "pool.jsonl"
    write_jsonl(source_path, rows)
    write_jsonl(eval_path, eval_rows)
    write_jsonl(pool_path, pool_rows)
    return {
        "rows": len(rows),
        "eval_rows": len(eval_rows),
        "pool_rows": len(pool_rows),
        "eval_set": str(eval_path),
    }


if __name__ == "__main__":
    from src.pipeline.config import load_config

    cfg = load_config("configs/systems.yaml")
    print(run(cfg))
