"""
services/cv_parser.py
--------------------
Responsibility: Extract structured JSON from CV text using LLM.
"""

import re
import json
import logging
from typing import Optional
from services.llm_client import LLMClient
from models.cv_schema import CVData
from utils.logger import get_logger
from guards.output_guard import PII_PATTERNS
from guards.input_guard import INJECTION_PATTERNS

logger = get_logger(__name__)

MAX_CV_CHARS = 12000  # Approx 3-4 pages of text

PARSE_PROMPT = """
Extract structured information from the following CV text. 
Respond ONLY with a JSON object matching this structure:
{
  "summary": "string",
  "education": [{"institution": "string", "degree": "string"}],
  "experience": [{"role": "string", "description": "string"}],
  "skills": ["string"],
  "projects": [{"name": "string", "description": "string"}],
  "achievements": ["string"]
}
If information is missing, use empty lists or null.

CV Text:
"""

class CVParser:
    def __init__(self):
        self.llm = LLMClient()

    def parse(self, text: str) -> Optional[CVData]:
        """Convert raw CV text into structured CVData."""
        if not text or len(text) > MAX_CV_CHARS:
            logger.warning(f"CV rejected: size issues (len={len(text) if text else 0})")
            return None

        # Security: Detect prompt injection attempts in CV text
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning("CV rejected: potential injection detected in content")
                return None

        # Privacy: Redact PII before sending to LLM
        sanitized_text = text
        for pattern, replacement in PII_PATTERNS:
            sanitized_text = re.sub(pattern, replacement, sanitized_text, flags=re.IGNORECASE)

        try:
            prompt = PARSE_PROMPT + sanitized_text
            clean_text = self.llm.generate(prompt)
            
            if clean_text == "I don't know":
                return None

            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            
            data = json.loads(clean_text)
            return CVData(**data)
        except Exception as e:
            logger.error(f"CVParser failed: {e}")
            return None