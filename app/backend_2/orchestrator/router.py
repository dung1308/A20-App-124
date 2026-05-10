"""
orchestrator/router.py
----------------------
Responsibility: Classify incoming user messages into one of four intents.

MOCK mode:
- Uses deterministic keyword-based routing (no LLM)

REAL mode:
- Uses Gemini to classify intent
"""

import logging
import json
from typing import List, Dict, Any

from config import USE_MOCK
from services.llm_client import LLMClient
from utils.logger import get_logger

logger = get_logger(__name__)

VALID_ROUTES = {"rag", "crm", "advisor", "fallback"}

ROUTER_SYSTEM_PROMPT = """
You are an intent classifier for a university admissions chatbot.
Classify the user message into exactly one of: rag, crm, advisor, fallback.

rag      → factual question about programs, requirements, deadlines, campus life
crm      → question about the student's own profile, scores, or personal history
advisor  → request for guidance on which major to choose or career direction
fallback → out-of-scope, harmful, or impossible to answer reliably

Respond with ONLY the label. No explanation.
"""


class LLMRouter:
    def __init__(self):
        # ✅ Do NOT load model in MOCK mode
        self.llm = None if USE_MOCK else LLMClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, message: str, history: List[Dict[str, Any]]) -> str:
        """
        Main routing function.
        """
        logger.info(f"Routing message: '{message[:60]}...'")

        # ==========================================================
        # ✅ MOCK MODE — NO LLM CALLS
        # ==========================================================
        if USE_MOCK:
            route = self._mock_route(message)
            logger.info(f"[MOCK] Routed to: {route}")
            return route

        # ==========================================================
        # REAL MODE — LLM routing
        # ==========================================================
        try:
            prompt = self._build_routing_prompt(message, history)
            response = self.llm.generate(prompt)

            if not response or response == "I don't know":
                logger.warning("Empty LLM response → default to 'rag'")
                return "rag"

            label = response.strip().lower()

            if label in VALID_ROUTES:
                logger.info(f"[LLM] Routed to: {label}")
                return label

            logger.warning(f"Invalid route label '{label}' → default to 'rag'")
            return "rag"

        except Exception as e:
            logger.error(f"Router failure: {e} → fallback to 'rag'")
            return "rag"

    # ------------------------------------------------------------------
    # MOCK ROUTER (deterministic)
    # ------------------------------------------------------------------

    def _mock_route(self, message: str) -> str:
        msg = message.lower()

        # CRM intent
        if any(word in msg for word in [
            "hồ sơ", "điểm", "ielts", "gpa", "thông tin cá nhân"
        ]):
            return "crm"

        # Advisor intent
        if any(word in msg for word in [
            "ngành", "chọn", "tư vấn", "phù hợp", "match", "nên học"
        ]):
            return "advisor"

        # Default → factual
        return "rag"

    # ------------------------------------------------------------------
    # Prompt builder (REAL mode)
    # ------------------------------------------------------------------

    def _build_routing_prompt(self, message: str, history: List[Dict[str, Any]]) -> str:
        """
        Build prompt with last 3 turns of history.
        """
        history = history[-3:] if history else []

        history_text = ""
        for turn in history:
            if "role" in turn and "content" in turn:
                role = "User" if turn["role"] == "user" else "Assistant"
                history_text += f"{role}: {turn['content']}\n"

        return (
            f"{ROUTER_SYSTEM_PROMPT}\n\n"
            f"Conversation:\n{history_text}\n"
            f"User message: {message}"
        )