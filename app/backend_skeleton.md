backend/
  main.py (entry point)
  config.py (LLM initialization - hinge rule)
  orchestrator/
    router.py (intent classification)
    pipeline.py (main flow control)
  agents/
    advisor.py
    rag.py (Vector search retrieval)
    crm.py (PII masking and student data)
    judge.py
    cv_agent.py (convert CV data into signals)
  guards/
    input_guard.py
    output_guard.py
    rate_limiter.py
  middleware/
    admin_audit.py (Track staff/admin actions) (temporarily in guard/)
    observability.py (Step-level timing and tracing) (temporarily in utils/)
  services/
    rag_service.py (embedding + retrieval)
    db_service.py (PostgreSQL + migrate_db logic)
    cv_parser.py (extract structured data from CV)
    metric_service.py (compute PMF and performance metrics)
    pdf_loader.py (extract text from uploaded CVs)
  models/
    schemas.py (Pydantic models)
    cv_schema.py (define structured CV format)
  utils/
    logger.py
  scripts/
    reset_admin.py (CLI for user management)
    db_init.py (Initial setup and seed data)

Each file must contain a minimal working function + docstring explaining responsibility.