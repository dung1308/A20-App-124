"""
orchestrator/pipeline.py
------------------------
Responsibility: Main request flow controller.
Coordinates the full pipeline for both /api/match and /api/chat:

  Request
    → [InputGuard]      block injection / length violations
    → [RateLimiter]     enforce per-user quota
    → [LLMRouter]       classify intent  (chat only)
    → [Agent]           RAG / CRM / Advisor based on route
    → [OutputGuard]     redact PII, sanitize HTML
    → [Judge]           safety evaluation (fail-safe: reject on error)
    → [AuditLog]        record everything to DB
    → Response
"""

import json
import logging
import time
import urllib.error
import urllib.request
from typing import List, Dict, Any, Optional

from orchestrator.router import LLMRouter
from agents.advisor import AdvisorAgent
from agents.rag import RAGAgent
from agents.crm import CRMAgent
from agents.cv_agent import CVAgent
from services.cv_parser import CVParser
from agents.judge import JudgeAgent
from guards.input_guard import InputGuard
from guards.output_guard import OutputGuard
from guards.rate_limiter import RateLimiter
from utils.logger import get_logger
from services.db_service import DBService
from models.cv_schema import CVSignals
from services.short_memory import ShortTermMemory
from services.long_memory import LongTermMemory
from services.memory_manager import MemoryManager

from config import USE_MOCK, HUMAN_WEBHOOK

logger = get_logger(__name__)

DISCLAIMER = (
    "Kết quả do AI phân tích dựa trên câu trả lời của bạn "
    "— không thay thế buổi tư vấn trực tiếp."
)


class Pipeline:

    def __init__(self, rag_service=None):

        self.router = LLMRouter()
        self.advisor = AdvisorAgent()
        self.rag = RAGAgent()

        # lấy RAG service hiện có
        self.rag_service = rag_service or self.rag.rag_service

        self.crm = CRMAgent()
        self.judge = JudgeAgent()

        self.input_guard = InputGuard()
        self.output_guard = OutputGuard()
        self.rate_limiter = RateLimiter()

        self.cv_parser = CVParser()
        self.cv_agent = CVAgent()

        self.db_service = DBService()
        self.memory = MemoryManager()
        # SHORT TERM
        self.short_memory = ShortTermMemory(max_turns=10)

        # LONG TERM VECTOR MEMORY
        self.memory_collection = (
            self.rag_service.client.get_or_create_collection(
                name="long_term_memory"
            )
        )
        self.long_memory = LongTermMemory(
            self.memory_collection
        )


    # ------------------------------------------------------------------
    # Wizard flow
    # ------------------------------------------------------------------

    def run_match(self, user_id: str, answers: Dict[str, Any], cv_text: str = None, cv_signals: CVSignals = None) -> Dict[str, Any]:
        """
        Full pipeline for POST /api/match (wizard submit).
        Calls AdvisorAgent to produce Top 3 major recommendations.

        Args:
            user_id: Student identifier string.
            answers:  Dict with keys interests, strengths, dislikes, work_style.

        Returns:
            Dict with keys: top3 (list), fallback (bool), disclaimer (str).

        TODO: 1. input_guard.check(str(answers)) — raise HTTPException 400 if blocked.
        TODO: 2. rate_limiter.allow(user_id)     — raise HTTPException 429 if exceeded.
        TODO: 3. raw_result = advisor.match_majors(answers).
        TODO: 4. safe_result = output_guard.redact(raw_result["disclaimer"] + str(raw_result)).
        TODO: 5. judge_result = judge.evaluate(str(answers), str(raw_result)).
        TODO: 6. If judge_result["pass"] is False → return fallback response.
        TODO: 7. audit_log(user_id, answers, raw_result, judge_result).
        TODO: 8. Return raw_result enriched with disclaimer.
        """
        logger.info(f"run_match for user: {user_id}")

        try:
            if USE_MOCK:
                # Simulate realistic processing time for demo mode
                time.sleep(1.0)
                judge_result = {"pass": True, "score": 1.0}
                # Deterministic mock advisor result
                raw_result = {
                    "top3": [
                        {
                            "major_id": "cs",
                            "major_name": "Khoa học Máy tính",
                            "match_reason": "Dựa trên sở thích công nghệ của bạn (Mock).",
                            "match_score": 95,
                            "what_students_do": "Sinh viên CS làm việc với AI và phần mềm."
                        }
                    ],
                    "fallback": False
                }
            else:
                # 1. Process CV if provided (sanitization happens inside parser)
                if not cv_signals:
                    if cv_text:
                        cv_data = self.cv_parser.parse(cv_text)
                        if cv_data:
                            cv_signals = self.cv_agent.generate_signals(cv_data)

                # 2. Match majors using AdvisorAgent
                raw_result = self.advisor.match_majors(answers, cv_signals)
                # 3. Safety check with JudgeAgent (Only in real mode)
                judge_result = self.judge.evaluate(str(answers), str(raw_result))

            if not judge_result.get("pass", False):
                logger.warning(f"Judge rejected match result for {user_id}")
                return {"top3": [], "fallback": True, "disclaimer": DISCLAIMER}

            # 4. Audit logging
            try:
                self._audit_log(user_id, answers, raw_result, judge_result)
            except Exception as audit_err:
                logger.error(f"Audit log failed (non-blocking): {audit_err}")

            return {**raw_result, "disclaimer": DISCLAIMER}

        except Exception as e:
            logger.error(f"Pipeline match failure for {user_id}: {e}")
            return {"top3": [], "fallback": True, "disclaimer": DISCLAIMER}

    def parse_cv(self, text: str) -> Optional[CVSignals]:
        """
        Extract structured signals from CV text.
        """
        try:
            cv_data = self.cv_parser.parse(text)
            if not cv_data:
                return None
            
            signals = self.cv_agent.generate_signals(cv_data)
            return signals
        except Exception as e:
            logger.error(f"Pipeline parse_cv failure: {e}")
            return None

    # ------------------------------------------------------------------
    # Chat flow
    # ------------------------------------------------------------------

    def run_chat(
        self,
        user_id: str,
        message: str,
        history: List[Dict[str, str]],
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:

        logger.info(f"run_chat for user: {user_id}, route pending")

        start_time = time.perf_counter()

        # Persist the incoming user message for DB-backed history and future human handoff.
        try:
            self.db_service.create_user_if_not_exists(user_id)
            session_id = self.db_service.get_or_create_chat_session(user_id, session_id=session_id)
            self.db_service.save_message(user_id, "user", message, agent_type="user_input", session_id=session_id)
        except Exception as e:
            logger.warning(f"Could not save incoming message for user {user_id}: {e}")
            session_id = session_id or "new"

        judge_result = {"pass": True, "score": 1.0}

        handoff_summary = None

        try:

            # =========================================================
            # INPUT GUARD
            # =========================================================

            self.input_guard.check(message)

            # =========================================================
            # RATE LIMIT
            # =========================================================

            if not self.rate_limiter.allow(user_id):

                return {
                    "response": "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.",
                    "intent": "rate_limit",
                    "status": "blocked"
                }

            # =========================================================
            # SHORT-TERM MEMORY
            # =========================================================

            short_memory_context = self.short_memory.get_context(user_id)

            if isinstance(short_memory_context, list):

                short_memory_context = "\n".join([
                    f"{m.get('role', 'user')}: {m.get('content', '')}"
                    for m in short_memory_context
                ])

            # =========================================================
            # LONG-TERM MEMORY
            # =========================================================

            long_memory_context = self.long_memory.retrieve_memories(
                user_id=user_id,
                query=message,
                top_k=3
            )

            if isinstance(long_memory_context, list):

                long_memory_context = "\n".join(long_memory_context)

            # =========================================================
            # BUILD ENHANCED HISTORY
            # =========================================================

            enhanced_history = history.copy()

            # inject short-term memory
            if short_memory_context:

                enhanced_history.append({
                    "role": "system",
                    "content": (
                        "Recent conversation history:\n"
                        f"{short_memory_context}"
                    )
                })

            # inject long-term memory
            if long_memory_context:

                enhanced_history.append({
                    "role": "system",
                    "content": (
                        "Relevant user memories:\n"
                        f"{long_memory_context}"
                    )
                })

            # =========================================================
            # ROUTING
            # =========================================================

            if USE_MOCK:

                logger.info("Pipeline operating in MOCK mode")

                time.sleep(0.7)

                route = self._mock_route(message)

            else:

                logger.info("Pipeline operating in REAL mode")

                route = self.router.route(
                    message,
                    enhanced_history
                )

            if route == "fallback":
                handoff_summary = self.build_human_handoff_summary(user_id)
                self._notify_human_webhook(
                    user_id=user_id,
                    route=route,
                    judge_result=judge_result,
                    handoff_summary=handoff_summary,
                )

            logger.info(
                f"[CHAT_ROUTE] user={user_id} "
                f"intent={route} "
                f"message_preview={message[:80]!r}"
            )

            # =========================================================
            # DISPATCH
            # =========================================================

            enhanced_message = self.memory.build_context(
                message=message,
                history=history,
            )

            raw_response = self._dispatch(
                route=route,
                user_id=user_id,
                message=enhanced_message,
                history=enhanced_history,
                short_term_memory={
                    "short_term": short_memory_context,
                    "long_term": long_memory_context,
                },
            )

            logger.info(
                f"[CHAT_RESPONSE] user={user_id} "
                f"intent={route} "
                f"raw_response_preview={raw_response[:160]!r}"
            )

            # =========================================================
            # OUTPUT GUARD
            # =========================================================

            safe_response = self.output_guard.redact(raw_response)

            # =========================================================
            # JUDGE
            # =========================================================

            if not USE_MOCK:

                judge_result = self.judge.evaluate(
                    message,
                    safe_response
                )

            if not judge_result.get("pass", False):

                logger.warning(
                    f"Judge REJECTED response for user {user_id}. "
                    f"Reason: {judge_result.get('reason')}"
                )

                safe_response = (
                    "Tôi xin lỗi, nhưng tôi không thể trả lời "
                    "câu hỏi này vì lý do an toàn."
                )

                route = "fallback"
                handoff_summary = self.build_human_handoff_summary(user_id)
                self._notify_human_webhook(
                    user_id=user_id,
                    route=route,
                    judge_result=judge_result,
                    handoff_summary=handoff_summary,
                )

            # =========================================================
            # SAVE SHORT-TERM MEMORY
            # =========================================================

            self.short_memory.add_message(
                user_id,
                "user",
                message
            )

            self.short_memory.add_message(
                user_id,
                "assistant",
                safe_response
            )

            # Persist assistant response so handoff summaries include full dialog.
            try:
                self.db_service.save_message(
                    user_id,
                    "assistant",
                    safe_response,
                    agent_type=route,
                    session_id=session_id,
                )
            except Exception as e:
                logger.warning(f"Could not save assistant response for user {user_id}: {e}")

            # =========================================================
            # SAVE LONG-TERM MEMORY
            # =========================================================

            if len(message.strip()) > 20:

                memory_text = f"""
    User: {message}

    Assistant: {safe_response}
    """.strip()

                self.long_memory.save_memory(
                    user_id=user_id,
                    content=memory_text,
                    memory_type="chat",
                    importance=0.7,
                )

            # =========================================================
            # AUDIT LOG
            # =========================================================

            response_time_ms = (time.perf_counter() - start_time) * 1000.0
            fallback_flag = route == "fallback" or not judge_result.get("pass", False)
            ai_resolved = not fallback_flag

            self._audit_log(
                user_id,
                message,
                safe_response,
                judge_result,
                route=route,
                response_time_ms=response_time_ms,
                ai_resolved=ai_resolved,
                fallback=fallback_flag,
            )

            # =========================================================
            # FINAL RESPONSE
            # =========================================================

            status = (
                "success"
                if judge_result.get("pass", False)
                else "rejected"
            )

            return {
                "response": safe_response,
                "intent": route,
                "status": status,
                "handoff_summary": handoff_summary,
                "sessionId": session_id,
            }

        except Exception as e:

            import traceback

            logger.error(traceback.format_exc())

            return {
                "response": (
                    "Hệ thống đang gặp sự cố. "
                    "Vui lòng thử lại sau."
                ),
                "intent": "fallback",
                "status": "error"
            }

    def build_human_handoff_summary(self, user_id: str, limit: int = 50) -> str:
        """Build a short, human-readable handoff summary from DB history.

        This summary is used when the chatbot cannot answer and needs
        a human advisor to understand the user's context quickly.
        """
        profile = self.db_service.get_student_profile(user_id)
        history = self.db_service.get_history(user_id, limit)

        if not profile and not history:
            return (
                "Chưa có đủ dữ liệu hội thoại để tạo bản tóm tắt. "
                "Vui lòng kiểm tra lại sau khi người dùng đã tương tác thêm."
            )

        lines = ["Tóm tắt ngắn gọn cho nhân viên tư vấn:"]

        if profile:
            lines.append("\nThông tin học sinh:")
            if profile.get("full_name"):
                lines.append(f"- Họ tên: {profile.get('full_name')}")
            if profile.get("email"):
                lines.append(f"- Email: {profile.get('email')}")
            if profile.get("phone"):
                lines.append(f"- Số điện thoại: {profile.get('phone')}")
            if profile.get("gpa") is not None:
                lines.append(f"- GPA/Điểm trung bình: {profile.get('gpa')}")
            if profile.get("ielts_score") is not None:
                lines.append(f"- IELTS: {profile.get('ielts_score')}")
            if profile.get("major_interests"):
                interests = ", ".join(profile.get("major_interests", []))
                lines.append(f"- Sở thích / Ngành quan tâm: {interests}")

        if history:
            lines.append("\nCác nội dung chính đã trao đổi (các lượt gần nhất):")
            for turn in history[-20:]:
                prefix = "Học sinh" if turn.get("role") == "user" else "Trợ lý"
                content = turn.get("content", "").replace("\n", " ")
                if len(content) > 220:
                    content = content[:217].rstrip() + "..."
                lines.append(f"- {prefix}: {content}")

        return "\n".join(lines)

    def _notify_human_webhook(
        self,
        user_id: str,
        route: str,
        judge_result: Dict[str, Any],
        handoff_summary: str,
    ) -> None:
        """Send a handoff payload to the configured HUMAN_WEBHOOK."""
        if not HUMAN_WEBHOOK or not HUMAN_WEBHOOK.strip():
            logger.debug("No HUMAN_WEBHOOK configured, skipping handoff notification.")
            return

        payload = {
            "user_id": user_id,
            "route": route,
            "judge_result": judge_result,
            "handoff_summary": handoff_summary,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        data = json.dumps(payload).encode("utf-8")
        max_attempts = 2

        for attempt in range(1, max_attempts + 1):
            request = urllib.request.Request(
                HUMAN_WEBHOOK,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            try:
                with urllib.request.urlopen(request, timeout=5) as response:
                    body = response.read().decode("utf-8", errors="replace")
                    logger.info(
                        f"Sent handoff summary to HUMAN_WEBHOOK (status={response.status}, attempt={attempt}) for user {user_id}."
                    )
                    if body:
                        logger.debug(
                            f"HUMAN_WEBHOOK response body (attempt={attempt}): {body}"
                        )
                    return
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                logger.warning(
                    f"HUMAN_WEBHOOK HTTPError attempt {attempt}/{max_attempts} for user {user_id}: status={e.code}, reason={e.reason}, body={body}"
                )
            except urllib.error.URLError as e:
                logger.warning(
                    f"HUMAN_WEBHOOK URLError attempt {attempt}/{max_attempts} for user {user_id}: {e}"
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error sending handoff webhook attempt {attempt}/{max_attempts} for user {user_id}: {e}"
                )

            if attempt < max_attempts:
                time.sleep(1)

        logger.error(
            f"All {max_attempts} attempts to notify HUMAN_WEBHOOK failed for user {user_id}."
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _dispatch(
        self,
        route: str,
        user_id: str,
        message: str,
        history: List[Dict[str, Any]],
        short_term_memory: Dict[str, Any],
    ) -> str:

        agent_map = {
            "advisor": self.advisor,
            "crm": self.crm,
            "rag": self.rag,
        }

        if route == "fallback":
            return (
                "Bạn muốn được kết nối với "
                "tư vấn viên của chúng tôi không?"
            )

        agent = agent_map.get(route, self.rag)

        return agent.run(
            message=message,
            history=history,
            user_id=user_id,
            short_term_memory=short_term_memory,
        )

    def _mock_route(self, message: str) -> str:
        """Deterministic keyword-based router for Mock mode."""
        msg = message.lower()
        if any(word in msg for word in ["hồ sơ", "điểm", "ielts", "gpa", "thông tin cá nhân"]):
            return "crm"
        if any(word in msg for word in ["ngành", "chọn", "tư vấn", "phù hợp", "match"]):
            return "advisor"
        return "rag"

    def _audit_log(
        self,
        user_id: str,
        input_data: Any,
        output_data: Any,
        judge_result: Dict,
        route: str = "chat",
        response_time_ms: float = 0.0,
        ai_resolved: bool = False,
        fallback: bool = False,
    ) -> None:
        """
        Persist an audit record to the database.

        Args:
            user_id:      Student identifier.
            input_data:   Raw input (answers dict or message string).
            output_data:  Agent output before/after redaction.
            judge_result: Result dict from JudgeAgent.evaluate().
            route:        Final intent route used for the chat response.
            response_time_ms: Measured chat response latency.
            ai_resolved:  True when AI response succeeded without fallback.
            fallback:     True when the response was escalated or rejected.
        """
        logger.info(
            f"AUDIT [{user_id}] route={route} "
            f"judge_pass={judge_result.get('pass')} "
            f"ai_resolved={ai_resolved} fallback={fallback} "
            f"response_time_ms={response_time_ms:.1f}"
        )
        self.db_service.save_audit_log(
            user_id,
            str(input_data),
            str(output_data),
            judge_result,
            route=route,
            response_time_ms=response_time_ms,
            ai_resolved=ai_resolved,
            fallback=fallback,
        )
