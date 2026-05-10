2. Backend Services Report
Overview The backend is a high-performance FastAPI application centered around a multi-agent AI pipeline. It has been successfully transitioned from Google Gemini to OpenAI (GPT-4o-mini).

AI Intelligence & Retrieval

LLM Integration: Centrally managed by LLMClient, utilizing gpt-4o-mini for its balance of speed and cost-effectiveness.
Hybrid RAG Service:
Uses ChromaDB with three distinct collections: admissions (official docs), faq (common queries), and cv_{user_id} (personal context).
Implements Query Expansion to improve retrieval recall.
Employs a Learning-to-Rank (LTR) reranker using a Logistic Regression model to prioritize the most relevant chunks based on semantic similarity and source metadata.
Agent Orchestration:
LLMRouter: Classifies user intent into rag, crm, advisor, or fallback.
AdvisorAgent: Handles the complex logic of matching majors using a weighted formula (0.6 Wizard + 0.4 CV).
CRMAgent: Accesses the relational database to answer personalized questions about student profiles.
Safety & Infrastructure

Guardrail Pipeline: Every request passes through InputGuard (injection detection), RateLimiter, and OutputGuard (PII redaction/HTML sanitization).
Judge Agent: A final safety gate that evaluates generated responses against strict criteria before they are returned to the user.
Database: Dual-layer storage using PostgreSQL (via SQLAlchemy ORM) for structured user/profile data and ChromaDB for vector embeddings.