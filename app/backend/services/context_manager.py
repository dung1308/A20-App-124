"""
services/context_manager.py
----------------------------
Responsibility: Control token / context size before any text reaches the LLM.

Rules enforced here (single source of truth):
  - Max tokens per chunk
  - Max total context tokens sent to LLM
  - Max prompt tokens (context + query + prompt template overhead)
  - Truncation strategy: hard cut vs sentence-boundary cut

Token counting uses tiktoken for OpenAI models.
"""

from __future__ import annotations

import re
try:
    import tiktoken
except ImportError:
    tiktoken = None

from typing import List

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Limits  (tune these per model / pricing tier)
# ---------------------------------------------------------------------------

# Gemini Flash context window is large but we self-limit to keep costs low
MAX_CONTEXT_TOKENS   = 1_500   # total tokens allowed across all chunks
MAX_PROMPT_TOKENS    = 2_000   # context + query + template overhead
MAX_ANSWER_TOKENS    = 512     # max_output_tokens passed to Gemini
MAX_CHUNK_TOKENS     = 300     # single chunk hard limit

# Expansion query should be short — reject if the LLM returns something huge
MAX_EXPANDED_QUERY_TOKENS = 60


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _count_tokens(text: str) -> int:
    """
    Count tokens using tiktoken (cl100k_base) for OpenAI.
    Falls back to whitespace approximation if tiktoken is missing.
    """
    if tiktoken:
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            pass
    return max(1, len(text) // 4)
def _truncate_to_tokens(text: str, max_tokens: int) -> str:
    """
    Truncate text to at most `max_tokens` tokens, cutting at a sentence
    boundary when possible, otherwise cutting hard.
    """
    if _count_tokens(text) <= max_tokens:
        return text

    max_chars = max_tokens * 4
    truncated = text[:max_chars]

    # Try to cut at the last sentence boundary
    last_period = max(
        truncated.rfind(". "),
        truncated.rfind(".\n"),
        truncated.rfind("! "),
        truncated.rfind("? "),
    )
    if last_period > max_chars * 0.5:          # only if we keep >50 % of content
        truncated = truncated[: last_period + 1]

    return truncated.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class ContextManager:
    """
    Stateless helper used by RAGService to budget token usage before LLM calls.
    """

    def __init__(
        self,
        max_context_tokens: int = MAX_CONTEXT_TOKENS,
        max_prompt_tokens:  int = MAX_PROMPT_TOKENS,
        max_chunk_tokens:   int = MAX_CHUNK_TOKENS,
        max_answer_tokens:  int = MAX_ANSWER_TOKENS,
    ):
        self.max_context_tokens = max_context_tokens
        self.max_prompt_tokens  = max_prompt_tokens
        self.max_chunk_tokens   = max_chunk_tokens
        self.max_answer_tokens  = max_answer_tokens

    # ------------------------------------------------------------------
    # Chunk-level control
    # ------------------------------------------------------------------

    def truncate_chunk(self, chunk: str) -> str:
        """Ensure a single chunk never exceeds MAX_CHUNK_TOKENS."""
        truncated = _truncate_to_tokens(chunk, self.max_chunk_tokens)
        if truncated != chunk:
            logger.debug(f"Chunk truncated: {_count_tokens(chunk)} → {_count_tokens(truncated)} tokens")
        return truncated

    # ------------------------------------------------------------------
    # Context-level control
    # ------------------------------------------------------------------

    def fit_chunks_to_budget(self, chunks: List[str]) -> List[str]:
        """
        Truncate each chunk individually, then greedily include chunks
        until the total context token budget is exhausted.

        Returns a list of chunks that fits within MAX_CONTEXT_TOKENS.
        """
        result: List[str] = []
        total_tokens = 0

        for raw_chunk in chunks:
            chunk = self.truncate_chunk(raw_chunk)
            chunk_tokens = _count_tokens(chunk)

            if total_tokens + chunk_tokens > self.max_context_tokens:
                logger.info(
                    f"Context budget reached at {total_tokens} tokens "
                    f"({len(result)}/{len(chunks)} chunks used)"
                )
                break

            result.append(chunk)
            total_tokens += chunk_tokens

        logger.debug(f"fit_chunks_to_budget: {total_tokens} tokens across {len(result)} chunks")
        return result

    # ------------------------------------------------------------------
    # Prompt-level control
    # ------------------------------------------------------------------

    def fits_in_prompt(self, prompt: str) -> bool:
        """Return True if the full prompt is within the prompt token limit."""
        tokens = _count_tokens(prompt)
        ok = tokens <= self.max_prompt_tokens
        if not ok:
            logger.warning(f"Prompt too large: {tokens} tokens > limit {self.max_prompt_tokens}")
        return ok

    def trim_prompt(self, prompt: str) -> str:
        """Hard-truncate a prompt that exceeded the limit (last resort)."""
        if self.fits_in_prompt(prompt):
            return prompt
        trimmed = _truncate_to_tokens(prompt, self.max_prompt_tokens)
        logger.warning(
            f"Prompt trimmed: {_count_tokens(prompt)} → {_count_tokens(trimmed)} tokens"
        )
        return trimmed

    # ------------------------------------------------------------------
    # Query expansion guard
    # ------------------------------------------------------------------

    def validate_expanded_query(self, original: str, expanded: str) -> str:
        """
        Reject the expanded query if it is unreasonably long (LLM hallucination).
        Falls back to the original query.
        """
        if _count_tokens(expanded) > MAX_EXPANDED_QUERY_TOKENS:
            logger.warning(
                f"Expanded query too long ({_count_tokens(expanded)} tokens), "
                "falling back to original"
            )
            return original
        return expanded

    # ------------------------------------------------------------------
    # Stats / introspection
    # ------------------------------------------------------------------

    def token_stats(self, chunks: List[str]) -> dict:
        """Return a dict of token counts for observability / logging."""
        counts = [_count_tokens(c) for c in chunks]
        return {
            "num_chunks":   len(chunks),
            "total_tokens": sum(counts),
            "max_chunk":    max(counts) if counts else 0,
            "min_chunk":    min(counts) if counts else 0,
        }
