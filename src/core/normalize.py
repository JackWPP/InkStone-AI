from __future__ import annotations

import hashlib
import re


_SPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    normalized = text.strip().lower()
    normalized = _SPACE_RE.sub(" ", normalized)
    return normalized


def stable_sid(text_zh: str, source: str, local_id: str) -> str:
    payload = f"{normalize_text(text_zh)}::{source}::{local_id}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
