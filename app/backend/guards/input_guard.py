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

        TODO: 1. Check len(text) < MIN_LENGTH → return (False, "input_too_short").
        TODO: 2. Check len(text) > MAX_LENGTH → return (False, "input_too_long").
        TODO: 3. Loop through INJECTION_PATTERNS with re.search(pattern, text, re.IGNORECASE).
                 On match → log warning + return (False, "injection_detected").
        TODO: 4. Loop through BLOCKED_TOPIC_PATTERNS.
                 On match → return (False, "blocked_topic").
        TODO: 5. All checks pass → return (True, "ok").
        """
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

        return True, "CLEAN"

    def sanitize(self, text: str) -> str:
        """
        Light sanitisation: strip leading/trailing whitespace, collapse
        multiple spaces. Does NOT alter content — full sanitisation happens
        in output_guard.py after LLM generation.

        Args:
            text: Raw input string.

        Returns:
            Lightly sanitised string.

        TODO: Add normalisation for Unicode homoglyphs (e.g., Cyrillic 'а' → 'a')
              if injection attempts using look-alike characters are detected.
        """
        # TODO: Add homoglyph normalisation if needed
        normalized = unicodedata.normalize('NFKC', text)
        return " ".join(normalized.split())
