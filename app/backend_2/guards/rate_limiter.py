"""
guards/rate_limiter.py
----------------------
Responsibility: Enforce per-user request quotas to prevent abuse and
control LLM cost.

Design:
  - Sliding window counter: tracks request timestamps per user_id.
  - Memory-safe: periodically evicts inactive users to prevent unbounded growth.
  - Config-driven: reads limits from config.py environment variables.

Returns True (allow) or False (block) — caller raises HTTP 429 if blocked.
"""

import time
import logging
from collections import defaultdict, deque
from typing import Deque, Dict

from config import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS
from utils.logger import get_logger

logger = get_logger(__name__)

MAX_TRACKED_USERS: int = 10_000   # Evict when store exceeds this count
CLEANUP_INTERVAL_SECONDS: int = 300  # Run cleanup every 5 minutes


class RateLimiter:
    """
    Sliding-window rate limiter with automatic memory cleanup.
    Thread-safe for single-process use; add a lock for multi-threaded FastAPI workers.
    """

    def __init__(
        self,
        max_requests: int = RATE_LIMIT_MAX_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
    ):
        self.max_requests = max_requests
        self.window = window_seconds
        # user_id → deque of request timestamps
        self.logs: Dict[str, Deque[float]] = defaultdict(deque)
        self.last_cleanup: float = time.time()

    def allow(self, user_id: str) -> bool:
        """
        Check whether a request from user_id is within quota.

        Args:
            user_id: String identifier for the requesting user.

        Returns:
            True  → request is allowed.
            False → rate limit exceeded; caller should return HTTP 429.
        """
        now = time.time()
        self._cleanup_if_needed(now)

        timestamps = self.logs[user_id]

        # Remove timestamps older than the window
        while timestamps and now - timestamps[0] > self.window:
            timestamps.popleft()

        # Check against limit
        if len(timestamps) >= self.max_requests:
            logger.warning(f"RateLimiter: user '{user_id}' exceeded limit ({self.max_requests} req/{self.window}s)")
            return False

        timestamps.append(now)
        return True

    def stats(self) -> Dict:
        """
        Return current limiter statistics for the /metrics endpoint.

        Returns:
            Dict with tracked_users count and config values.

        TODO: Add total_blocked counter (increment in allow() on False return).
        """
        return {
            "tracked_users": len(self.logs),
            "max_requests": self.max_requests,
            "window_seconds": self.window,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _cleanup_if_needed(self, now: float) -> None:
        """
        Evict inactive users if the cleanup interval has elapsed or
        the store is approaching MAX_TRACKED_USERS.

        Args:
            now: Current timestamp from time.time().

        TODO: Check if (now - self.last_cleanup) > CLEANUP_INTERVAL_SECONDS.
        TODO: Also trigger if len(self.logs) > MAX_TRACKED_USERS.
        TODO: Call _cleanup_old_entries(now) and update self.last_cleanup.
        """
        if (
            now - self.last_cleanup > CLEANUP_INTERVAL_SECONDS
            or len(self.logs) > MAX_TRACKED_USERS
        ):
            self._cleanup_old_entries(now)
            self.last_cleanup = now

    def _cleanup_old_entries(self, now: float) -> None:
        """
        Remove users whose entire request history has expired from the window.

        Args:
            now: Current timestamp.

        TODO: 1. For each user_id, drop timestamps older than (now - self.window).
        TODO: 2. Collect user_ids whose deque is now empty.
        TODO: 3. Delete those user_ids from self.logs.
        TODO: 4. Log how many users were evicted.
        """
        to_remove = []
        for uid, timestamps in self.logs.items():
            while timestamps and now - timestamps[0] > self.window:
                timestamps.popleft()
            if not timestamps:
                to_remove.append(uid)

        for uid in to_remove:
            del self.logs[uid]

        if to_remove:
            logger.info(f"RateLimiter: evicted {len(to_remove)} inactive users.")
