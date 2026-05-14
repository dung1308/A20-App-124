from dotenv import load_dotenv
load_dotenv()  # This must be called before importing pipeline or database

import uvicorn
import os
import io
import tempfile
import time
import jwt
import re
import uuid
import threading
import json
import ast
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import logging
from fastapi import FastAPI, HTTPException, Depends, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from fastapi.security import OAuth2PasswordBearer
from fastapi.exceptions import RequestValidationError

from orchestrator.pipeline import Pipeline
from utils.logger import get_logger
from fastapi import UploadFile, File
import database
from services.pdf_loader import extract_text_from_pdf
from services.metric_service import MetricService
from config import CORS_ORIGINS
from guards.rate_limiter import RateLimiter
from guards.admin_audit import AdminAuditMiddleware

# Suppress noisy font warnings from pdfminer/pdfplumber
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# Google Auth imports
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com")
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"

# Global RAG Configuration (In-memory for now, could be in DB)
rag_config = {
    "sync_interval_hours": 24
}

# Define where to get the token (header: Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# --- Permission Mapping ---
ROLE_PERMISSIONS = {
    "admin": ["system:all", "db:manage", "tokens:view", "profile:edit"],
    "editor": ["tokens:view", "profile:edit"],
    "user": ["profile:edit", "match:run"]
}

logger = get_logger(__name__)

app = FastAPI(
    title="VinUni Admission Assistant API",
    description="Backend API for major matching and admission chat support.",
    version="0.1.0"
)

# --- Helper Security Functions ---
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=1440)  # 24h
    
    role = data.get("role", "user")
    base_permissions = ROLE_PERMISSIONS.get(role, [])
    # Merge role-based permissions with custom database-persisted permissions
    custom_permissions = data.get("permissions") or []
    all_permissions = list(set(base_permissions + custom_permissions))
    
    to_encode.update({"exp": expire, "permissions": all_permissions})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to validate JWT and return current user info."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("JWT payload missing 'sub' claim")
            raise credentials_exception
        try:
            profile = pipeline.db_service.get_student_profile(email)
            if profile and profile.get("blacklisted"):
                raise HTTPException(status_code=403, detail="TÃ i khoáº£n nÃ y Ä‘Ã£ bá»‹ khá»‘a trong há»‡ thá»‘ng.")
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Could not verify blacklist status for {email}: {e}")
        return {
            "email": email, 
            "role": payload.get("role"), 
            "permissions": payload.get("permissions", [])
        }
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise HTTPException(
            status_code=401,
            detail="Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        logger.error(f"JWT verification error: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise credentials_exception

class RoleChecker:
    """Class-based dependency to check for various user roles."""
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in self.allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Quyền truy cập bị từ chối. Yêu cầu một trong các vai trò: {', '.join(self.allowed_roles)}"
            )
        return current_user

# Define reusable instances for common permission sets
admin_required = RoleChecker(["admin"])
staff_required = RoleChecker(["admin", "editor"])
user_required = RoleChecker(["admin", "user", "editor"])

def sanitize_id(raw_id: str) -> str:
    """Sanitizes strings to be used as database identifiers (namespaces/collection names)."""
    if raw_id is None or not str(raw_id).strip():
        return "anonymous"
        
    # Replace anything not alpha-numeric, dot, underscore, or dash with underscore
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', str(raw_id))
    # Ensure it starts and ends with alpha-numeric (stripping leading/trailing symbols)
    return sanitized.strip('._-')

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database & Pipeline Initialization ---
# We initialize the database at the global level to ensure SessionLocal is available 
# when the Pipeline (and its nested agents) are instantiated below.
try:
    database.init_database()
    logger.info("Database initialized at module level.")
    
    # Run migrations immediately after DB init so tables (like 'prompts') 
    # exist before the Pipeline/Agents are created below.
    database.get_database_info() # Warm up connection
except Exception as e:
    logger.critical(f"CRITICAL: Failed to initialize database: {e}")
    raise SystemExit(1)

# Initialize the Orchestrator Pipeline
pipeline = Pipeline()

def run_periodic_ingestion(interval_hours: int = 12):
    """Background thread to refresh RAG data periodically."""
    interval_seconds = interval_hours * 3600
    logger.info(f"Background sync thread started. Interval: {interval_hours}h")
    while True:
        time.sleep(interval_seconds)
        try:
            logger.info("Starting periodic RAG data sync...")
            pipeline.rag.rag_service.sync_all()
            logger.info("Periodic RAG data sync completed successfully.")
        except Exception as e:
            logger.error(f"Periodic RAG sync failed: {e}")

# Register the Admin Audit Middleware
app.add_middleware(AdminAuditMiddleware, pipeline=pipeline)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize database when the application starts."""
    # Note: database.init_database() is now called at module level to support Agent init.
    try:
        # Run migrations and start background tasks
        # We call it again here just to be safe, but it's now primarily 
        # for background thread orchestration.
        logger.info("Running background task synchronization...")
        
        pipeline.db_service.migrate_db()
        
        # Start periodic ingestion in a background thread
        # This ensures it doesn't block the main API service
        # Thay đổi args=(24,) cho mỗi ngày, hoặc args=(48,) cho mỗi 2 ngày
        sync_thread = threading.Thread(target=run_periodic_ingestion, args=(24,), daemon=True)
        sync_thread.start()
        
    except Exception as e:
        logger.error(f"Error during startup_event tasks: {e}")
        # We don't necessarily exit here as the core DB connection was verified above.

# Initialize global rate limiter for sensitive endpoints
metrics_limiter = RateLimiter()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print("VALIDATION ERROR:", exc.errors())

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

class ChatRequest(BaseModel):
    user_id: Optional[str] = Field("anonymous", alias="userId")
    session_id: Optional[str] = Field(None, alias="sessionId")
    message: str = Field(..., alias="text")
    history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    persona_summary: Optional[str] = Field(None, alias="personaSummary")

    model_config = {
        "populate_by_name": True
    }

class SignupRequest(BaseModel):
    full_name: str
    email: str
    password: str
    admin_key: Optional[str] = None

    @field_validator('password')
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Mật khẩu phải có ít nhất 8 ký tự.')
        if len(v) > 128:
            raise ValueError('Mật khẩu không được dài quá 128 ký tự.')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Mật khẩu phải chứa ít nhất một chữ cái in hoa.')
        if not re.search(r'[a-z]', v):
            raise ValueError('Mật khẩu phải chứa ít nhất một chữ cái thường.')
        if not re.search(r'\d', v):
            raise ValueError('Mật khẩu phải chứa ít nhất một chữ số.')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Mật khẩu phải chứa ít nhất một ký tự đặc biệt.')
        return v

class LoginRequest(BaseModel):
    email: str
    password: str

class RenameSessionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)

class HandoffActionRequest(BaseModel):
    status: str # 'accepted' or 'busy'

class RagConfigRequest(BaseModel):
    interval_hours: int

class GoogleLoginRequest(BaseModel):
    token: str

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    dob: Optional[str] = None
    phone: Optional[str] = None
    gpa: Optional[float] = None
    test_scores: Optional[Dict[str, Any]] = None
    preferred_majors: Optional[List[str]] = None

class EmailLogRequest(BaseModel):
    user_id: str

class ConsultationClickRequest(BaseModel):
    user_id: Optional[str] = None
    source: Optional[str] = "report"

class AdminUserCreateRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: str = "user"
    permissions: Optional[List[str]] = None

class AdminRoleUpdateRequest(BaseModel):
    role: str

class AdminPermissionUpdateRequest(BaseModel):
    permission: str

class AdminBlacklistRequest(BaseModel):
    blacklisted: bool

class MatchRequest(BaseModel):
    user_id: str
    answers: Dict[str, Any]
    cv_text: Optional[str] = None
    cv_signals: Optional[Dict[str, Any]] = None

@app.get("/health")
async def health_check():
    """Confirm the service is live and reachable."""
    return {"status": "ok", "service": "vinuni-assistant-backend"}

@app.post("/api/chat")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Route free-form chat messages through the pipeline."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty")

    # Security: Override user_id from payload with the authenticated user's email
    user_id = current_user["email"]

    # Handle new session initialization
    session_id = request.session_id
    if not session_id or session_id == "new":
        session_id = str(uuid.uuid4())

    # Ensure the orchestrator result is wrapped in the structure 
    # expected by ConsultantPage.jsx (response.response)
    chat_response = pipeline.run_chat(
        user_id, 
        request.message, 
        request.history, 
        session_id=session_id,
        persona_summary=request.persona_summary
    )
    logger.info(f"Chat response {chat_response}")

    if isinstance(chat_response, dict):
        return {
            **chat_response,
            "sources": chat_response.get("sources", []),
            "session_id": session_id,
        }

    return {
        "response": chat_response,
        "sources": [],
        "session_id": session_id
    }

@app.get("/api/chat/sessions/{user_id}")
async def get_chat_sessions(user_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve all chat sessions for a specific user."""
    # Security check: Users can only see their own sessions unless they are an admin
    if current_user.get("role") != "admin" and current_user.get("email") != user_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem phiên chat của người dùng khác")

    sessions = pipeline.db_service.get_user_sessions(user_id)
    return {"status": "success", "sessions": sessions}

@app.get("/api/chat/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve message history for a specific session."""
    # 1. Verify session existence and ownership
    session = pipeline.db_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Phiên hội thoại không tồn tại")

    # 2. Security check
    is_admin = current_user.get("role") == "admin"
    is_owner = current_user.get("email") == session["user_id"]
    
    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập dữ liệu này")

    messages = pipeline.db_service.get_history(session["user_id"], session_id=session_id)
    return {"status": "success", "messages": messages}

@app.get("/api/chat/sessions/{session_id}/download")
async def download_chat_history(session_id: str, current_user: dict = Depends(get_current_user)):
    """Generate and stream a text file containing the chat history."""
    # 1. Verify session existence and ownership
    session = pipeline.db_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Phiên hội thoại không tồn tại")

    if current_user.get("role") != "admin" and current_user.get("email") != session["user_id"]:
        raise HTTPException(status_code=403, detail="Bạn không có quyền tải dữ liệu này")

    # 2. Fetch all messages for the session
    messages = pipeline.db_service.get_history(session["user_id"], session_id=session_id, limit=200)
    
    # 3. Format history as text
    output = io.StringIO()
    output.write(f"LỊCH SỬ TRÒ CHUYỆN - VINUNI ADMISSION ASSISTANT\n")
    output.write(f"Phiên: {session.get('title', 'Hội thoại mới')}\n")
    output.write(f"Ngày tạo: {session.get('created_at')}\n")
    output.write("="*50 + "\n\n")

    for msg in messages:
        role_label = "Học sinh" if msg["role"] == "user" else "Trợ lý VinUni"
        timestamp = f" [{msg['timestamp']}]" if msg.get("timestamp") else ""
        output.write(f"{role_label}{timestamp}:\n{msg['content']}\n")
        output.write("-" * 20 + "\n")

    # 4. Stream as file
    stream = io.BytesIO(output.getvalue().encode("utf-8"))
    filename = f"chat_history_{session_id[:8]}.txt"
    return StreamingResponse(stream, media_type="text/plain", headers={"Content-Disposition": f"attachment; filename={filename}"})

@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a specific chat session and its history."""
    # 1. Check if session exists and get owner info
    session = pipeline.db_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Phiên hội thoại không tồn tại")

    # 2. Security check: Only owner or admin can delete
    is_admin = current_user.get("role") == "admin"
    is_owner = current_user.get("email") == session["user_id"]
    
    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa phiên hội thoại này")

    pipeline.db_service.delete_session(session_id)
    return {"status": "success", "message": f"Đã xóa phiên hội thoại {session_id} thành công"}

@app.patch("/api/chat/sessions/{session_id}/rename")
async def rename_chat_session(
    session_id: str, 
    request: RenameSessionRequest, 
    current_user: dict = Depends(get_current_user)
):
    """Allow a user to manually rename a specific chat session."""
    # 1. Check if session exists
    session = pipeline.db_service.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Phiên hội thoại không tồn tại")

    # 2. Security check: Only owner or admin can rename
    if current_user.get("role") != "admin" and current_user.get("email") != session["user_id"]:
        raise HTTPException(status_code=403, detail="Bạn không có quyền đổi tên phiên hội thoại này")

    if pipeline.db_service.update_session_title(session_id, request.title):
        return {"status": "success", "message": "Đã đổi tên phiên hội thoại thành công"}
    raise HTTPException(status_code=500, detail="Không thể cập nhật tên phiên hội thoại")

@app.get("/api/handoff-summary")
async def get_handoff_summary(user_id: str, current_user: dict = Depends(staff_required)):
    """Retrieve a summary of the student profile and chat context for human handoff."""
    # Implementation fix: Building the handoff summary directly using CRM and DB services
    # as a fallback for the missing method in the Pipeline class.
    profile = pipeline.crm.get_profile(user_id) or {}
    history = pipeline.db_service.get_history(user_id, limit=6)
    
    if not profile and not history:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu bàn giao cho học sinh này")

    summary_parts = [
        f"=== BÁO CÁO BÀN GIAO NHÂN VIÊN TƯ VẤN ===",
        f"Học sinh: {user_id}",
        f"Ngày tạo: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "\n[1. THÔNG TIN HỒ SƠ]",
        f"- Họ tên: {profile.get('full_name', 'Chưa cập nhật')}",
        f"- Số điện thoại: {profile.get('phone', 'N/A')}",
        f"- GPA: {profile.get('gpa', 'Chưa có')}",
        f"- IELTS: {(profile.get('test_scores') or {}).get('ielts', 'N/A')}",
        f"- Ngành quan tâm: {', '.join(profile.get('preferred_majors') or []) if profile.get('preferred_majors') else 'Chưa xác định'}",
        "\n[2. DIỄN BIẾN HỘI THOẠI GẦN NHẤT]"
    ]

    if history:
        # Chronological order for context
        for msg in reversed(history):
            role = "Học sinh" if msg['role'] == 'user' else "AI Assistant"
            content = msg['content'][:300] + ("..." if len(msg['content']) > 300 else "")
            summary_parts.append(f"\n[{role}]:\n{content}")
    else:
        summary_parts.append("\n(Không có lịch sử trò chuyện được ghi lại)")

    return {"user_id": user_id, "handoff_summary": "\n".join(summary_parts)}

@app.get("/api/metrics")
async def get_metrics(hours: int = 336, current_user: dict = Depends(admin_required)):
    """Retrieve PMF-focused metrics over a requested time window."""
    # Rate limiting check to prevent abuse of compute-intensive metric aggregation
    if not metrics_limiter.allow(current_user["email"]):
        raise HTTPException(
            status_code=429, 
            detail="Yêu cầu quá thường xuyên. Vui lòng thử lại sau giây lát."
        )

    try:
        metric_service = MetricService(pipeline.db_service)
        return metric_service.get_pmf_metrics(hours_back=hours)
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail="Không thể tải dữ liệu thống kê")

def _coerce_audit_payload(payload: Any) -> Dict[str, Any]:
    """Parse audit payloads persisted as dicts, JSON strings, or Python repr strings."""
    if isinstance(payload, dict):
        return payload
    if not payload or not isinstance(payload, str):
        return {}

    try:
        parsed = json.loads(payload)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        pass

    try:
        parsed = ast.literal_eval(payload)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}

def _extract_top3_from_audit(log: Any) -> List[Dict[str, Any]]:
    payload = _coerce_audit_payload(log.output_data or log.output_text)
    top3 = payload.get("top3") or []
    return top3 if isinstance(top3, list) else []

@app.get("/api/admin/board")
async def get_admin_board(hours: int = 336, limit: int = 25, current_user: dict = Depends(admin_required)):
    """PRD-focused admin board: major demand, wizard completion, and consultation CTA clicks."""
    from models.schemas import AuditLog
    try:
        since_date = datetime.utcnow() - timedelta(hours=hours)
        with database.SessionLocal() as session:
            logs = session.query(AuditLog)\
                .filter(AuditLog.timestamp >= since_date)\
                .order_by(AuditLog.timestamp.desc())\
                .all()

            match_logs = [
                log for log in logs
                if log.route == "advisor" and _extract_top3_from_audit(log)
            ]
            fallback_logs = [
                log for log in logs
                if log.route in ("advisor", "fallback") and bool(log.fallback)
            ]
            consultation_logs = [log for log in logs if log.route == "consultation_cta"]

            major_counts = Counter()
            score_totals = defaultdict(float)
            appearances = Counter()
            major_names = {}

            for log in match_logs:
                for rank, major in enumerate(_extract_top3_from_audit(log), start=1):
                    major_id = major.get("major_id")
                    if not major_id:
                        continue
                    major_counts[major_id] += 4 - rank
                    appearances[major_id] += 1
                    score_totals[major_id] += float(major.get("match_score") or 0)
                    major_names[major_id] = major.get("major_name") or major_id

            top_majors = [{
                "major_id": major_id,
                "major_name": major_names.get(major_id, major_id),
                "weighted_count": int(weighted_count),
                "appearances": int(appearances[major_id]),
                "avg_score": round(score_totals[major_id] / appearances[major_id], 1) if appearances[major_id] else 0,
            } for major_id, weighted_count in major_counts.most_common()]

            recent_leads = [{
                "id": log.id,
                "user_id": log.user_id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "source": (_coerce_audit_payload(log.judge_result).get("source") if log.judge_result else None) or "report",
                "trace_id": log.trace_id,
            } for log in consultation_logs[:limit]]

            total_wizard_sessions = len(match_logs) + len(fallback_logs)
            return {
                "period_hours": hours,
                "total_wizard_sessions": total_wizard_sessions,
                "completed_matches": len(match_logs),
                "fallback_sessions": len(fallback_logs),
                "fallback_rate": round(len(fallback_logs) / total_wizard_sessions, 3) if total_wizard_sessions else 0,
                "consultation_clicks": len(consultation_logs),
                "top_majors": top_majors,
                "recent_consultation_leads": recent_leads,
                "generated_at": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Error fetching admin board: {e}")
        raise HTTPException(status_code=500, detail="KhÃ´ng thá»ƒ táº£i dá»¯ liá»‡u admin board")

@app.get("/api/admin/audit-logs")
async def get_audit_logs(
    user_id: Optional[str] = None,
    only_fallback: bool = False,
    limit: int = 100,
    offset: int = 0,
    hours: int = 336,
    current_user: dict = Depends(staff_required)
):
    """Retrieve the most recent system activity logs for administrative review."""
    from models.schemas import AuditLog
    from sqlalchemy import or_
    try:
        session_factory = getattr(database, "SessionLocal", None)
        if session_factory is None:
            raise RuntimeError("Database session factory is not initialized.")
            
        with session_factory() as session:
            query = session.query(AuditLog).filter(AuditLog.timestamp >= datetime.utcnow() - timedelta(hours=hours))
            if user_id:
                query = query.filter(or_(
                    AuditLog.user_id.ilike(f"%{user_id}%"),
                    AuditLog.trace_id.ilike(f"%{user_id}%")
                ))
            if only_fallback:
                query = query.filter(or_(AuditLog.ai_resolved == False, AuditLog.fallback == True))
            total = query.count()
            logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
            return {"logs": [{
                "id": log.id,
                "user_id": log.user_id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "route": log.route,
                "input": log.input_data,
                "output": log.output_data,
                "latency": log.response_time_ms,
                "judge_result": log.judge_result,
                "trace_id": log.trace_id,
                "escalation_level": log.escalation_level,
                "escalation_reason": log.escalation_reason,
                "handoff_status": log.handoff_status,
                "ai_resolved": log.ai_resolved,
                "fallback": log.fallback
            } for log in logs], "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        raise HTTPException(status_code=500, detail="Không thể tải nhật ký hệ thống")

@app.get("/api/admin/pending-handoffs")
async def get_pending_handoffs(current_user: dict = Depends(admin_required)):
    """Lấy danh sách các yêu cầu đang chờ người tư vấn chấp nhận."""
    from models.schemas import AuditLog
    try:
        with database.SessionLocal() as session:
            logs = session.query(AuditLog).filter(
                AuditLog.handoff_status == 'pending'
            ).order_by(AuditLog.timestamp.desc()).all()
            
            return [{
                "trace_id": log.trace_id,
                "user_id": log.user_id,
                "input": log.input_data,
                "escalation_level": log.escalation_level,
                "escalation_reason": log.escalation_reason,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None
            } for log in logs]
    except Exception as e:
        logger.error(f"Error fetching pending handoffs: {e}")
        return []

@app.post("/api/admin/handoff/{trace_id}")
async def handle_handoff(trace_id: str, request: HandoffActionRequest, current_user: dict = Depends(admin_required)):
    """Chấp nhận hoặc từ chối yêu cầu tư vấn dựa trên trace_id."""
    from models.schemas import AuditLog
    try:
        with database.SessionLocal() as session:
            log = session.query(AuditLog).filter(AuditLog.trace_id == trace_id).first()
            if not log:
                raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")
            
            log.handoff_status = request.status
            session.commit()
            return {"status": "success"}
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Error updating handoff status: {e}")
        raise HTTPException(status_code=500, detail="Lỗi khi cập nhật trạng thái")

@app.post("/api/audit/email-sent")
async def log_email_action(request: EmailLogRequest, current_user: dict = Depends(staff_required)):
    """Explicitly logs when a counselor/staff initiates an email to a student."""
    try:
        pipeline.db_service.save_audit_log(
            user_id=current_user["email"],
            input_data=f"STAFF_ACTION: Opened email client for student {request.user_id}",
            output_data="Action: mailto client triggered",
            judge_result={"action": "email_initiated", "target_student": request.user_id},
            route="staff_action",
            ai_resolved=True,
            fallback=False
        )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to log email action: {e}")
        raise HTTPException(status_code=500, detail="Lỗi khi ghi nhật ký hoạt động")

@app.post("/api/audit/consultation-click")
async def log_consultation_click(request: ConsultationClickRequest, current_user: dict = Depends(get_current_user)):
    """Log the PRD consultation CTA so Admin Board can show interested students."""
    try:
        pipeline.db_service.save_audit_log(
            user_id=current_user["email"],
            input_data=f"USER_ACTION: Consultation CTA clicked from {request.source or 'report'}",
            output_data="Action: consultation request intent captured",
            judge_result={"action": "consultation_click", "source": request.source or "report"},
            route="consultation_cta",
            ai_resolved=True,
            fallback=False
        )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to log consultation click: {e}")
        raise HTTPException(status_code=500, detail="Lá»—i khi ghi nháº­t kÃ½ yÃªu cáº§u tÆ° váº¥n")

@app.post("/api/auth/signup")
async def signup(request: SignupRequest):
    """Handle student registration."""
    # 1. Kiểm tra người dùng tồn tại
    existing_user = pipeline.db_service.get_student_profile(request.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký.")

    try:
        # Determine role based on email domain or provided secret admin key
        admin_signup_key = os.getenv("ADMIN_SIGNUP_KEY", "dev-admin-key")
        is_admin_key_valid = request.admin_key == admin_signup_key if request.admin_key else False
        
        role = "admin" if (request.email.endswith("@vinuni.edu.vn") or is_admin_key_valid) else "user"

        user_data = {
            "full_name": request.full_name,
            "email": request.email,
            "password": request.password,
            "role": role
        }
        # Use email as the internal user_id for consistency across login/signup
        pipeline.db_service.upsert_student_profile(request.email, user_data)
        
        return {"status": "success", "message": "Đăng ký thành công!"}
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Lỗi khi tạo tài khoản.")

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Verify credentials and return access token."""
    # Offload verification to Database SQL functions
    user = pipeline.db_service.authenticate_user(request.email, request.password)

    if not user:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")

    # 2. Tạo JWT token thực tế
    role = user.get("role", "user")
    db_permissions = user.get("permissions") or []
    token = create_access_token({"sub": request.email, "role": role, "permissions": db_permissions})
    
    all_permissions = list(set(ROLE_PERMISSIONS.get(role, []) + db_permissions))

    return {
        "status": "success", 
        "token": token, 
        "user_email": request.email, 
        "role": role,
        "permissions": all_permissions
    }

@app.post("/api/auth/google")
async def google_auth(request: GoogleLoginRequest):
    """Verify Google ID Token and return application session."""
    try:
        # Verify the token against Google's servers
        id_info = id_token.verify_oauth2_token(
            request.token, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )

        # Extract user info
        email = id_info.get('email')
        full_name = id_info.get('name')
        picture = id_info.get('picture') # URL ảnh đại diện từ Google
        
        if not email:
            raise HTTPException(status_code=400, detail="Token không chứa email")

        # Fetch existing user to include persisted permissions
        user = pipeline.db_service.get_student_profile(email)
        if user and user.get("blacklisted"):
            raise HTTPException(status_code=403, detail="TÃ i khoáº£n nÃ y Ä‘Ã£ bá»‹ khá»‘a trong há»‡ thá»‘ng.")
        db_permissions = user.get("permissions") or [] if user else []

        # Logic phân quyền tương tự login thường
        role = user.get("role") if user else ("admin" if email.endswith("@vinuni.edu.vn") else "user")
        
        app_token = create_access_token({"sub": email, "role": role, "permissions": db_permissions})
        
        all_permissions = list(set(ROLE_PERMISSIONS.get(role, []) + db_permissions))

        return {
            "status": "success", 
            "token": app_token, 
            "user_email": email, 
            "role": role, 
            "permissions": all_permissions,
            "full_name": full_name,
            "picture": picture
        }

    except ValueError as e:
        logger.error(f"Google Token validation failed: {e}")
        raise HTTPException(status_code=401, detail="Token Google không hợp lệ")

@app.post("/api/match")
async def match(request: MatchRequest, current_user: dict = Depends(get_current_user)):
    """Submit wizard answers for major matching recommendations."""
    # Security hardening: Use the authenticated user's ID from the token
    authenticated_user_id = current_user["email"]

    # 1. Generate the major matching results via Advisor Agent
    results = pipeline.run_match(authenticated_user_id, request.answers, request.cv_text, request.cv_signals)
    
    # 2. Persist to SQL DB for CRM Agent and Profile Page
    try:
        # Persist wizard answers and the latest matched majors for advisor/admin views.
        profile_update = request.answers.copy()
        if results.get("top3"):
            profile_update["preferred_majors"] = [
                item.get("major_id") for item in results["top3"] if item.get("major_id")
            ]
        pipeline.db_service.upsert_student_profile(authenticated_user_id, profile_update)
        logger.info(f"Student profile persisted to SQL for: {authenticated_user_id}")
    except Exception as e:
        logger.error(f"Failed to persist student profile to SQL: {e}")

    # 3. Store the survey answers as context for the RAG service (Vector DB)
    try:
        summary_parts = ["Student Profile and Preferences:"]
        for category, selection in request.answers.items():
            if selection:
                # Format list values (like interests) or strings (like work style)
                val_str = ", ".join(selection) if isinstance(selection, list) else str(selection)
                summary_parts.append(f"- {category.replace('_', ' ').capitalize()}: {val_str}")
        
        context_text = "\n".join(summary_parts)
        pipeline.rag.rag_service.ingest_cv(sanitize_id(authenticated_user_id), context_text)
        logger.info(f"Wizard answers indexed for user context: {authenticated_user_id}")
    except Exception as e:
        logger.error(f"Failed to ingest wizard answers for user {authenticated_user_id}: {e}")
        
    return results

@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str, current_user: dict = Depends(get_current_user)):
    """Retrieve the structured student profile as managed by the CRM agent."""
    # Bảo mật: Cho phép staff xem mọi profile, hoặc user tự xem profile của chính mình
    if current_user.get("role") not in ["admin", "editor"] and current_user.get("email") != user_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem hồ sơ này")

    profile = pipeline.crm.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.post("/api/profile/{user_id}")
async def update_profile(user_id: str, request: ProfileUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Update student profile information."""
    # Bảo mật: Cho phép staff cập nhật mọi profile, hoặc user tự cập nhật profile của chính mình
    if current_user.get("role") not in ["admin", "editor"] and current_user.get("email") != user_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật hồ sơ này")

    try:
        # Chuyển đổi dữ liệu request thành dict để cập nhật vào DB
        update_data = request.model_dump(exclude_unset=True)
        
        # Sử dụng db_service để cập nhật thông tin (giả định upsert hỗ trợ các trường này)
        pipeline.db_service.upsert_student_profile(user_id, update_data)
        
        logger.info(f"Profile updated for user: {user_id}")
        return {"status": "success", "message": "Thông tin hồ sơ đã được cập nhật"}
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")
        raise HTTPException(status_code=500, detail="Không thể cập nhật hồ sơ")

@app.get("/api/system/db-status")
async def get_db_status(admin: dict = Depends(admin_required)):
    """Admin-only endpoint to check database statistics."""
    db_info = database.get_database_info()
    user_counts = {"total": 0, "admin": 0, "editor": 0, "user": 0, "blacklisted": 0}
    try:
        from models.schemas import User
        from sqlalchemy import func
        with database.SessionLocal() as session:
            user_counts["total"] = session.query(User).count()
            for role, count in session.query(User.role, func.count(User.user_id)).group_by(User.role).all():
                user_counts[role or "user"] = int(count or 0)
            user_counts["blacklisted"] = session.query(User).filter(User.blacklisted == True).count()
    except Exception as e:
        logger.warning(f"Could not fetch DB user counts: {e}")
    return {
        "status": "connected" if db_info["connected"] else "disconnected",
        "database": db_info["name"],
        "type": db_info["type"],
        "tables": ["users", "students", "chat_messages", "majors"],
        "user_counts": user_counts,
        "accessed_by": admin["email"]
    }

def _validate_admin_role(role: str) -> str:
    if role not in {"admin", "editor", "user"}:
        raise HTTPException(status_code=400, detail="Role khÃ´ng há»£p lá»‡. Chá»‰ há»— trá»£ admin, editor, user.")
    return role

def _normalize_permission(permission: str) -> str:
    permission = (permission or "").strip()
    if not permission:
        raise HTTPException(status_code=400, detail="Permission khÃ´ng Ä‘Æ°á»£c Ä‘á»ƒ trá»‘ng.")
    return permission

@app.get("/api/admin/users")
async def list_admin_users(admin: dict = Depends(admin_required)):
    """List users stored in PostgreSQL for admin database management."""
    users = pipeline.db_service.get_all_users()
    users.sort(key=lambda u: (u.get("role") != "admin", u.get("email") or u.get("user_id") or ""))
    return {"status": "success", "count": len(users), "users": users}

@app.post("/api/admin/users")
async def create_admin_user(request: AdminUserCreateRequest, admin: dict = Depends(admin_required)):
    """Create or update a user account directly from the database admin page."""
    role = _validate_admin_role(request.role)
    try:
        pipeline.db_service.upsert_student_profile(request.email, {
            "email": request.email,
            "full_name": request.full_name or request.email,
            "password": request.password,
            "role": role,
            "permissions": request.permissions or []
        })
        pipeline.db_service.save_audit_log(
            user_id=admin["email"],
            input_data=f"ADMIN_DB_ACTION: created_or_updated_user {request.email}",
            output_data=f"role={role}",
            judge_result={"action": "admin_user_upsert", "target": request.email, "role": role},
            route="admin_internal",
            ai_resolved=True,
            fallback=False
        )
        return {"status": "success", "message": f"ÄÃ£ táº¡o/cáº­p nháº­t {role}: {request.email}"}
    except Exception as e:
        logger.error(f"Admin create user failed: {e}")
        raise HTTPException(status_code=500, detail="KhÃ´ng thá»ƒ táº¡o/cáº­p nháº­t user")

@app.patch("/api/admin/users/{user_id}/role")
async def update_admin_user_role(user_id: str, request: AdminRoleUpdateRequest, admin: dict = Depends(admin_required)):
    role = _validate_admin_role(request.role)
    try:
        pipeline.db_service.upsert_student_profile(user_id, {"role": role})
        return {"status": "success", "user_id": user_id, "role": role}
    except Exception as e:
        logger.error(f"Admin role update failed: {e}")
        raise HTTPException(status_code=500, detail="KhÃ´ng thá»ƒ cáº­p nháº­t role")

@app.post("/api/admin/users/{user_id}/permissions/grant")
async def grant_admin_user_permission(user_id: str, request: AdminPermissionUpdateRequest, admin: dict = Depends(admin_required)):
    permission = _normalize_permission(request.permission)
    profile = pipeline.db_service.get_student_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="KhÃ´ng tÃ¬m tháº¥y user")
    permissions = list(dict.fromkeys((profile.get("permissions") or []) + [permission]))
    pipeline.db_service.upsert_student_profile(user_id, {"permissions": permissions})
    return {"status": "success", "user_id": user_id, "permissions": permissions}

@app.post("/api/admin/users/{user_id}/permissions/revoke")
async def revoke_admin_user_permission(user_id: str, request: AdminPermissionUpdateRequest, admin: dict = Depends(admin_required)):
    permission = _normalize_permission(request.permission)
    profile = pipeline.db_service.get_student_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="KhÃ´ng tÃ¬m tháº¥y user")
    permissions = [p for p in (profile.get("permissions") or []) if p != permission]
    pipeline.db_service.upsert_student_profile(user_id, {"permissions": permissions})
    return {"status": "success", "user_id": user_id, "permissions": permissions}

@app.patch("/api/admin/users/{user_id}/blacklist")
async def update_admin_user_blacklist(user_id: str, request: AdminBlacklistRequest, admin: dict = Depends(admin_required)):
    if user_id == admin["email"] and request.blacklisted:
        raise HTTPException(status_code=400, detail="KhÃ´ng thá»ƒ blacklist chÃ­nh tÃ i khoáº£n admin Ä‘ang Ä‘Äƒng nháº­p.")
    profile = pipeline.db_service.get_student_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="KhÃ´ng tÃ¬m tháº¥y user")
    pipeline.db_service.upsert_student_profile(user_id, {"blacklisted": request.blacklisted})
    return {"status": "success", "user_id": user_id, "blacklisted": request.blacklisted}

@app.post("/api/admin/rag-sync")
async def manual_rag_sync(admin: dict = Depends(admin_required)):
    """Admin-only endpoint to manually trigger RAG data ingestion/sync."""
    try:
        logger.info(f"Manual RAG sync triggered by admin: {admin['email']}")
        # Call the sync method on the RAG service via the pipeline
        sync_report = pipeline.rag.rag_service.sync_all()
        logger.info(f"Manual RAG sync report: {sync_report}")
        return {"status": "success", "message": "RAG data synchronization completed successfully.", "report": sync_report}
    except Exception as e:
        logger.error(f"Manual RAG sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"RAG sync failed: {str(e)}")

@app.get("/api/admin/rag/ingest/stream")
async def rag_ingest_stream(admin: dict = Depends(admin_required)):
    """Stream real-time ingestion progress using SSE."""
    def event_generator():
        try:
            for update in pipeline.rag.rag_service.sync_all_streaming():
                # SSE format: data: <content>\n\n
                yield f"data: {json.dumps(update)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/admin/rag/status")
async def get_rag_status(admin: dict = Depends(admin_required)):
    """Admin-only endpoint to get detailed RAG health and collection stats."""
    from config import USE_MOCK
    try:
        rs = pipeline.rag.rag_service
        
        # 1. Get collection counts
        collections = {
            "admissions": rs.admission_collection.count() if not USE_MOCK else 12,
            "faq": rs.faq_collection.count() if not USE_MOCK else 25,
            "cvs": len(rs.cv_collections) # Count of user-specific collections
        }
        
        # 2. Fetch latency performance from logs
        from models.schemas import AuditLog
        from sqlalchemy import func
        
        avg_total = 0
        with database.SessionLocal() as session:
            avg_total = session.query(func.avg(AuditLog.response_time_ms))\
                .filter(AuditLog.route == 'rag').scalar() or 0

        return {
            "status": "active",
            "db_status": "connected",
            "model_status": "active",
            "sync_interval_hours": rag_config["sync_interval_hours"],
            "collections": collections,
            "performance": {
                "avg_total": round(float(avg_total), 2),
                "avg_chroma": 150, # Estimated/Placeholder
                "avg_openai": round(float(avg_total) - 150, 2) if avg_total > 150 else 0
            },
            "last_sync": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to fetch RAG status: {e}")
        raise HTTPException(status_code=500, detail="Không thể lấy trạng thái hệ thống tri thức")

@app.post("/api/admin/rag/ingest")
async def rag_ingest_alias(admin: dict = Depends(admin_required)):
    """Alias for rag-sync to match frontend endpoint naming."""
    try:
        report = pipeline.rag.rag_service.sync_all()
        return {"status": "success", "report": report}
    except Exception as e:
        logger.error(f"RAG ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/rag/config")
async def update_rag_config(request: RagConfigRequest, admin: dict = Depends(admin_required)):
    """Update RAG synchronization settings."""
    try:
        rag_config["sync_interval_hours"] = request.interval_hours
        # In a real app, you would restart the background thread or update a scheduler
        logger.info(f"RAG sync interval updated to {request.interval_hours} hours")
        return {"status": "success", "config": rag_config}
    except Exception as e:
        logger.error(f"Failed to update RAG config: {e}")
        raise HTTPException(status_code=500, detail="Không thể cập nhật cấu hình RAG")

@app.get("/api/test-db/users")
async def get_all_users_test(admin: dict = Depends(admin_required)):
    """Admin-only test endpoint to verify registered users."""
    users = pipeline.db_service.get_all_users()
    return {"status": "success", "count": len(users), "users": users}

@app.get("/api/profile/{user_id}/cv")
async def download_profile_cv(user_id: str, current_user: dict = Depends(get_current_user)):
    """Return the saved CV PDF for profile review."""
    if current_user.get("role") not in ["admin", "editor"] and current_user.get("email") != user_id:
        raise HTTPException(status_code=403, detail="Báº¡n khÃ´ng cÃ³ quyá»n táº£i CV nÃ y")

    saved_path = os.path.join(os.path.dirname(__file__), "uploads", "cv", f"{sanitize_id(user_id)}.pdf")
    if not os.path.exists(saved_path):
        raise HTTPException(status_code=404, detail="CV chÆ°a Ä‘Æ°á»£c táº£i lÃªn")

    profile = pipeline.db_service.get_student_profile(user_id) or {}
    filename = profile.get("cv_filename") or "vinuni_cv.pdf"
    return FileResponse(saved_path, media_type="application/pdf", filename=filename)

@app.post("/api/upload-cv")
async def upload_cv(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload and index a PDF CV."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận tệp tin định dạng PDF.")

    try:
        user_id = current_user["email"] # Use the email from the authenticated user
        safe_user_id = sanitize_id(user_id)
        upload_dir = os.path.join(os.path.dirname(__file__), "uploads", "cv")
        os.makedirs(upload_dir, exist_ok=True)
        saved_path = os.path.join(upload_dir, f"{safe_user_id}.pdf")
        # Create a temporary file that is automatically deleted
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            text = extract_text_from_pdf(tmp_path)
            
            # EXTRACT CV SIGNALS: Extract structured attributes (majors, confidence, GPA)
            # to provide immediate feedback to the student and aid prompt context.
            cv_signals = {}
            if hasattr(pipeline, 'cv_agent') and pipeline.cv_agent:
                cv_signals = pipeline.cv_agent.analyze(text)

            pipeline.rag.rag_service.ingest_cv(sanitize_id(user_id), text)
            with open(saved_path, "wb") as saved_file:
                saved_file.write(content)
            pipeline.db_service.upsert_student_profile(user_id, {
                "cv_filename": file.filename,
                "cv_url": f"/api/profile/{user_id}/cv",
                "cv_uploaded_at": datetime.utcnow().isoformat(),
                "cv_signals": cv_signals
            })
        except Exception as e:
            logger.error(f"Failed to process PDF: {e}")
            raise HTTPException(status_code=400, detail="Tệp tin PDF không hợp lệ hoặc bị lỗi cấu trúc.")
        
        return {
            "status": "CV indexed successfully", 
            "filename": file.filename,
            "cv_url": f"/api/profile/{user_id}/cv",
            "cv_signals": cv_signals,
            "cv_text": text
        }
    finally:
        # Clean up the temp file after indexing
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
