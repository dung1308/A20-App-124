"""
agents/rag.py
-------------
Responsibility: Handle Retrieval-Augmented Generation for free-form queries.
Enriches the context using user persona signals for more relevant answers.
"""

import re
from typing import List, Dict, Any, Optional
from services.rag_service import RAGService
from utils.logger import get_logger
import config

logger = get_logger(__name__)

class RAGAgent:
    def __init__(self):
        # Initializing the RAG service which handles vector search/retrieval
        self.rag_service = RAGService()

    def run(
        self, 
        message: str, 
        history: List[Dict[str, Any]], 
        user_id: str = None, 
        persona_summary: str = None,
        **kwargs
    ) -> str:
        """
        Executes the RAG flow: Retrieve -> Filter (using persona) -> Generate.
        """
        logger.info(f"RAGAgent: Processing query for {user_id}")

        # 1. Retrieve raw documents from the RAG Service
        # Passing user_id leverages user-specific context (e.g., their own CV/Wizard chunks)
        # Đảm bảo RAGService tìm cả ở global admissions và user context
        retrieved_docs = self.rag_service.retrieve(
            message, 
            user_id=user_id, 
            history=history
        )
        
        # 2. Filter/Re-rank retrieved documents based on persona_summary
        # This ensures we prioritize chunks relevant to the student's background.
        context_docs = self._filter_docs_by_persona(retrieved_docs, persona_summary)
        
        # 3. Construct Context for the LLM
        context_text = "\n\n".join(context_docs)
        
        # 4. Setup System Prompt with Persona Context
        system_prompt = (
            "Bạn là trợ lý tuyển sinh của VinUni. Hãy trả lời câu hỏi dựa trên ngữ cảnh được cung cấp.\n"
            "Nếu ngữ cảnh không chứa thông tin, hãy nói bạn không biết, đừng tự bịa câu trả lời.\n"
        )
        
        if persona_summary:
            system_prompt += f"\nThông tin về người học: {persona_summary}\n"
            system_prompt += "Hãy điều chỉnh câu trả lời để phù hợp với trình độ chuyên môn và lĩnh vực quan tâm của người học."

        # 5. Generate Response
        if config.USE_MOCK:
            # Simulate a grounded response for testing
            return f"[RAG MOCK] Dựa trên hồ sơ của bạn và tài liệu VinUni, tôi xin trả lời: {context_text[:150]}..."
            
        # In REAL mode, invoke your LLM client (e.g., Gemini or OpenAI)
        # return llm_client.generate(system_prompt, message, history, context_text)
        return "Câu trả lời từ RAG Agent dựa trên tài liệu tuyển sinh và hồ sơ cá nhân."

    def _filter_docs_by_persona(self, docs: List[str], persona: Optional[str]) -> List[str]:
        """
        Boosts documents that match keywords found in the persona summary to increase 
        relevance before passing to the LLM.
        """
        if not persona or not docs:
            return docs[:5]  # Default to top 5 hits from initial retrieval

        # Define priority keywords for major domains to aid re-ranking
        domain_keywords = {
            "Computer Science": ["khoa học máy tính", "lập trình", "phần mềm", "cs", "it", "thuật toán"],
            "Business Administration": ["quản trị", "kinh doanh", "marketing", "tài chính", "khởi nghiệp"],
            "Mechanical Engineering": ["kỹ thuật", "cơ khí", "chế tạo", "robot", "tự động hóa"],
        }
        
        active_keywords = []
        persona_lower = persona.lower()
        for domain, keywords in domain_keywords.items():
            if domain.lower() in persona_lower:
                active_keywords.extend(keywords)

        # Fallback: Extract significant terms from persona if no domain-specific match
        if not active_keywords:
            active_keywords = [w for w in re.findall(r'\w+', persona_lower) if len(w) > 4]

        if not active_keywords:
            return docs[:5]

        scored_docs = []
        for doc in docs:
            text = doc.lower()
            # Calculate a simple persona-relevance boost score
            # (Weighted +2 for every persona keyword match found in the doc)
            persona_boost = sum(2 for k in active_keywords if k in text)
            scored_docs.append((persona_boost, doc))

        # Sort primarily by persona boost, then by original retrieval order
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        return [item[1] for item in scored_docs[:5]]
