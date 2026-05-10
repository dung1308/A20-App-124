"""
utils/observability.py
-----------------------
Responsibility: Per-request structured observability.

What this captures for every RAG pipeline call:
  - trace_id          unique request identifier (injected into every log line)
  - user_id           student identifier
  - route             which pipeline path was taken (rag / expand / fallback …)
  - latency_ms        wall-clock time for the full call and each sub-step
  - llm_errors        list of error/timeout events that occurred
  - retrieved_docs    top-k docs returned by retrieval (truncated for log safety)
  - fallback_used     which fallback tier fired (none / chunk / rule / generic)
  - cost_usd          estimated cost for this request (from CostController)
  - token_stats       input/output token counts
  - final_status      "ok" | "fallback" | "blocked" | "error"

Usage inside RAGService:

    from utils.observability import ObservabilityMiddleware

    obs = ObservabilityMiddleware()   # one per RAGService instance

    # Wrap the full request:
    with obs.trace(user_id="u42", route="retrieve_and_answer") as span:
        docs = self.retrieve(query)
        span.set_retrieved_docs(docs)

        with span.step("generate_answer"):
            answer = self.generate_answer(query, docs)

        span.set_status("ok")

    # The span emits a single structured summary log on __exit__.

Reading traces:
    Pair with logger.py's trace_id injection — every logger.info() call inside
    the `with obs.trace(...)` block will carry the same trace_id, so you can
    grep a single ID to reconstruct the full request timeline.
"""

from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, List, Optional

from utils.logger import get_logger, set_trace_id, clear_trace_id

logger = get_logger(__name__)

# Max characters of each retrieved doc to log (avoid huge log lines)
DOC_PREVIEW_CHARS = 120


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class StepTiming:
    name:       str
    start_ms:   float
    end_ms:     float = 0.0

    @property
    def duration_ms(self) -> float:
        return round(self.end_ms - self.start_ms, 2)


@dataclass
class RequestSpan:
    """
    Mutable record built up during a single request.
    Emits a structured summary log on close().
    """
    trace_id:      str
    user_id:       str
    route:         str
    start_time:    float                   = field(default_factory=time.monotonic)

    # Populated by callers
    retrieved_docs: List[str]              = field(default_factory=list)
    llm_errors:     List[Dict[str, Any]]   = field(default_factory=list)
    fallback_used:  str                    = "none"   # none|chunk|rule|generic|blocked
    cost_usd:       float                  = 0.0
    token_stats:    Dict[str, int]         = field(default_factory=dict)
    final_status:   str                    = "ok"     # ok|fallback|blocked|error
    extra:          Dict[str, Any]         = field(default_factory=dict)

    # Internal step timings
    _steps: List[StepTiming]              = field(default_factory=list)

    # ------------------------------------------------------------------
    # Public setters  (fluent — return self for chaining)
    # ------------------------------------------------------------------

    def set_retrieved_docs(self, docs: List[str]) -> "RequestSpan":
        """Store truncated previews of retrieved documents."""
        self.retrieved_docs = [d[:DOC_PREVIEW_CHARS] + "…" if len(d) > DOC_PREVIEW_CHARS else d
                               for d in docs]
        return self

    def add_llm_error(self, error_type: str, detail: str) -> "RequestSpan":
        """Record an LLM timeout, API error, or cost-block event."""
        self.llm_errors.append({
            "type":      error_type,
            "detail":    detail,
            "elapsed_ms": round((time.monotonic() - self.start_time) * 1000, 2),
        })
        return self

    def set_fallback(self, tier: str) -> "RequestSpan":
        """tier: 'chunk' | 'rule' | 'generic' | 'blocked'"""
        self.fallback_used = tier
        if self.final_status == "ok":
            self.final_status = "fallback"
        return self

    def set_cost(self, cost_usd: float) -> "RequestSpan":
        self.cost_usd = round(cost_usd, 6)
        return self

    def set_token_stats(self, stats: Dict[str, int]) -> "RequestSpan":
        self.token_stats = stats
        return self

    def set_status(self, status: str) -> "RequestSpan":
        """Override final_status: 'ok' | 'fallback' | 'blocked' | 'error'"""
        self.final_status = status
        return self

    def set_extra(self, **kwargs: Any) -> "RequestSpan":
        """Attach arbitrary key-value pairs to the summary (e.g. reranker score)."""
        self.extra.update(kwargs)
        return self

    # ------------------------------------------------------------------
    # Step timing context manager
    # ------------------------------------------------------------------

    @contextmanager
    def step(self, name: str) -> Generator[None, None, None]:
        """
        Time a sub-step and append it to _steps.

        Usage:
            with span.step("chroma_query"):
                results = collection.query(...)
        """
        timing = StepTiming(name=name, start_ms=time.monotonic() * 1000)
        try:
            yield
        finally:
            timing.end_ms = time.monotonic() * 1000
            self._steps.append(timing)
            logger.debug(f"[{self.trace_id}] step={name} {timing.duration_ms}ms")

    # ------------------------------------------------------------------
    # Emit summary
    # ------------------------------------------------------------------

    def close(self) -> None:
        """
        Emit one structured summary log line.
        Called automatically by ObservabilityMiddleware.trace().
        """
        total_ms = round((time.monotonic() - self.start_time) * 1000, 2)

        summary: Dict[str, Any] = {
            "event":          "request_trace",
            "trace_id":       self.trace_id,
            "user_id":        self.user_id,
            "route":          self.route,
            "status":         self.final_status,
            "latency_ms":     total_ms,
            "steps_ms":       {s.name: s.duration_ms for s in self._steps},
            "retrieved_docs": self.retrieved_docs,
            "llm_errors":     self.llm_errors,
            "fallback_used":  self.fallback_used,
            "cost_usd":       self.cost_usd,
            "token_stats":    self.token_stats,
        }
        if self.extra:
            summary["extra"] = self.extra

        # Log level escalates on non-ok outcomes
        if self.final_status == "error":
            logger.error(f"TRACE {summary}")
        elif self.final_status in ("fallback", "blocked"):
            logger.warning(f"TRACE {summary}")
        else:
            logger.info(f"TRACE {summary}")


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class ObservabilityMiddleware:
    """
    Thin wrapper that creates RequestSpan objects, manages the trace_id
    context variable in logger.py, and ensures close() is always called.

    One instance lives on RAGService (self.obs = ObservabilityMiddleware()).
    """

    @contextmanager
    def trace(
        self,
        user_id: str,
        route:   str,
    ) -> Generator[RequestSpan, None, None]:
        """
        Context manager that:
          1. Generates a unique trace_id.
          2. Injects it into the logger context (all log lines get trace_id).
          3. Yields a mutable RequestSpan for the caller to populate.
          4. Always calls span.close() on exit (even on exception).
          5. Clears the trace context.

        Usage:
            with self.obs.trace(user_id=user_id, route="retrieve_and_answer") as span:
                docs = self.retrieve(query)
                span.set_retrieved_docs(docs)
                answer = self.generate_answer(query, docs)
                span.set_status("ok")
        """
        trace_id = f"req-{uuid.uuid4().hex[:12]}"
        set_trace_id(trace_id)

        span = RequestSpan(
            trace_id=trace_id,
            user_id=user_id,
            route=route,
        )

        logger.info(f"[{trace_id}] START route={route} user={user_id}")

        try:
            yield span
        except Exception as exc:
            span.set_status("error")
            span.add_llm_error("unhandled_exception", str(exc))
            logger.exception(f"[{trace_id}] UNHANDLED exception in route={route}: {exc}")
            raise
        finally:
            span.close()
            clear_trace_id()
