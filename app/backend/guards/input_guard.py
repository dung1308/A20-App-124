"""
guards/input_guard.py
---------------------
Responsibility: First line of defence. Validates all incoming user text
before it reaches the orchestrator or any LLM.

Checks (in order):
  1. Length — reject if empty or > MAX_LENGTH characters.
  2. Injection patterns — detect common prompt injection and jailbreak attempts.
  3. Blocked topics — reject questions clearly outside scope.

Returns (is_safe: bool, reason: str) — caller decides whether to raise HTTP 400.
"""

import re
import logging
import unicodedata
from typing import Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

MIN_LENGTH: int = 1
MAX_LENGTH: int = 5000

HOMOGLYPH_TRANSLATION = str.maketrans({
    "\u0430": "a", "\u0410": "A",
    "\u0435": "e", "\u0415": "E",
    "\u043e": "o", "\u041e": "O",
    "\u0440": "p", "\u0420": "P",
    "\u0441": "c", "\u0421": "C",
    "\u0445": "x", "\u0425": "X",
    "\u0443": "y", "\u0423": "Y",
    "\u0456": "i", "\u0406": "I",
    "\u0458": "j", "\u0408": "J",
    "\u0455": "s", "\u0405": "S",
})

# TODO: Expand this list with additional Vietnamese and English injection patterns
INJECTION_PATTERNS: list[str] = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"forget\s+your\s+instructions",
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(if\s+you\s+are\s+)?a",
    r"jailbreak",
    r"DAN\s+mode",
    r"<\s*script",          # XSS
    r";\s*DROP\s+TABLE",    # SQL injection
    r"UNION\s+SELECT",      # SQL injection
]

# TODO: Add more out-of-scope topic patterns relevant to admissions chatbot
BLOCKED_TOPIC_PATTERNS: list[str] = [
    r"\b(bomb|weapon|hack|exploit)\b",
    r"\b(pháp lý|pháp luật|luật sư|tư vấn pháp lý|hợp đồng|tranh chấp|kiện cáo)\b",
    r"\b(tài chính cá nhân|tư vấn tài chính|đầu tư|chứng khoán|nợ|thuế|bảo hiểm|làm giàu|tiền ảo|crypto)\b",
    r"\b(sức khỏe|bệnh|bệnh lý|tâm lý|trầm cảm|lo âu|stress|tự tử|suicide|vaccine|ung thư|uống thuốc|thuốc giảm cân|thuốc ngủ)\b",
]


class InputGuard:
    """
    Validates user input length and scans for injection / blocked content.
    """

    def check(self, text: str) -> Tuple[bool, str]:
        """
        Run all input checks and return a safety verdict.

        Args:
            text: Raw user input string.

        Returns:
            Tuple (is_safe, reason):
              is_safe=True  → input is acceptable, proceed.
              is_safe=False → input blocked; reason describes why.

        Implemented checks:
          - Enforce minimum and maximum length limits.
          - Block prompt-injection, XSS, and SQL-injection patterns.
          - Block clearly out-of-scope topics for the admissions chatbot.
          - Return (True, "ok") only after all checks pass.
        """
        if text is None:
            return False, "input_too_short"

        text = self.sanitize(str(text))
        logger.debug(f"InputGuard.check() — length {len(text)}")

        if len(text) < MIN_LENGTH:
            return False, "input_too_short"

        if len(text) > MAX_LENGTH:
            logger.warning(f"InputGuard: input length {len(text)} exceeds maximum {MAX_LENGTH}")
            return False, "input_too_long"

        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"InputGuard: injection pattern matched — '{pattern}'")
                return False, "injection_detected"

        for pattern in BLOCKED_TOPIC_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "blocked_topic"

        return True, "ok"

    def sanitize(self, text: str) -> str:
        """
        Light sanitisation: strip leading/trailing whitespace, collapse
        multiple spaces. Does NOT alter content — full sanitisation happens
        in output_guard.py after LLM generation.

        Args:
            text: Raw input string.

        Returns:
            Lightly sanitised string.

        Uses Unicode NFKC normalization plus a small explicit homoglyph map for
        common Cyrillic look-alike characters seen in prompt-injection bypasses.
        """
        normalized = unicodedata.normalize('NFKC', str(text)).translate(HOMOGLYPH_TRANSLATION)
        return " ".join(normalized.split())
