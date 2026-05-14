"""
guards/escalation_detector.py
-----------------------------
Rule-based detection for admissions overcommitment.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Tuple


class EscalationDetector:
    """Detect overconfident admissions claims in generated responses."""

    HIGH_PATTERNS: tuple[tuple[str, str], ...] = (
        (r"\bchac chan\b.{0,40}\b(dau|do|trung tuyen|duoc vao)\b", "definitive admission promise"),
        (r"\bbao dam\b.{0,40}\b(trung tuyen|duoc vao|dau|do)\b", "guaranteed admission claim"),
        (r"\bdam bao\b.{0,40}\b(trung tuyen|duoc vao|dau|do)\b", "guaranteed admission claim"),
        (r"\bduong nhien\b.{0,40}\b(duoc vao|trung tuyen|dau|do)\b", "automatic admission claim"),
        (r"100%.{0,50}\b(hoc bong|trung tuyen|duoc vao|dau|do)\b", "100 percent guarantee"),
        (r"\bchac chan\b.{0,40}\b(co|duoc|nhan)\b.{0,30}\bhoc bong\b", "scholarship guarantee"),
        (r"\bbao dam\b.{0,40}\b(cap|co|duoc|nhan)\b.{0,30}\bhoc bong\b", "scholarship guarantee"),
        (r"\bguarantee(d)?\b.{0,50}\b(admission|scholarship|acceptance)\b", "English guarantee claim"),
        (r"\bdefinitely\b.{0,50}\b(admitted|accepted|get in|receive a scholarship)\b", "English definitive promise"),
    )

    MEDIUM_PATTERNS: tuple[tuple[str, str], ...] = (
        (r"\btruong\b.{0,40}\b(quy dinh|bat buoc)\b.{0,80}\b(phai|luon|luc nao cung)\b", "unverified policy claim"),
        (r"\btruong\b.{0,40}\b(quy dinh bat buoc|bat buoc)\b", "unverified policy claim"),
        (r"\bbo quy dinh\b.{0,40}\b(luon|luc nao cung|bat buoc)\b", "unverified policy claim"),
        (r"\bem khong lo\b.{0,50}\b(100%|chac chan|se duoc)\b", "false reassurance"),
        (r"\bdung vay\b.{0,50}\b(chac chan|100%|bao dam|dam bao)\b", "confirms unsafe assumption"),
        (r"\bkhong can xac minh\b", "discourages verification"),
        (r"\bofficial policy is always\b", "unverified policy claim"),
    )

    @classmethod
    def detect_overcommitment(cls, text: str) -> Tuple[str, str]:
        normalized = cls._normalize(text)
        for pattern, reason in cls.HIGH_PATTERNS:
            if re.search(pattern, normalized):
                return "HIGH", reason

        for pattern, reason in cls.MEDIUM_PATTERNS:
            if re.search(pattern, normalized):
                return "MEDIUM", reason

        return "NONE", ""

    @staticmethod
    def should_escalate(escalation_level: str) -> bool:
        return escalation_level in {"MEDIUM", "HIGH"}

    @staticmethod
    def _normalize(text: str) -> str:
        if not text:
            return ""

        decomposed = unicodedata.normalize("NFD", text)
        without_marks = "".join(
            char for char in decomposed if unicodedata.category(char) != "Mn"
        )
        without_marks = without_marks.replace("\u0111", "d").replace("\u0110", "D")
        return " ".join(without_marks.lower().split())
