"""
config.py
---------
Responsibility: Centralized LLM and environment configuration.
HINGE RULE: This is the ONLY file that imports google.generativeai or
initialises any LLM client. All agents call get_gemini_model() from here.
Swapping LLM providers = edit this one file only.
"""

import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
DATABASE_URL: str = os.getenv("DATABASE_URL", "") # Initialize as empty string, actual value from get_database_url
USE_MOCK: bool = os.getenv("USE_MOCK", "True").lower() == "true"
REDIS_URL: str | None = os.getenv("REDIS_URL")
HUMAN_WEBHOOK: str = os.getenv("HUMAN_WEBHOOK", "http://localhost:9000/handoff")
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "10"))
RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
DAILY_LLM_BUDGET: float = float(os.getenv("DAILY_LLM_BUDGET", "100"))

# Security settings
SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

if not OPENAI_API_KEY and not USE_MOCK:
    logger.warning("OPENAI_API_KEY not set — LLM calls will fail at runtime.")

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


# ---------------------------------------------------------------------------
# LLM client factory (hinge rule)
# ---------------------------------------------------------------------------

class MockGenerativeModel:
    """
    A mock object that mimics the interface of google.generativeai.GenerativeModel.
    Used when USE_MOCK=True to avoid external API calls.
    """
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate_content(self, prompt: str, **kwargs):
        """
        Returns a simulated response based on detected prompt keywords to ensure 
        JSON parsers in agents don't break.
        """
        text = "Đây là phản hồi giả lập từ hệ thống VinUni Major Matcher."
        
        # Detect agent-specific intents for structured JSON responses
        if "top3" in prompt: # AdvisorAgent
            text = '{"top3": [{"major_id": "cs", "match_reason": "Dựa trên sở thích công nghệ và logic của bạn.", "match_score": 95}], "fallback": false}'
        elif "suggested_majors" in prompt: # CVAgent
            text = '{"suggested_majors": ["cs", "ba"], "confidence": 0.9, "evidence": ["Hồ sơ có thế mạnh về lập trình."]}'
        elif "pass" in prompt: # JudgeAgent
            text = '{"pass": true, "reason": "Nội dung an toàn và phù hợp.", "score": 100}'
        elif "summary" in prompt and "education" in prompt: # CVParser
            text = '{"summary": "Sinh viên tiềm năng.", "education": [], "experience": [], "skills": ["Python", "AI"], "projects": [], "achievements": []}'
        elif "intent" in prompt: # LLMRouter.classify_intent
            text = '{"intent": "INFO_QUERY", "confidence": 1.0}'
        elif "rag, crm, advisor, fallback" in prompt: # LLMRouter.route
            text = "rag"

        class MockResponse:
            def __init__(self, t):
                self.text = t
        
        return MockResponse(text)

def get_database_url() -> str:
    """
    Return the current database URL from environment variables.
    Always reads from os.getenv to ensure the most recent value is retrieved.
    """
    url = os.getenv("DATABASE_URL", "sqlite:///./vinuni_match.db") # Direct fallback here
    
    if not USE_MOCK and url.startswith("sqlite"):
        logger.warning("Application is NOT in MOCK mode but is falling back to SQLite. Check your .env file.")
        
    return url

def embed_text(text: str):
    if USE_MOCK:
        return None

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding
