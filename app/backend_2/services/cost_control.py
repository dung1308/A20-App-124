"""
services/cost_control.py
-------------------------
Responsibility: Track, enforce, and report LLM token costs.

What this does:
  - Counts estimated tokens per call (input + output)
  - Maintains per-user and global daily budgets
  - Blocks calls that would exceed budget (fail-fast)
  - Exposes a usage report for monitoring / audit

Pricing constants default to OpenAI GPT-4o-mini as of late 2024.
Values are USD per 1,000 tokens.

Usage:
    cost_guard = CostController()

    # Before calling LLM:
    if not cost_guard.allow(user_id, prompt, estimated_output_tokens=200):
        return fallback_response

    # After calling LLM:
    cost_guard.record(user_id, prompt, actual_output)
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Pricing  (USD per 1 000 tokens — Gemini 1.5 Flash defaults)
# ---------------------------------------------------------------------------

INPUT_COST_PER_1K  = float(os.getenv("LLM_INPUT_COST_PER_1K",  "0.00015"))
OUTPUT_COST_PER_1K = float(os.getenv("LLM_OUTPUT_COST_PER_1K", "0.00060"))

# ---------------------------------------------------------------------------
# Budget limits
# ---------------------------------------------------------------------------

GLOBAL_DAILY_BUDGET_USD = float(os.getenv("GLOBAL_DAILY_BUDGET_USD", "5.00"))
USER_DAILY_BUDGET_USD   = float(os.getenv("USER_DAILY_BUDGET_USD",   "0.50"))

# Max tokens we ever send in a single prompt (hard gate before pricing check)
MAX_SINGLE_PROMPT_TOKENS = int(os.getenv("MAX_SINGLE_PROMPT_TOKENS", "2000"))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

try:
    import tiktoken
except ImportError:
    tiktoken = None

def _count_tokens(text: str) -> int:
    """Count tokens using tiktoken for precision, fallback to approximation."""
    if tiktoken:
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            pass
    return max(1, len(text) // 4)


def _today_key() -> str:
    """Returns current UTC date string as YYYY-MM-DD."""
    return time.strftime("%Y-%m-%d", time.gmtime())


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        input_tokens  / 1_000 * INPUT_COST_PER_1K +
        output_tokens / 1_000 * OUTPUT_COST_PER_1K
    )


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CallRecord:
    timestamp:     float
    user_id:       str
    input_tokens:  int
    output_tokens: int
    cost_usd:      float
    call_type:     str   # "expand_query" | "generate_answer"
    blocked:       bool = False


@dataclass
class DailyBucket:
    date:         str
    total_tokens: int   = 0
    total_cost:   float = 0.0
    call_count:   int   = 0
    blocked_count: int  = 0


# ---------------------------------------------------------------------------
# CostController
# ---------------------------------------------------------------------------

class CostController:
    """
    Thread-compatible (but not thread-safe) cost guard.
    For multi-process deployments, back `_global` and `_per_user` with Redis.
    """

    def __init__(
        self,
        global_daily_budget: float = GLOBAL_DAILY_BUDGET_USD,
        user_daily_budget:   float = USER_DAILY_BUDGET_USD,
    ):
        self.global_daily_budget = global_daily_budget
        self.user_daily_budget   = user_daily_budget

        # date → DailyBucket
        self._global: Dict[str, DailyBucket] = {}
        # user_id → date → DailyBucket
        self._per_user: Dict[str, Dict[str, DailyBucket]] = defaultdict(dict)
        # flat call log for reporting
        self._call_log: list[CallRecord] = []

    # ------------------------------------------------------------------
    # Pre-call gate
    # ------------------------------------------------------------------

    def allow(
        self,
        user_id: str,
        prompt: str,
        estimated_output_tokens: int = 256,
        call_type: str = "generate_answer",
    ) -> bool:
        """
        Return True if the call is allowed under budget constraints.
        Logs and returns False (fail-fast) if any limit is breached.

        Args:
            user_id:                 Student identifier.
            prompt:                  Full prompt string about to be sent.
            estimated_output_tokens: Rough output size estimate.
            call_type:               Label for logging ("expand_query" etc.).
        """
        today = _today_key()
        input_tokens = _count_tokens(prompt)

        # 1. Hard token size gate (independent of cost)
        if input_tokens > MAX_SINGLE_PROMPT_TOKENS:
            logger.warning(
                f"[CostControl] BLOCKED {call_type} for user={user_id}: "
                f"prompt too large ({input_tokens} tokens > {MAX_SINGLE_PROMPT_TOKENS})"
            )
            self._log_blocked(user_id, input_tokens, estimated_output_tokens, call_type, today)
            return False

        estimated_cost = _estimate_cost(input_tokens, estimated_output_tokens)

        # 2. Global daily budget
        global_bucket = self._get_global_bucket(today)
        if global_bucket.total_cost + estimated_cost > self.global_daily_budget:
            logger.error(
                f"[CostControl] BLOCKED {call_type}: global daily budget "
                f"${self.global_daily_budget:.2f} would be exceeded "
                f"(current=${global_bucket.total_cost:.4f}, est=+${estimated_cost:.4f})"
            )
            self._log_blocked(user_id, input_tokens, estimated_output_tokens, call_type, today)
            return False

        # 3. Per-user daily budget
        user_bucket = self._get_user_bucket(user_id, today)
        if user_bucket.total_cost + estimated_cost > self.user_daily_budget:
            logger.warning(
                f"[CostControl] BLOCKED {call_type} for user={user_id}: "
                f"user daily budget ${self.user_daily_budget:.2f} would be exceeded "
                f"(current=${user_bucket.total_cost:.4f}, est=+${estimated_cost:.4f})"
            )
            self._log_blocked(user_id, input_tokens, estimated_output_tokens, call_type, today)
            return False

        logger.debug(
            f"[CostControl] ALLOW {call_type} user={user_id} "
            f"est_tokens={input_tokens}+{estimated_output_tokens} "
            f"est_cost=${estimated_cost:.5f}"
        )
        return True

    # ------------------------------------------------------------------
    # Post-call recording
    # ------------------------------------------------------------------

    def record(
        self,
        user_id:      str,
        prompt:       str,
        output:       str,
        call_type:    str = "generate_answer",
    ) -> float:
        """
        Record actual token usage after a successful LLM call.

        Returns:
            Actual cost in USD for this call.
        """
        today         = _today_key()
        input_tokens  = _count_tokens(prompt)
        output_tokens = _count_tokens(output)
        cost          = _estimate_cost(input_tokens, output_tokens)

        self._get_global_bucket(today).total_tokens += input_tokens + output_tokens
        self._get_global_bucket(today).total_cost   += cost
        self._get_global_bucket(today).call_count   += 1

        self._get_user_bucket(user_id, today).total_tokens += input_tokens + output_tokens
        self._get_user_bucket(user_id, today).total_cost   += cost
        self._get_user_bucket(user_id, today).call_count   += 1

        self._call_log.append(CallRecord(
            timestamp=time.time(),
            user_id=user_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            call_type=call_type,
        ))

        logger.info(
            f"[CostControl] RECORDED {call_type} user={user_id} "
            f"tokens={input_tokens}+{output_tokens} cost=${cost:.5f} "
            f"(daily_global=${self._get_global_bucket(today).total_cost:.4f})"
        )
        return cost

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def usage_report(self, user_id: Optional[str] = None) -> dict:
        """
        Return a summary dict for monitoring dashboards or audit logs.

        Args:
            user_id: If provided, include per-user breakdown.
        """
        today = _today_key()
        gb = self._get_global_bucket(today)

        report: dict = {
            "date": today,
            "global": {
                "total_tokens":   gb.total_tokens,
                "total_cost_usd": round(gb.total_cost, 6),
                "call_count":     gb.call_count,
                "blocked_count":  gb.blocked_count,
                "budget_usd":     self.global_daily_budget,
                "budget_used_pct": round(gb.total_cost / self.global_daily_budget * 100, 2),
            },
        }

        if user_id:
            ub = self._get_user_bucket(user_id, today)
            report["user"] = {
                "user_id":        user_id,
                "total_tokens":   ub.total_tokens,
                "total_cost_usd": round(ub.total_cost, 6),
                "call_count":     ub.call_count,
                "budget_usd":     self.user_daily_budget,
                "budget_used_pct": round(ub.total_cost / self.user_daily_budget * 100, 2),
            }

        return report

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_global_bucket(self, date: str) -> DailyBucket:
        if date not in self._global:
            self._global[date] = DailyBucket(date=date)
        return self._global[date]

    def _get_user_bucket(self, user_id: str, date: str) -> DailyBucket:
        if date not in self._per_user[user_id]:
            self._per_user[user_id][date] = DailyBucket(date=date)
        return self._per_user[user_id][date]

    def _log_blocked(
        self,
        user_id:       str,
        input_tokens:  int,
        output_tokens: int,
        call_type:     str,
        date:          str,
    ) -> None:
        cost = _estimate_cost(input_tokens, output_tokens)
        self._get_global_bucket(date).blocked_count += 1
        self._get_user_bucket(user_id, date).blocked_count += 1
        self._call_log.append(CallRecord(
            timestamp=time.time(),
            user_id=user_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            call_type=call_type,
            blocked=True,
        ))
