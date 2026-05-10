import uuid
from datetime import datetime
from typing import List

from config import embed_text
from utils.logger import get_logger

logger = get_logger(__name__)


class LongTermMemory:

    def __init__(self, collection):
        self.collection = collection

    def save_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "general",
        importance: float = 0.5,
    ):

        try:
            emb = embed_text(content)

            self.collection.add(
                ids=[str(uuid.uuid4())],
                documents=[content],
                embeddings=[emb],
                metadatas=[{
                    "user_id": user_id,
                    "memory_type": memory_type,
                    "importance": importance,
                    "created_at": str(datetime.utcnow())
                }]
            )

        except Exception as e:
            logger.error(f"save_memory failed: {e}")

    def retrieve_memories(
        self,
        user_id: str,
        query: str,
        top_k: int = 3
    ) -> List[str]:

        try:
            emb = embed_text(query)

            results = self.collection.query(
                query_embeddings=[emb],
                n_results=top_k,
                where={"user_id": user_id}
            )

            return results.get("documents", [[]])[0]

        except Exception as e:
            logger.error(f"retrieve_memories failed: {e}")
            return []