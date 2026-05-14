"""
guards/output_guard.py
----------------------
Responsibility: Post-process every LLM response before it reaches the user.

Protections:
  1. PII redaction — mask SSN, emails, phone numbers, credit cards.
  2. HTML/XSS sanitisation — strip tags and javascript: URLs.
  3. Sensitive keyword detection — log warnings for passwords, tokens, API keys.

All redactions are logged (without the actual PII) for audit purposes.
"""

import re
import logging
from typing import Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

# (pattern, replacement) pairs applied in order
PII_PATTERNS: list[Tuple[str, str]] = [
    # Email addresses
    (r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),
    # Vietnamese phone numbers (09x, 08x, 03x, 07x, etc.)
    (r"\b(0[3-9]\d{8})\b", "[PHONE]"),
    # International phone
    (r"\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{4,10}", "[PHONE]"),
    # Credit card (basic 4×4 pattern)
    (r"\b\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4}\b", "[CARD]"),
    # Vietnamese CMND / CCCD (9 or 12 digits)
    (r"\b\d{9}\b|\b\d{12}\b", "[ID]"),
]

SENSITIVE_KEYWORDS: list[str] = [
    "password", "mật khẩu", "secret", "api_key", "token",
    "private_key", "authorization",
]

MAX_OUTPUT_LENGTH: int = 4000


class OutputGuard:
    """
    Redacts PII and sanitises HTML from LLM-generated text before delivery.
    """

    def redact(self, text: str) -> str:
        """
        Apply all PII redaction patterns to the output text.

        Args:
            text: Raw LLM response string.

        Returns:
            Redacted string safe to deliver to the user.

        Implemented protections:
          - Apply each PII replacement pattern.
          - Log redaction by PII type without exposing the original value.
          - Warn on sensitive keywords while leaving final blocking to JudgeAgent.
        """
        redacted = text
        for pattern, replacement in PII_PATTERNS:
            original_len = len(redacted)
            redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
            if len(redacted) != original_len: # Simple check if a substitution occurred
                logger.info(f"OutputGuard: Redacted PII type '{replacement}'")

        for kw in SENSITIVE_KEYWORDS:
            if kw.lower() in redacted.lower():
                logger.warning(f"OutputGuard: sensitive keyword detected — '{kw}'")

        return redacted

    def sanitize_html(self, text: str) -> str:
        """
        Remove HTML tags and dangerous URL schemes from LLM output.

        Args:
            text: Text potentially containing HTML markup.

        Returns:
            Plain text with HTML stripped.

        TODO: Use a proper HTML parser (bleach or html.parser) instead of
              regex for production — regex-based HTML stripping has known
              bypass vectors (nested tags, malformed markup).
        """
        # Strip HTML tags
        clean = re.sub(r"<[^>]+>", "", text)
        # Remove javascript: URLs
        clean = re.sub(r"javascript\s*:", "", clean, flags=re.IGNORECASE)
        # TODO: Replace with bleach.clean() once bleach is added to requirements.txt
        return clean

    def process(self, text: str) -> str:
        """
        Run full output processing pipeline: redact PII then sanitise HTML.

        Args:
            text: Raw LLM response.

        Returns:
            Fully processed, safe response string.

        Applies the configured character limit and appends a truncation note.
        """
        processed_text = self.sanitize_html(self.redact(text))

        if len(processed_text) > MAX_OUTPUT_LENGTH:
            logger.warning(f"OutputGuard: Truncating output from {len(processed_text)} to {MAX_OUTPUT_LENGTH} characters.")
            processed_text = processed_text[:MAX_OUTPUT_LENGTH - len("... [truncated]")].strip() + "... [truncated]"

        return processed_text
