import time
import os
from openai import OpenAI
from utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate(self, prompt: str, max_retries=3, timeout=10):
        for attempt in range(max_retries):
            try:
                start = time.time()

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    timeout=timeout
                )

                latency = time.time() - start
                logger.info(f"LLM latency ({self.model}): {latency:.2f}s")

                if response and response.choices:
                    return response.choices[0].message.content.strip()

                return "I don't know"

            except Exception as e:
                logger.warning(f"LLM retry {attempt+1}: {e}")
                time.sleep(1)

        logger.error("LLM failed after retries")
        return "I don't know"