
"""
config.py
---------
Centralized LLM + environment config (OpenAI v1+ compatible)
"""

import os
import logging
from functools import lru_cache
from dotenv import load_dotenv

from openai import OpenAI  # ✅ NEW API

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "sqlite:///./vinuni_match.db"
)
USE_MOCK: bool = os.getenv("USE_MOCK", "True").lower() == "true"
REDIS_URL: str | None = os.getenv("REDIS_URL")
HUMAN_WEBHOOK: str = os.getenv("HUMAN_WEBHOOK", "http://localhost:9000/handoff")
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

def get_database_url() -> str:
    return DATABASE_URL

RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "10"))
RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
DAILY_LLM_BUDGET: float = float(os.getenv("DAILY_LLM_BUDGET", "100"))

if not OPENAI_API_KEY and not USE_MOCK:
    logger.warning("OPENAI_API_KEY not set — LLM calls will fail.")

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------------------------------------------------------
# Mock model (unchanged)
# ---------------------------------------------------------------------------

class MockOpenAIModel:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate_content(self, prompt: str, **kwargs):
        text = "Đây là phản hồi giả lập từ hệ thống VinUni Major Matcher."
        if "top3" in prompt:
            text = '{"top3": [{"major_id": "cs", "match_reason": "Dựa trên sở thích công nghệ.", "match_score": 95}], "fallback": false}'
        elif "intent" in prompt:
            text = '{"intent": "INFO_QUERY", "confidence": 1.0}'

        class MockResponse:
            def __init__(self, t):
                self.text = t

        return MockResponse(text)

# ---------------------------------------------------------------------------
# OpenAI client factory (FIXED)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_openai_model(model_name: str = "gpt-4o-mini"):
    """
    Return a cached OpenAI model wrapper (v1 API).
    """

    if USE_MOCK:
        logger.info(f"[MOCK] Using MockOpenAIModel: {model_name}")
        return MockOpenAIModel(model_name)

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required when USE_MOCK=False")

    client = OpenAI(api_key=OPENAI_API_KEY)  # ✅ NEW CLIENT

    class OpenAIChatModel:
        def __init__(self, client, model_name):
            self.client = client
            self.model_name = model_name

        def generate_content(self, prompt: str, **kwargs):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                    max_tokens=256,
                )

                text = response.choices[0].message.content

                class Resp:
                    def __init__(self, t):
                        self.text = t

                return Resp(text)

            except Exception as e:
                logger.exception("LLM call failed")
                raise e

    return OpenAIChatModel(client, model_name)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_database_url() -> str:
    return DATABASE_URL

# ---------------------------------------------------------------------------
# Embedding (optional upgrade)
# ---------------------------------------------------------------------------

EMBEDDING_MODEL = "text-embedding-3-small"

def embed_text(text: str):
    """
    Optional: OpenAI embedding v1 API
    """
    if USE_MOCK:
        return [0.0] * 10
    # Reuse the global client

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )

    return response.data[0].embedding
