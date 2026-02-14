from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from src.core.normalize import normalize_text, stable_sid
from src.core.schema import METAPHOR_TYPES


_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_SENT_SPLIT_RE = re.compile(r"[。！？!?]\s*")

_TEXT_KEYS = [
    "text_zh",
    "zh",
    "src_zh",
    "chinese",
    "source",
    "sentence",
    "text",
    "content",
]

_TYPE_KEYS = [
    "metaphor_type",
    "type",
    "label",
    "category",
    "metaphor",
]


def _has_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text))


def _norm_mtype(raw: str | None) -> str:
    if raw is None:
        return "mixed_other"
    val = str(raw).strip().lower()
    if val in METAPHOR_TYPES:
        return val
    mapping = {
        "明喻": "simile",
        "simile": "simile",
        "隐喻": "implicit",
        "metaphor": "implicit",
        "拟人": "personification",
        "personification": "personification",
        "通感": "synesthesia",
        "synesthesia": "synesthesia",
        "典故": "cultural_allusion",
        "allusion": "cultural_allusion",
        "文化负载": "cultural_allusion",
        "惯用": "dead_conventional",
        "conventional": "dead_conventional",
    }
    for key, mtype in mapping.items():
        if key in val:
            return mtype
    return "mixed_other"


def _infer_mtype(text_zh: str) -> str:
    text = text_zh.strip()
    if any(k in text for k in ["像", "如同", "仿佛", "好似"]):
        return "simile"
    if any(k in text for k in ["城市", "风", "时间", "黑夜"]) and any(
        k in text for k in ["笑", "哭", "说", "哈欠", "醒", "沉睡"]
    ):
        return "personification"
    if any(k in text for k in ["颜色", "味道", "声音", "冰蓝", "温暖"]):
        return "synesthesia"
    return "mixed_other"


def _pick_text_and_type(row: dict[str, Any]) -> tuple[str | None, str | None]:
    text_val: str | None = None
    type_val: str | None = None
    for key in _TYPE_KEYS:
        if key in row and row[key] is not None:
            type_val = str(row[key])
            break
    for key in _TEXT_KEYS:
        if key not in row or row[key] is None:
            continue
        val = str(row[key]).strip()
        if not val:
            continue
        if _has_cjk(val):
            text_val = val
            break
    if text_val is None:
        for value in row.values():
            if value is None:
                continue
            val = str(value).strip()
            if 4 <= len(val) <= 220 and _has_cjk(val):
                text_val = val
                break
    return text_val, type_val


def _iter_json_file(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ["data", "records", "samples", "items", "train"]:
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if all(isinstance(v, dict) for v in data.values()):
            return [v for v in data.values() if isinstance(v, dict)]
    return []


def _iter_jsonl_file(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def _iter_table_file(path: Path, delimiter: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            rows.append({str(k): v for k, v in row.items()})
    return rows


def _iter_txt_file(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    chunks = []
    for piece in _SENT_SPLIT_RE.split(text):
        piece = piece.strip()
        if 6 <= len(piece) <= 220 and _has_cjk(piece):
            chunks.append({"text_zh": piece + "。"})
    return chunks


def discover_external_files(external_dir: Path) -> list[Path]:
    if not external_dir.exists():
        return []
    patterns = ["**/*.jsonl", "**/*.json", "**/*.csv", "**/*.tsv", "**/*.txt"]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(external_dir.glob(pattern))
    files = [p for p in files if p.is_file()]
    files.sort(key=lambda p: str(p))
    return files


def parse_external_rows(
    external_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    files = discover_external_files(external_dir)
    out_rows: list[dict[str, Any]] = []
    file_stats: list[dict[str, Any]] = []
    created_at = datetime.now(timezone.utc).isoformat()

    for file_path in files:
        ext = file_path.suffix.lower()
        raw_rows: list[dict[str, Any]] = []
        try:
            if ext == ".jsonl":
                raw_rows = _iter_jsonl_file(file_path)
            elif ext == ".json":
                raw_rows = _iter_json_file(file_path)
            elif ext == ".csv":
                raw_rows = _iter_table_file(file_path, ",")
            elif ext == ".tsv":
                raw_rows = _iter_table_file(file_path, "\t")
            elif ext == ".txt":
                raw_rows = _iter_txt_file(file_path)
        except Exception:
            raw_rows = []

        accepted = 0
        source_name = "external"
        low = str(file_path).lower()
        if "cmdag" in low:
            source_name = "cmdag"
        elif "cmc" in low:
            source_name = "cmc"

        for idx, row in enumerate(raw_rows, start=1):
            text_zh, type_val = _pick_text_and_type(row)
            if text_zh is None:
                continue
            text_zh = text_zh.strip()
            if len(text_zh) < 6:
                continue
            mtype = _norm_mtype(type_val)
            if mtype == "mixed_other":
                mtype = _infer_mtype(text_zh)
            local_id = f"{file_path.name}:{idx}"
            sid = stable_sid(text_zh, source_name, local_id)
            out_rows.append(
                {
                    "sid": sid,
                    "text_zh": text_zh,
                    "source_meta": {
                        "source": source_name,
                        "local_id": local_id,
                        "file": str(file_path),
                        "license_tag": "external_unknown",
                    },
                    "metaphor_meta": {
                        "metaphor_type": mtype,
                        "cultural_load": "unknown",
                    },
                    "meta": {
                        "len_char": len(text_zh),
                        "created_at": created_at,
                    },
                }
            )
            accepted += 1

        file_stats.append(
            {
                "file": str(file_path),
                "ext": ext,
                "parsed_rows": len(raw_rows),
                "accepted_rows": accepted,
                "source": source_name,
            }
        )

    return out_rows, {"files": file_stats, "n_files": len(files)}


def parse_books_rows(books_dir: Path) -> list[dict[str, Any]]:
    if not books_dir.exists():
        return []
    out_rows: list[dict[str, Any]] = []
    created_at = datetime.now(timezone.utc).isoformat()
    txt_files = sorted(books_dir.glob("*.txt"))
    for fp in txt_files:
        chunks = _iter_txt_file(fp)
        for idx, item in enumerate(chunks, start=1):
            text_zh = str(item.get("text_zh", "")).strip()
            if not text_zh:
                continue
            mtype = _infer_mtype(text_zh)
            local_id = f"{fp.name}:{idx}"
            sid = stable_sid(text_zh, "books", local_id)
            out_rows.append(
                {
                    "sid": sid,
                    "text_zh": text_zh,
                    "source_meta": {
                        "source": "books",
                        "local_id": local_id,
                        "doc": fp.name,
                        "file": str(fp),
                        "license_tag": "internal_books",
                    },
                    "metaphor_meta": {
                        "metaphor_type": mtype,
                        "cultural_load": "unknown",
                    },
                    "meta": {
                        "len_char": len(text_zh),
                        "created_at": created_at,
                    },
                }
            )
    return out_rows


def dedup_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    dropped = 0
    for row in rows:
        key = normalize_text(str(row.get("text_zh", "")))
        if not key:
            dropped += 1
            continue
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        out.append(row)
    return out, dropped


def build_quality_report(
    rows_before_dedup: int,
    rows_after_dedup: list[dict[str, Any]],
    eval_rows: list[dict[str, Any]],
    pool_rows: list[dict[str, Any]],
    parser_meta: dict[str, Any],
) -> dict[str, Any]:
    lengths = [
        int(r.get("meta", {}).get("len_char", len(r.get("text_zh", ""))))
        for r in rows_after_dedup
    ]
    lengths.sort()
    p50 = lengths[len(lengths) // 2] if lengths else 0
    p90 = lengths[int(len(lengths) * 0.9)] if lengths else 0
    source_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {m: 0 for m in METAPHOR_TYPES}
    for row in rows_after_dedup:
        src = str(row.get("source_meta", {}).get("source", "unknown"))
        source_counts[src] = source_counts.get(src, 0) + 1
        mtype = str(row.get("metaphor_meta", {}).get("metaphor_type", "mixed_other"))
        type_counts[mtype] = type_counts.get(mtype, 0) + 1

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rows_before_dedup": rows_before_dedup,
        "rows_after_dedup": len(rows_after_dedup),
        "duplicates_removed": rows_before_dedup - len(rows_after_dedup),
        "eval_rows": len(eval_rows),
        "pool_rows": len(pool_rows),
        "source_counts": source_counts,
        "metaphor_type_counts": type_counts,
        "length_stats": {
            "min": min(lengths) if lengths else 0,
            "max": max(lengths) if lengths else 0,
            "mean": float(mean(lengths)) if lengths else 0.0,
            "p50": p50,
            "p90": p90,
        },
        "parser_meta": parser_meta,
    }
