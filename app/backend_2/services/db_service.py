"""
services/db_service.py
----------------------
Responsibility: All PostgreSQL interactions via SQLAlchemy ORM.
Single point of DB access — no other file runs raw SQL or uses sessions directly.

Tables managed here:
  - ConversationHistory  (chat messages per user)
  - Student              (CRM profiles)
  - AuditLog             (compliance trail)
  - SecurityEvent        (guardrail events)
"""

import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from collections import defaultdict

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_database_url, USE_MOCK
from models.schemas import User, ChatMessage, ChatSession, Student, AuditLog, AdmissionsData
from utils.logger import get_logger

logger = get_logger(__name__)

# TODO: Import SQLAlchemy Session and ORM models once models/schemas.py is complete
# from sqlalchemy.orm import Session
# from models.schemas import ConversationHistory, Student, AuditLog, SecurityEvent
# from database import get_db_session


class DBService:
    """
    Provides high-level data access methods for all pipeline components.
    All methods accept and return plain Python dicts — no ORM objects leak out.
    """

    def __init__(self):
        self.use_mock = USE_MOCK
        if self.use_mock:
            # user_id -> list of message dicts
            self._history: Dict[str, List[Dict]] = defaultdict(list)
            # user_id -> profile dict
            self._profiles: Dict[str, Dict[str, Any]] = {}
            logger.info("DBService initialised in MOCK mode (in-memory)")
        else:
            engine = create_engine(get_database_url())
            # Ensure tables exist
            from models.schemas import Base
            Base.metadata.create_all(bind=engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            # TODO: Accept a SQLAlchemy Session factory or use dependency injection
            #       via FastAPI's Depends(get_db) pattern.
            logger.info("DBService initialised with PostgreSQL engine")

    # ------------------------------------------------------------------
    # Conversation history
    # ------------------------------------------------------------------

    def save_message(self, user_id: str, role: str, content: str, agent_type: str = "", session_id: Optional[str] = None) -> None:
        """
        Persist one conversation turn to ConversationHistory.

        Args:
            user_id:    Student identifier.
            role:       "user" or "assistant".
            content:    Message text.
            agent_type: Which agent generated this (rag/crm/advisor/judge).
            session_id: Optional chat session ID.

        TODO: 1. Create a ConversationHistory ORM object with all fields + timestamp.
        TODO: 2. Add to DB session and commit.
        TODO: 3. Log at DEBUG level (do NOT log content — may contain PII).
        """
        if self.use_mock:
            self._history[user_id].append({
                "role": role,
                "content": content,
                "agent_type": agent_type,
                "timestamp": datetime.utcnow()
            })
            logger.debug(f"DBService.save_message(MOCK) — user={user_id}, role={role}")
            return

        with self.SessionLocal() as session:
            new_msg = ChatMessage(
                user_id=user_id,
                role=role,
                content=content,
                agent_type=agent_type,
                session_id=session_id,
            )
            session.add(new_msg)
            session.commit()
        logger.debug(f"DBService.save_message() — user={user_id}, role={role}")
        # TODO: Implement DB write

    def get_history(self, user_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """
        Fetch the most recent N conversation turns for a user.

        Args:
            user_id: Student identifier.
            limit:   Max number of turns to return (default 20).

        Returns:
            List of dicts: [{"role": "user"|"assistant", "content": "..."}]
            Ordered oldest → newest.

        TODO: 1. Query ConversationHistory filtered by user_id, ordered by timestamp DESC, limit N.
        TODO: 2. Reverse to get oldest → newest order.
        TODO: 3. Map ORM objects to plain dicts.
        TODO: 4. Return empty list (not raise) if user has no history.
        """
        if self.use_mock:
            msgs = self._history.get(user_id, [])
            # Return last N turns, mapped to standard role/content format
            history = [{"role": m["role"], "content": m["content"]} for m in msgs[-limit:]]
            logger.debug(f"DBService.get_history(MOCK) — user={user_id}, found {len(history)} turns")
            return history

        with self.SessionLocal() as session:
            msgs = session.query(ChatMessage)\
                .filter(ChatMessage.user_id == user_id)\
                .order_by(ChatMessage.timestamp.desc())\
                .limit(limit)\
                .all()
            history = [{"role": m.role, "content": m.content} for m in reversed(msgs)]
            logger.debug(f"DBService.get_history() — user={user_id}, found {len(history)} turns")
            return history
        # TODO: Implement DB read

    # ------------------------------------------------------------------
    # Chat sessions
    # ------------------------------------------------------------------

    def create_chat_session(self, user_id: str, title: str = "Hội thoại mới") -> str:
        """Create a new chat session and return its ID."""
        if self.use_mock:
            session_id = str(uuid.uuid4())
            logger.debug(f"DBService.create_chat_session(MOCK) — user={user_id}, session_id={session_id}")
            return session_id

        with self.SessionLocal() as session:
            new_session = ChatSession(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=title,
            )
            session.add(new_session)
            session.commit()
            return new_session.id

    def get_or_create_chat_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        """Return an existing session ID or create a new one if requested."""
        if self.use_mock:
            if session_id and session_id != "new":
                return session_id
            return str(uuid.uuid4())

        if not session_id or session_id == "new":
            return self.create_chat_session(user_id)

        with self.SessionLocal() as session:
            existing = session.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
            ).first()
            if existing:
                return existing.id
            return self.create_chat_session(user_id)

    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Return the list of chat sessions for a user."""
        if self.use_mock:
            return []

        with self.SessionLocal() as session:
            sessions = session.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.created_at.desc()).all()
            return [
                {
                    "id": s.id,
                    "title": s.title or "Hội thoại mới",
                    "created_at": s.created_at,
                }
                for s in sessions
            ]

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Return all messages for a session."""
        if self.use_mock:
            return []

        with self.SessionLocal() as session:
            msgs = session.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.asc()).all()
            return [
                {
                    "role": m.role,
                    "content": m.content,
                    "agent_type": m.agent_type,
                    "timestamp": m.timestamp,
                }
                for m in msgs
            ]

    def rename_chat_session(self, session_id: str, title: str) -> bool:
        """Rename a chat session."""
        if self.use_mock:
            logger.debug(f"DBService.rename_chat_session(MOCK) — session_id={session_id}, title={title}")
            return True

        with self.SessionLocal() as session:
            session_obj = session.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session_obj:
                return False
            session_obj.title = title
            session.commit()
            return True

    def delete_chat_session(self, session_id: str) -> bool:
        """Delete a chat session and its messages."""
        if self.use_mock:
            logger.debug(f"DBService.delete_chat_session(MOCK) — session_id={session_id}")
            return True

        with self.SessionLocal() as session:
            session_obj = session.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session_obj:
                return False
            session.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
            session.delete(session_obj)
            session.commit()
            return True

    # ------------------------------------------------------------------
    # Student profiles (CRM)
    # ------------------------------------------------------------------

    def get_student_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch student profile from the Student table.

        Args:
            user_id: Student identifier.

        Returns:
            Profile dict or None if user not found.

        TODO: 1. Query Student table by user_id.
        TODO: 2. Return profile_data JSON field as a Python dict.
        TODO: 3. Return None (do NOT raise) if not found.
        """
        if self.use_mock:
            profile = self._profiles.get(user_id)
            logger.debug(f"DBService.get_student_profile(MOCK) — user={user_id}, found={profile is not None}")
            return profile

        with self.SessionLocal() as session:
            student = session.query(Student).filter(Student.user_id == user_id).first()
            if student:
                profile = {
                    "full_name": student.full_name,
                    "email": student.email,
                    "phone": student.phone,
                    "gpa": student.gpa,
                    "ielts_score": student.ielts_score,
                    "major_interests": student.major_interests,
                    "cv_data": student.cv_data,
                    "created_at": student.created_at,
                    "updated_at": student.updated_at,
                }
                logger.debug(f"DBService.get_student_profile() — user={user_id}, found profile")
                return profile
            else:
                logger.debug(f"DBService.get_student_profile() — user={user_id}, not found")
                return None

    def upsert_student_profile(self, user_id: str, profile_data: Dict[str, Any]) -> None:
        """
        Insert or update a student's profile.

        Args:
            user_id:      Student identifier.
            profile_data: Dict of profile fields (gpa, ielts, interests, etc.).

        TODO: 1. Check if Student with user_id exists.
        TODO: 2. If yes → update profile_data and updated_at.
        TODO: 3. If no  → insert new Student row.
        TODO: 4. Commit session.
        """
        if self.use_mock:
            self._profiles[user_id] = profile_data
            logger.debug(f"DBService.upsert_student_profile(MOCK) — user={user_id}")
            return

        with self.SessionLocal() as session:
            student = session.query(Student).filter(Student.user_id == user_id).first()
            if student:
                # Update existing
                for key, value in profile_data.items():
                    setattr(student, key, value)
                student.updated_at = datetime.utcnow()
            else:
                # Insert new
                new_student = Student(user_id=user_id, **profile_data)
                session.add(new_student)
            session.commit()
            logger.debug(f"DBService.upsert_student_profile() — user={user_id}")

    def create_user_if_not_exists(self, user_id: str) -> None:
        """
        Ensure a user record exists in the users table.

        Args:
            user_id: Student identifier.
        """
        if self.use_mock:
            logger.debug(f"DBService.create_user_if_not_exists(MOCK) — user={user_id}")
            return

        with self.SessionLocal() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                new_user = User(user_id=user_id)
                session.add(new_user)
                session.commit()
                logger.info(f"DBService: Created new user record for {user_id}")

    # ------------------------------------------------------------------
    # Audit logging
    # ------------------------------------------------------------------

    def save_audit_log(
        self,
        user_id: str,
        input_text: str,
        output_text: str,
        judge_result: Dict[str, Any],
        route: str = "chat",
        response_time_ms: float = 0.0,
        ai_resolved: bool = False,
        fallback: bool = False,
    ) -> None:
        """
        Persist an audit record for compliance and debugging.

        Args:
            user_id:      Student identifier.
            input_text:   Sanitised user input.
            output_text:  Final agent response (post-redaction).
            judge_result: Dict from JudgeAgent.evaluate().
            route:        Final route/intention used for the response.
            response_time_ms: Total chat response latency in milliseconds.
            ai_resolved:  True when the AI responded successfully without fallback.
            fallback:     True when the system escalated or rejected the AI response.

        TODO: 1. Create AuditLog ORM object with all fields + datetime.utcnow().
        TODO: 2. Store judge_result as JSON in the judge_result column.
        TODO: 3. Commit session.
        TODO: 4. Also append a line to audit_log.json for file-based compliance trail.
        """
        logger.info(
            f"DBService.save_audit_log() — user={user_id}, pass={judge_result.get('pass')}, "
            f"route={route}, ai_resolved={ai_resolved}, fallback={fallback}, "
            f"response_time_ms={response_time_ms:.1f}"
        )
        if self.use_mock:
            logger.debug(f"DBService.save_audit_log(MOCK) — user={user_id}")
            return

        with self.SessionLocal() as session:
            audit = AuditLog(
                user_id=user_id,
                route=route,
                response_time_ms=response_time_ms,
                ai_resolved=ai_resolved,
                fallback=fallback,
                input_data=input_text,
                output_data=output_text,
                judge_result=judge_result,
                timestamp=datetime.utcnow()
            )
            session.add(audit)
            session.commit()
            logger.debug(f"DBService.save_audit_log() — user={user_id}")
