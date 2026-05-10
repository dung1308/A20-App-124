from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, JSON, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    user_id = Column(String, primary_key=True)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=True)
    role = Column(String)  # "user" or "assistant"
    content = Column(Text)
    agent_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    title = Column(String, default="Hội thoại mới")
    created_at = Column(DateTime, default=datetime.utcnow)

class Student(Base):
    __tablename__ = "students"
    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    full_name = Column(String)
    email = Column(String)
    phone = Column(String)
    gpa = Column(Float)
    ielts_score = Column(Float)
    major_interests = Column(JSON)  # List of interests
    cv_data = Column(Text)  # Raw CV text
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.user_id"))
    route = Column(String)
    response_time_ms = Column(Float)
    ai_resolved = Column(Boolean, default=False)
    fallback = Column(Boolean, default=False)
    input_data = Column(Text)
    output_data = Column(Text)
    judge_result = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AdmissionsData(Base):
    __tablename__ = "admissions_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    major_id = Column(String)
    requirements = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)