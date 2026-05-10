"""
services/rag_service.py (Chroma version)

Safety & observability layers applied to every request:

  1. TIMEOUT + FAIL FAST   — ThreadPoolExecutor with hard wall-clock deadline.
                             Gemini hangs → TimeoutError → fallback, not API hang.

  2. FALLBACK STRATEGY     — LLM failure/timeout:
                               Tier A: top RAG chunk returned directly
                               Tier B: keyword-matched rule-based response
                               Tier C: generic contact message

  3. CONTEXT SIZE CONTROL  — ContextManager enforces per-chunk and total token
                             budgets before any text reaches the LLM.

  4. COST CONTROL          — CostController gates every call against per-user
                             and global daily USD budgets.

  5. OBSERVABILITY         — ObservabilityMiddleware wraps retrieve_and_answer().
                             Every request emits one structured TRACE log line
                             containing: trace_id, user_id, route, latency_ms,
                             step timings, retrieved_docs, llm_errors,
                             fallback_used, cost_usd, token_stats, final_status.
                             The same trace_id is injected into every logger call
                             made during the request (via logger.py context var).
"""

from __future__ import annotations

import re
import copy
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import chromadb

from chromadb.config import Settings

from openai import OpenAI
from services.ltr import LearningToRank
from services.llm_client import LLMClient
from services.context_manager import ContextManager
from services.cost_control import CostController
from services.features import extract_features
from utils.logger import get_logger
from utils.observability import ObservabilityMiddleware, RequestSpan
from config import USE_MOCK, embed_text

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Timeouts
# ---------------------------------------------------------------------------

LLM_TIMEOUT_SECONDS  = 8   # hard deadline for answer generation
QUERY_EXPAND_TIMEOUT = 4   # expansion is best-effort — fail faster

# ---------------------------------------------------------------------------
# Rule-based fallback responses
# ---------------------------------------------------------------------------

RULE_BASED_FALLBACKS: Dict[str, str] = {
    "admission":   "For admissions enquiries please visit vinuni.edu.vn/admissions or email admissions@vinuni.edu.vn.",
    "deadline":    "Application deadlines are published at vinuni.edu.vn/admissions/deadlines.",
    "scholarship": "Scholarship information is available at vinuni.edu.vn/financial-aid.",
    "tuition":     "Tuition and fee schedules are listed at vinuni.edu.vn/tuition.",
    "contact":     "You can reach VinUni at info@vinuni.edu.vn or +84-24-3975-xxxx.",
}
GENERIC_FALLBACK = (
    "I'm currently unable to generate a full answer. "
    "Please contact VinUni directly at info@vinuni.edu.vn for assistance."
)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

QUERY_EXPANSION_PROMPT = (
    "Viết lại câu hỏi sau của học sinh để cụ thể hơn và tối ưu hơn cho việc tìm kiếm thông tin. "
    "Sử dụng lịch sử trò chuyện để giải quyết các đại từ hoặc ngữ cảnh bị thiếu. "
    "Return ONLY the rewritten query, nothing else.\n\n"
    "Lịch sử trò chuyện:\n{history}\n"
    "Original query: {query}\n"
    "Rewritten query:"
)

ANSWER_GENERATION_PROMPT = (
    "Bạn là trợ lý tư vấn tuyển sinh của VinUni.\n"
    "Trả lời câu hỏi của học sinh CHỈ sử dụng thông tin từ Context dưới đây.\n"
    "Nếu Context không có đủ thông tin, hãy trả lời là bạn chưa có thông tin chính xác.\n\n"
    "Context:\n{context}\n\n"
    "Câu hỏi của học sinh: {query}\n\n"
    "Trả lời:"
)

# ---------------------------------------------------------------------------
# Demo corpus
# ---------------------------------------------------------------------------

DEMO_CORPUS: List[Dict[str, str]] = [
    {"id": "cs",           "text": "Khoa học Máy tính (CS) tại VinUni tập trung vào AI, phát triển phần mềm..."},
    {"id": "ee",           "text": "Kỹ thuật Điện — Điện tử (EE) đào tạo về mạch điện, hệ thống nhúng..."},
    {"id": "me",           "text": "Kỹ thuật Cơ khí (ME) đào tạo thiết kế máy móc..."},
    {"id": "bme",          "text": "Kỹ thuật Y sinh (BME)..."},
    {"id": "ba",           "text": "Quản trị Kinh doanh (BA)..."},
    {"id": "finance",      "text": "Tài chính..."},
    {"id": "data_science", "text": "Khoa học Dữ liệu..."},
    {"id": "liberal_arts", "text": "Khoa học Xã hội..."},
    {"id": "architecture", "text": "Kiến trúc..."},
]


# ---------------------------------------------------------------------------
# RAGService
# ---------------------------------------------------------------------------

class RAGService:
    def __init__(self):
        logger.info("Initializing RAGService")

        self.corpus    = DEMO_CORPUS
        self.llm       = LLMClient()
        self.ctx       = ContextManager()
        self.cost      = CostController()
        self.obs       = ObservabilityMiddleware()       # ← Layer 5
        self._executor = ThreadPoolExecutor(max_workers=4)

        # MOCK MODE — keyword search only, no Chroma
        if USE_MOCK:
            logger.info("RAGService in MOCK mode (keyword search)")
            return

        # REAL MODE — Chroma

        self.client = chromadb.PersistentClient(
            path="./chroma_db"
        )
        # Explicitly set embedding_function=None to prevent Chroma from downloading default models.
        self.admission_collection = self.client.get_or_create_collection(name="admissions", embedding_function=None)
        self.faq_collection       = self.client.get_or_create_collection(name="faq", embedding_function=None)
        self.cv_collections: Dict[str, Any] = {}
        self.reranker       = LearningToRank()
        
        # Sửa lỗi uvicorn --reload: Chỉ ingest nếu collection trống
        if self.faq_collection.count() == 0:
            logger.info("FAQ collection empty. Ingesting...")
            self.ingest_faq_folder()

        if self.admission_collection.count() == 0:
            logger.info("Admissions collection empty. Ingesting...")
            self._ingest_admissions()

    # ------------------------------------------------------------------
    # Layer 1: TIMEOUT WRAPPER
    # ------------------------------------------------------------------

    def _call_llm_with_timeout(
        self,
        prompt:   str,
        timeout:  float = LLM_TIMEOUT_SECONDS,
        span:     Optional[RequestSpan] = None,
        step_name: str = "llm_call",
    ) -> Optional[str]:
        """
        Submit self.llm.generate(prompt) to a thread pool and wait at most
        `timeout` seconds. Returns None on timeout or any exception.

        If a RequestSpan is provided, the sub-step timing and any errors
        are recorded directly onto the span for the TRACE summary.
        """
        future = self._executor.submit(self.llm.generate, prompt)

        ctx = span.step(step_name) if span else _noop_context()
        with ctx:
            try:
                result = future.result(timeout=timeout)
                return result
            except FuturesTimeoutError:
                msg = f"LLM call '{step_name}' exceeded {timeout}s"
                logger.warning(f"[Timeout] {msg}")
                if span:
                    span.add_llm_error("timeout", msg)
                future.cancel()
                return None
            except Exception as exc:
                msg = str(exc)
                logger.warning(f"[LLMError] {step_name}: {msg}")
                if span:
                    span.add_llm_error("api_error", msg)
                return None

    # ------------------------------------------------------------------
    # Layer 2: FALLBACK STRATEGY
    # ------------------------------------------------------------------

    def _fallback_response(
        self,
        query:  str,
        chunks: List[str],
        span:   Optional[RequestSpan] = None,
    ) -> str:
        """
        Tier A — top RAG chunk returned directly.
        Tier B — keyword-matched rule-based response.
        Tier C — generic catch-all with contact info.
        """
        # Tier A
        if chunks:
            logger.info("[Fallback] Returning top RAG chunk directly")
            if span:
                span.set_fallback("chunk")
            return f"[Based on available information]\n\n{chunks[0]}"

        # Tier B
        q_lower = query.lower()
        for keyword, response in RULE_BASED_FALLBACKS.items():
            if keyword in q_lower:
                logger.info(f"[Fallback] Rule-based match on keyword='{keyword}'")
                if span:
                    span.set_fallback("rule")
                return response

        # Tier C
        logger.info("[Fallback] Using generic fallback response")
        if span:
            span.set_fallback("generic")
        return GENERIC_FALLBACK

    # ------------------------------------------------------------------
    # LLM helpers  (layers 1-4, span-aware)
    # ------------------------------------------------------------------
    def embed_text(self, text: str):
        """
        Embed text using OpenAI embedding API.
        Returns a list of floats or None on failure.

        In MOCK mode, returns a dummy embedding.
        """
        return embed_text(text)

    def expand_query(
        self,
        query:   str,
        history: List[Dict[str, Any]] = None,
        user_id: str = "system",
        span:    Optional[RequestSpan] = None,
    ) -> str:
        """
        Rewrite the query for better retrieval coverage.
        Best-effort: any failure silently returns the original query.
        """
        # Format history turns for context
        history_text = ""
        if history:
            history_text = "\n".join([
                f"{'Học sinh' if t.get('role')=='user' else 'Trợ lý'}: {t.get('content')}" 
                for t in history[-3:] # Use last 3 turns for context
            ])

        prompt = QUERY_EXPANSION_PROMPT.format(query=query, history=history_text or "Không có lịch sử.")

        # Layer 4: cost gate
        if not self.cost.allow(user_id, prompt, estimated_output_tokens=30, call_type="expand_query"):
            logger.info("[CostBlock] expand_query skipped — budget exceeded")
            if span:
                span.add_llm_error("cost_block", "expand_query budget exceeded")
            return query

        # Layer 1: timeout-guarded call
        result = self._call_llm_with_timeout(
            prompt, timeout=QUERY_EXPAND_TIMEOUT,
            span=span, step_name="expand_query",
        )

        if not result or result == "I don't know":
            return query

        # Layer 3: reject oversized expansions
        validated = self.ctx.validate_expanded_query(query, result)
        self.cost.record(user_id, prompt, validated, call_type="expand_query")
        logger.info(f"Query expanded: '{query[:50]}' → '{validated[:50]}'")
        return validated

    def generate_answer(
        self,
        query:          str,
        context_chunks: List[str],
        user_id:        str = "system",
        span:           Optional[RequestSpan] = None,
    ) -> str:
        """
        Synthesize a final answer from retrieved context.
        All four safety layers applied in sequence.

        Layer 3 → token budget fitting + prompt trimming
        Layer 4 → cost gate
        Layer 1 → timeout-guarded LLM call
        Layer 2 → fallback on any failure
        """
        # Layer 3a: fit chunks to token budget
        fitted_chunks = self.ctx.fit_chunks_to_budget(context_chunks)
        if span:
            span.set_token_stats(self.ctx.token_stats(fitted_chunks))

        if not fitted_chunks:
            logger.warning("[ContextManager] No chunks survived budget fitting — fallback")
            return self._fallback_response(query, context_chunks, span=span)

        context = "\n\n".join(fitted_chunks)
        prompt  = ANSWER_GENERATION_PROMPT.format(context=context, query=query)

        # Layer 3b: hard-trim prompt if still oversized
        prompt = self.ctx.trim_prompt(prompt)

        # Layer 4: cost gate
        if not self.cost.allow(
            user_id, prompt,
            estimated_output_tokens=self.ctx.max_answer_tokens,
            call_type="generate_answer",
        ):
            logger.warning("[CostBlock] generate_answer blocked — returning fallback")
            if span:
                span.set_fallback("blocked").set_status("blocked")
            return self._fallback_response(query, fitted_chunks, span=span)

        # Layer 1: timeout-guarded LLM call
        answer = self._call_llm_with_timeout(
            prompt, timeout=LLM_TIMEOUT_SECONDS,
            span=span, step_name="generate_answer",
        )

        # Layer 2: fallback if LLM returned nothing
        if not answer or answer == "I don't know":
            return self._fallback_response(query, fitted_chunks, span=span)

        # Record actual cost
        cost = self.cost.record(user_id, prompt, answer, call_type="generate_answer")
        if span:
            span.set_cost(cost)

        logger.info(f"generate_answer OK — query='{query[:60]}'")
        return answer

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        user_id: Optional[str] = None,
        expand: bool = True,
        span: Optional[RequestSpan] = None,
        history: List[Dict[str, Any]] = None,
    ) -> List[str]:

        retrieval_query = (
            self.expand_query(query, user_id=user_id or "system", span=span, history=history)
            if expand else query
        )

        if USE_MOCK:
            return self._keyword_search(retrieval_query, top_k)

        # embedding
        query_embedding = self.embed_text(retrieval_query)
        if query_embedding is None:
            logger.warning("Embedding failed → fallback keyword search")
            return self._keyword_search(retrieval_query, top_k)

        # query both collections (HYBRID)
        step_ctx = span.step("chroma_query") if span else _noop_context()
        with step_ctx:
            try:
                res_adm = self.admission_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=["documents", "distances", "metadatas"]
                )

                res_faq = self.faq_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=["documents", "distances", "metadatas"]
                )

            except Exception as e:
                logger.error(f"Chroma query failed: {e}")
                return self._keyword_search(retrieval_query, top_k)

        # extract safely
        def safe_extract(res):
            if not res or "documents" not in res:
                return [], [], []
            docs = res.get("documents", [[]])[0] or []
            dists = res.get("distances", [[]])[0] or []
            metas = res.get("metadatas", [[]])[0] or [{} for _ in docs]
            return docs, dists, metas

        docs_adm, dist_adm, meta_adm = safe_extract(res_adm)
        docs_faq, dist_faq, meta_faq = safe_extract(res_faq)

        # merge (HYBRID CORE)
        docs = docs_adm + docs_faq
        distances = dist_adm + dist_faq
        metadatas = meta_adm + meta_faq

        if not docs:
            logger.warning("No docs from hybrid → fallback keyword")
            return self._keyword_search(retrieval_query, top_k)

        # rerank
        rerank_ctx = span.step("reranker") if span else _noop_context()
        with rerank_ctx:
            try:
                reranked = self.reranker.rerank(
                    query=retrieval_query,
                    docs=docs,
                    distances=distances,
                    metadatas=metadatas,
                    top_k=top_k,
                )
            except Exception as e:
                logger.error(f"Reranker failed: {e}")
                return docs[:top_k]

        return reranked

    # ------------------------------------------------------------------
    # Layer 5: PRIMARY ENTRY POINT — full observability trace
    # ------------------------------------------------------------------

    def retrieve_and_answer(
        self,
        query:   str,
        top_k:   int = 3,
        history: List[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Primary entry point for RAGAgent.

        Wraps the full pipeline inside an ObservabilityMiddleware trace:
          retrieve → context-fit → generate (timeout + fallback + cost)

        Every sub-step is timed. On exit, a single TRACE log line is emitted
        with: trace_id, user_id, route, latency_ms, step timings,
        retrieved_docs, llm_errors, fallback_used, cost_usd, token_stats,
        final_status.
        """
        _user_id = user_id or "anonymous"

        with self.obs.trace(user_id=_user_id, route="retrieve_and_answer") as span:

            # Retrieval (chroma_query + reranker steps timed inside retrieve())
            with span.step("retrieval"):
                docs = self.retrieve(
                    query, top_k=top_k, user_id=_user_id,
                    expand=True, span=span, history=history
                )

            # Record what we retrieved for debugging
            span.set_retrieved_docs(docs)

            if not docs:
                logger.warning("No documents retrieved — going straight to fallback")
                answer = self._fallback_response(query, [], span=span)
                span.set_status("fallback")
                return answer

            # Generation (context fitting + LLM call timed inside generate_answer())
            answer = self.generate_answer(
                query, docs, user_id=_user_id, span=span,
            )

            # Final status: generate_answer sets fallback/blocked on span internally;
            # only set "ok" if no fallback was triggered.
            if span.fallback_used == "none":
                span.set_status("ok")

        return answer

    # ------------------------------------------------------------------
    # retrieve_with_details — training use, no observability overhead
    # ------------------------------------------------------------------

    def retrieve_with_details(
        self,
        query:   str,
        top_k:   int = 3,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Raw retrieval with embeddings — used for LTR training.
        No expansion, no reranking, no LLM, no observability span.
        """
        if USE_MOCK:
            mock_docs = self._keyword_search(query, top_k)
            return [{"text": doc, "distance": 0.1, "metadata": {"source": "mock"}} for doc in mock_docs]

        query_embedding = self.embed_text(query)
        if query_embedding is None:
            mock_docs = self._keyword_search(query, top_k)
            return [{"text": doc, "distance": 0.1, "metadata": {"source": "mock"}} for doc in mock_docs]

        vector_candidates_raw = []

        # Main collections (Admissions + FAQ)
        for collection_name, coll in [
            ("admissions", self.admission_collection),
            ("faq", self.faq_collection)
        ]:
            res = coll.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "distances", "metadatas", "embeddings"],
            )
            docs  = res.get("documents", [[]])[0]
            dists = res.get("distances",  [[]])[0]
            metas = res.get("metadatas",  [[]])[0] or [{} for _ in docs]
            embs  = res.get("embeddings", [[]])[0] or [None for _ in docs]
            for doc, dist, meta, emb in zip(docs, dists, metas, embs):
                meta_copy = copy.deepcopy(meta)
                meta_copy.setdefault("source", collection_name)
                vector_candidates_raw.append((doc, dist, meta_copy, emb))

        # CV collection
        if user_id and user_id in self.cv_collections:
            cv_res = self.cv_collections[user_id].query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "distances", "metadatas", "embeddings"],
            )
            cv_docs  = cv_res.get("documents", [[]])[0]
            cv_dists = cv_res.get("distances",  [[]])[0]
            cv_metas = cv_res.get("metadatas",  [[]])[0] or [{} for _ in cv_docs]
            cv_embs  = cv_res.get("embeddings", [[]])[0] or [None for _ in cv_docs]
            for doc, dist, meta, emb in zip(cv_docs, cv_dists, cv_metas, cv_embs):
                meta.setdefault("source", "cv")
                vector_candidates_raw.append((doc, dist, copy.deepcopy(meta), emb))

        detailed_candidates: List[Dict[str, Any]] = []
        seen_docs: set = set()

        for doc, dist, meta, emb in vector_candidates_raw:
            if doc not in seen_docs and dist < 1.2:
                detailed_candidates.append({
                    "text": doc, "distance": dist, "metadata": meta,
                    "embedding": emb, "query_embedding": query_embedding,
                })
                seen_docs.add(doc)

        for doc in self._keyword_search(query, top_k):
            if doc not in seen_docs:
                detailed_candidates.append({"text": doc, "distance": 0.5, "metadata": {"source": "keyword"}})
                seen_docs.add(doc)

        return detailed_candidates

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------
    def ingest_faq_folder(self, folder_path="data/faq"):
        import json
        from pathlib import Path

        folder = Path(folder_path)

        ids, documents, embeddings, metadatas = [], [], [], []

        idx = 0

        for file in folder.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                q = item.get("question", "")
                a = item.get("answer", "")
                section = item.get("section", "")
                url = item.get("url", "")

                if not q or not a:
                    continue

                # 👉 rất quan trọng: ưu tiên question
                text = f"""
                Question: {q}
                Answer: {a}
                """.strip()

                emb = self.embed_text(text)
                if emb is None:
                    continue

                ids.append(f"{file.stem}_{item['id']}_{idx}")
                documents.append(text)
                embeddings.append(emb)

                metadatas.append({
                    "type": "faq",
                    "section": section,
                    "url": url
                })

                idx += 1

        if ids:
            self.faq_collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

        logger.info(f"Ingested {len(ids)} FAQ items")
    def _ingest_admissions(self, data_dir="data/admissions"):
        import json
        from pathlib import Path

        data_dir = Path(data_dir)

        ids, documents, embeddings, metadatas = [], [], [], []

        for file in data_dir.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                text = item.get("text", "")
                section = item.get("section", "")
                source = item.get("source", "")
                url = item.get("url", "")

                # 👉 enrich text (RẤT QUAN TRỌNG)
                full_text = f"""
                Section: {section}
                Source: {source}
                Content: {text}
                """.strip()

                if not full_text:
                    continue

                chunks = chunk_text(full_text)

                for i, chunk in enumerate(chunks):
                    emb = self.embed_text(chunk)
                    if emb is None:
                        continue

                    ids.append(f"{item['id']}_{i}")
                    documents.append(chunk)
                    embeddings.append(emb)

                    metadatas.append({
                        "type": "admission",
                        "section": section,
                        "source": source,
                        "url": url
                    })

        if ids:
            self.admission_collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

        logger.info(f"Ingested {len(ids)} admission chunks")

    def ingest_cv(self, user_id: str, cv_text: str):
        if USE_MOCK:
            return
        logger.info(f"Ingesting CV for user {user_id}")
        collection = self.client.get_or_create_collection(name=f"cv_{user_id}")
        chunks = chunk_text(cv_text)
        ids, documents, embeddings = [], [], []
        for i, chunk in enumerate(chunks):
            emb = self.embed_text(chunk)
            if emb is None:
                continue
            ids.append(f"{user_id}_{i}")
            documents.append(chunk)
            embeddings.append(emb)
        if ids:
            collection.add(
                ids=ids, documents=documents, embeddings=embeddings,
                metadatas=[{"source": "cv", "user_id": user_id} for _ in documents],
            )
        self.cv_collections[user_id] = collection

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate_reranker(self, test_cases: List[Dict[str, Any]], k: int = 3) -> float:
        p_at_k_list = []
        for case in test_cases:
            results   = self.retrieve(case["query"], top_k=k, expand=False)
            relevance = [1 if doc == case["expected_doc"] else 0 for doc in results]
            p_at_k_list.append(precision_at_k(relevance, k))
        avg = sum(p_at_k_list) / len(p_at_k_list) if p_at_k_list else 0.0
        logger.info(f"Reranker Evaluation — Average Precision@{k}: {avg:.4f}")
        return avg

    # ------------------------------------------------------------------
    # Cost report passthrough
    # ------------------------------------------------------------------

    def cost_report(self, user_id: Optional[str] = None) -> dict:
        """Return today's cost/usage summary from CostController."""
        return self.cost.usage_report(user_id=user_id)

    # ------------------------------------------------------------------
    # MOCK fallback
    # ------------------------------------------------------------------

    def _keyword_search(self, query: str, top_k: int) -> List[str]:
        query_words = set(re.findall(r"\w+", query.lower()))
        scored = [
            (len(query_words & set(re.findall(r"\w+", doc["text"].lower()))), doc["text"])
            for doc in self.corpus
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [text for score, text in scored[:top_k] if score > 0]


# ---------------------------------------------------------------------------
# Internal helper: no-op context manager for when span is None
# ---------------------------------------------------------------------------

from contextlib import contextmanager

@contextmanager
def _noop_context():
    """Dummy context manager so span.step() calls are always safe."""
    yield


# ---------------------------------------------------------------------------
# Module-level utilities
# ---------------------------------------------------------------------------

def chunk_text(text: str, max_tokens: int = 200) -> List[str]:
    """Chunk text by semantic boundaries (headings, bullets, paragraphs)."""
    sections = re.split(r"\n{2,}|•|- ", text)
    chunks: List[str] = []
    current: List[str] = []
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        words = sec.split()
        if not words:
            continue
        if len(current) + len(words) > max_tokens:
            if current:
                chunks.append(" ".join(current))
            current = words
        else:
            current.extend(words)
    if current:
        chunks.append(" ".join(current))
    return chunks


def compress_context(chunks: List[str], max_chars: int = 1000) -> List[str]:
    """Legacy character-budget trimmer — prefer ContextManager.fit_chunks_to_budget()."""
    result, total = [], 0
    for c in chunks:
        if total + len(c) > max_chars:
            break
        result.append(c)
        total += len(c)
    return result


def generate_training_data(
    queries: List[str],
    retrieved_results: Dict[str, List[Dict[str, Any]]],
) -> Tuple[np.ndarray, np.ndarray]:
    """Bootstrap LTR training data: first doc = relevant (1), rest = not (0)."""
    X, y = [], []
    for query in queries:
        for i, doc_data in enumerate(retrieved_results.get(query, [])):
            features = extract_features(
                query, doc_data["text"],
                doc_data["distance"], doc_data.get("metadata", {}),
            )
            X.append(features)
            y.append(1 if i == 0 else 0)
    return np.array(X), np.array(y)


def precision_at_k(results: List[int], k: int = 3) -> float:
    return sum(results[:k]) / k