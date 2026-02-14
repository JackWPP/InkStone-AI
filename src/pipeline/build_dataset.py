from __future__ import annotations

import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.io import write_jsonl
from src.core.normalize import stable_sid
from src.core.schema import METAPHOR_TYPES
from src.pipeline.data_sources import (
    build_quality_report,
    dedup_rows,
    parse_books_rows,
    parse_external_rows,
)


def _seed_rows(target_n: int) -> list[dict[str, Any]]:
    base = [
        {"text_zh": "她的笑容像春风一样温暖。", "metaphor_type": "simile"},
        {"text_zh": "时间在指缝间悄悄流走。", "metaphor_type": "implicit"},
        {"text_zh": "城市在夜里打了个哈欠。", "metaphor_type": "personification"},
        {"text_zh": "这声音是冰蓝色的。", "metaphor_type": "synesthesia"},
        {"text_zh": "他是我们团队的定海神针。", "metaphor_type": "cultural_allusion"},
        {"text_zh": "生活是一场旅行。", "metaphor_type": "dead_conventional"},
        {"text_zh": "她把忧伤揉成一杯苦茶。", "metaphor_type": "mixed_other"},
    ]
    rows: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()
    source_target = max(target_n * 3, 900)
    for i in range(source_target):
        template = base[i % len(base)]
        text_zh = f"{template['text_zh']}（候选{i + 1}）"
        metaphor_type = str(template["metaphor_type"])
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
                "meta": {"len_char": len(text_zh), "created_at": now},
            }
        )
    return rows


def _stratified_sample(
    rows: list[dict[str, Any]], target_n: int, seed: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    random.seed(seed)
    by_type: dict[str, list[dict[str, Any]]] = {m: [] for m in METAPHOR_TYPES}
    for row in rows:
        mtype = str(row.get("metaphor_meta", {}).get("metaphor_type", "mixed_other"))
        by_type.setdefault(mtype, []).append(row)

    selected: list[dict[str, Any]] = []
    used: set[str] = set()
    remaining_slots = target_n

    non_empty_types = [m for m in METAPHOR_TYPES if by_type.get(m)]
    if non_empty_types:
        base_take = max(1, target_n // len(non_empty_types))
        for mtype in non_empty_types:
            bucket = by_type[mtype]
            random.shuffle(bucket)
            take = min(base_take, len(bucket), remaining_slots)
            for row in bucket[:take]:
                selected.append(row)
                used.add(str(row["sid"]))
            remaining_slots -= take
            if remaining_slots <= 0:
                break

    if remaining_slots > 0:
        rest = [r for r in rows if str(r["sid"]) not in used]
        random.shuffle(rest)
        for row in rest[:remaining_slots]:
            selected.append(row)
            used.add(str(row["sid"]))

    selected = selected[:target_n]
    pool = [r for r in rows if str(r["sid"]) not in used]
    return selected, pool


def _manifest_row(config: dict[str, Any], quality_report_path: Path) -> dict[str, Any]:
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": int(config["run"].get("seed", 20260215)),
        "n_eval": int(config["run"].get("n_eval", 300)),
        "paths": config.get("paths", {}),
        "quality_report": str(quality_report_path),
    }


def run(config: dict[str, Any]) -> dict[str, Any]:
    paths = config["paths"]
    run_cfg = config["run"]
    output_dir = Path(paths["data_processed"])
    output_dir.mkdir(parents=True, exist_ok=True)

    seed = int(run_cfg.get("seed", 20260215))
    target_n = int(run_cfg.get("n_eval", 300))

    external_dir = Path(paths.get("data_external", "data/external"))
    books_dir = Path(paths.get("data_raw_books", "data/raw/books"))

    external_rows, parser_meta = parse_external_rows(external_dir)
    books_rows = parse_books_rows(books_dir)
    seed_rows = _seed_rows(target_n)

    rows_before = external_rows + books_rows + seed_rows
    rows, dropped = dedup_rows(rows_before)
    eval_rows, pool_rows = _stratified_sample(rows, target_n, seed)

    source_path = output_dir / "source_items.jsonl"
    eval_path = output_dir / "eval_set.jsonl"
    pool_path = output_dir / "pool.jsonl"
    quality_path = output_dir / "data_quality.jsonl"
    freeze_manifest_path = output_dir / "freeze_manifest.jsonl"

    write_jsonl(source_path, rows)
    write_jsonl(eval_path, eval_rows)
    write_jsonl(pool_path, pool_rows)

    quality = build_quality_report(
        rows_before_dedup=len(rows_before),
        rows_after_dedup=rows,
        eval_rows=eval_rows,
        pool_rows=pool_rows,
        parser_meta=parser_meta,
    )
    quality["duplicates_removed"] = dropped
    quality["sources_before_merge"] = {
        "external_rows": len(external_rows),
        "books_rows": len(books_rows),
        "seed_rows": len(seed_rows),
    }

    write_jsonl(quality_path, [quality])
    write_jsonl(freeze_manifest_path, [_manifest_row(config, quality_path)])

    return {
        "rows": len(rows),
        "eval_rows": len(eval_rows),
        "pool_rows": len(pool_rows),
        "external_rows": len(external_rows),
        "books_rows": len(books_rows),
        "seed_rows": len(seed_rows),
        "eval_set": str(eval_path),
        "quality": str(quality_path),
    }


if __name__ == "__main__":
    from src.pipeline.config import load_config

    cfg = load_config("configs/systems.yaml")
    print(run(cfg))
