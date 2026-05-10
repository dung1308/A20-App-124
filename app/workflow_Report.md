3. Workflow & Operational Report
The AI Execution Lifecycle

Ingestion: Documents are chunked using semantic boundaries and embedded using text-embedding-3-small.
Request Flow:
The Pipeline coordinates a 5-step process: Guarding -> Routing -> Agent Execution -> Redaction -> Judging.
Traceability: Every request is assigned a unique trace_id. The ObservabilityMiddleware captures detailed step-level timings (e.g., how long the reranker took vs. the LLM generation) and emits a single structured trace log.
Development & Optimization Workflow

Mock Mode: The USE_MOCK environment flag allows developers to work on the UI and pipeline logic without incurring OpenAI API costs, using deterministic keyword-based routing and simulated responses.
Training Loop: The gen_data.py script enables the generation of training data from real retrieval results, which is then used by the LearningToRank class to improve the accuracy of the reranker over time.
Budgeting: The CostController tracks token usage in real-time using tiktoken, enforcing daily global and per-user USD budgets to prevent runaway costs.
Compliance & Auditing

Audit Logging: The system records every interaction, including the input, redacted output, and the JudgeAgent decision, ensuring a complete compliance trail for university administrators.