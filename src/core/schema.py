from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


METAPHOR_TYPES = [
    "simile",
    "implicit",
    "personification",
    "synesthesia",
    "cultural_allusion",
    "dead_conventional",
    "mixed_other",
]

DIMENSIONS = ["IF", "EC", "RE", "CA", "LE"]


@dataclass(slots=True)
class SourceItem:
    sid: str
    text_zh: str
    source_meta: dict[str, Any]
    metaphor_meta: dict[str, Any]
    meta: dict[str, Any]

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()
