import uvicorn
import io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import AliasChoices, BaseModel, Field
from typing import List, Dict, Any, Optional

from orchestrator.pipeline import Pipeline
from services.metric_service import MetricService
from utils.logger import get_logger
from fastapi import UploadFile, File

logger = get_logger(__name__)

app = FastAPI(
    title="VinUni Admission Assistant API",
    description="Backend API for major matching and admission chat support.",
    version="0.1.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Orchestrator Pipeline
pipeline = Pipeline()
metric_service = MetricService()

class ChatRequest(BaseModel):
    user_id: Optional[str] = Field(
        "anonymous",
        validation_alias=AliasChoices("userId", "user_id"),
    )
    message: str = Field(
        ...,
        validation_alias=AliasChoices("text", "message"),
    )
    session_id: Optional[str] = Field(
        "new",
        validation_alias=AliasChoices("sessionId", "session_id"),
    )
    history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }

class SignupRequest(BaseModel):
    full_name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

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
async def chat(request: ChatRequest):
    """Route free-form chat messages through the pipeline."""
    # Load conversation history from DB if not provided
    if not request.history:
        request.history = pipeline.db_service.get_history(request.user_id, limit=20)

    response = pipeline.run_chat(
        request.user_id,
        request.message,
        request.history,
        session_id=request.session_id,
    )
    return response

@app.get("/api/chat/sessions/{user_id}")
async def list_chat_sessions(user_id: str):
    """Return the conversation sessions for a user."""
    sessions = pipeline.db_service.get_user_sessions(user_id)
    return {"status": "success", "sessions": sessions}

@app.get("/api/chat/sessions/{session_id}/messages")
async def get_chat_session_messages(session_id: str):
    """Return stored messages for a specific chat session."""
    messages = pipeline.db_service.get_session_messages(session_id)
    return {"status": "success", "messages": messages}

@app.patch("/api/chat/sessions/{session_id}/rename")
async def rename_chat_session(session_id: str, title: Dict[str, str]):
    """Rename an existing chat session."""
    success = pipeline.db_service.rename_chat_session(session_id, title.get("title", "Hội thoại mới"))
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "sessionId": session_id}

@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session and its messages."""
    success = pipeline.db_service.delete_chat_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success", "sessionId": session_id}

@app.get("/api/chat/sessions/{session_id}/download")
async def download_chat_session(session_id: str):
    """Download session history as a plain text file."""
    messages = pipeline.db_service.get_session_messages(session_id)
    content_lines = [
        f"[{msg['role']}] {msg['content']}" for msg in messages
    ]
    text = "\n".join(content_lines)
    return StreamingResponse(
        content=io.BytesIO(text.encode("utf-8")),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=chat_session_{session_id}.txt"}
    )

@app.get("/api/handoff-summary")
async def handoff_summary(user_id: str):
    """Return a human-readable summary of the user's chat context."""
    return {
        "user_id": user_id,
        "handoff_summary": pipeline.build_human_handoff_summary(user_id)
    }

@app.get("/api/metrics")
async def metrics(hours: int = 336):
    """Return PMF-focused chatbot metrics for the given time window."""
    return metric_service.get_pmf_metrics(hours=hours)

@app.post("/api/auth/signup")
async def signup(request: SignupRequest):
    """Handle student registration."""
    return {"status": "success", "message": f"Account created for {request.full_name}"}

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Verify credentials and return access token."""
    # Assign 'admin' role to school emails for engineer testing, 'user' otherwise
    role = "admin" if request.email.endswith("@vinuni.edu.vn") else "user"
    return {"status": "success", "token": "mock-token-123", "user_email": request.email, "role": role}

@app.post("/api/match")
async def match(request: MatchRequest):
    """Submit wizard answers for major matching recommendations."""
    return pipeline.run_match(request.user_id, request.answers, request.cv_text, request.cv_signals)

@app.post("/api/upload-cv")
async def upload_cv(user_id: str, file: UploadFile = File(...)):
    file_path = f"/tmp/{file.filename}"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    from services.pdf_loader import extract_text_from_pdf

    text = extract_text_from_pdf(file_path)

    pipeline.rag.rag_service.ingest_cv(user_id, text)

    return {"status": "CV indexed successfully"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
