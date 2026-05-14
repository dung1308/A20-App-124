# 14/05/2026 Summary

This summary compiles the work completed on the VinUni Major Match app and the guide updates made during 14/05/2026.

## Product Scope Completed

- Strengthened the student profile flow so users can review CV-derived information before it becomes profile data.
- Added visible Profile sections for Summary, Career goals, Skills, Education, and Experience.
- Added CV document version support so uploaded PDFs can be saved, reviewed again, confirmed, or deleted from Profile.
- Connected Wizard and recommendation flows to `cv_document_id`, allowing the system to use the correct uploaded CV version.
- Improved RAG/profile context usage so recommendations and chat can use structured profile and CV information.
- Added Resources guidance so users have a clearer place to learn how to use the product.

## Backend Work Completed

- Added OCR-capable CV parsing support with embedded PDF text extraction and image/OCR fallback.
- Added structured CV parsing output, parse metadata, profile signals, and compatibility wrapper `CVParser`.
- Added CV document storage and APIs for upload, list, confirm, delete, and profile merge workflows.
- Added CV merge preview API so the frontend can show add/update/keep/skip changes before confirmation.
- Updated matching endpoints to accept `cv_document_id`.
- Added token usage admin API with filters and estimated usage derived from audit logs.
- Added prompt versioning APIs for creating/updating named versions, comparing rendered outputs, and selecting active prompts.
- Added staff human fallback workflow APIs for pending handoff jobs, accept/busy state, and staff replies.
- Added pain-point APIs for Profile readiness, contextual Resources, handoff status, and admin system health badges.
- Added structured response fields for `fallback_card`, `recovery_actions`, `decision_trace`, source labels, and recommendation `match_breakdown`.
- Updated backend data flow and Railway deployment notes for OCR/Tesseract requirements.

## Frontend Work Completed

- Added Profile fields for Summary, Career goals, Skills, Education, and Experience.
- Added CV document version controls on Profile, including confirm/delete actions and PDF review.
- Added Profile readiness UI and CV merge preview UI before confirming extracted CV data.
- Added CV upload review/edit flow before profile merge.
- Updated Wizard state to retain and submit `cv_document_id`.
- Added `/system/tokens` with filters, KPIs, usage records, and frequency graph.
- Improved `/system/database` prompt versioning with add/update forms, agent selection, compare controls, and active prompt selection.
- Added admin health badges for database, token usage, prompt versions, pending handoffs, and RAG ingest status.
- Added Resources page and sidebar entry.
- Added contextual Resources content and next-best actions based on Profile/Wizard/CV readiness.
- Reworked Report page with summary metrics, fallback handling, contextual actions, and local recovery.
- Updated Report cards to show matched signals, tradeoffs, evidence labels, and "Ask about this major" actions.
- Updated Chat to send report/UI context, show fallback cards, recovery actions, suggested resources, source labels, and handoff status.
- Reworked Staff dashboard for human fallback queues, session review, accept flow, and reply handling.
- Added chat polling so users can receive human advisor/editor replies.
- Fixed low-contrast white secondary buttons so labels/icons remain visible on white or light backgrounds.

## Admin And Operations

- Admin can inspect token usage by user/date/source and view frequency trends.
- Admin can manage prompt versions by agent, compare outputs, and select the active prompt.
- Staff/admin/editor users can handle human fallback jobs from the staff page.
- RAG administration wording was clarified so admins can distinguish scheduled ingestion from immediate ingestion.
- PMF/reporting guidance was expanded with graph filters and churn-rate metrics.

## Documentation Updated

- `app/guide/PRD.md`
- `app/guide/GUIDELINE.md`
- `app/guide/Guideline_v2.md`
- `app/backend/backend_dataFlow.md`
- `Railway_QuickStart.md`
- `app/CV_EXTRACTION_FIX_SUMMARY.md`

## Verification

- Backend touched Python files were checked with `py_compile` during implementation.
- Frontend production build was run after major UI changes.
- Vite build completed with the existing large chunk warning.
- Frontend contrast fix and new API integrations were verified with `npm run build`.
- OCR deployment requirements were documented for Railway/Docker.

## Remaining Risks

- Full end-to-end QA should still cover OCR on real scanned PDFs, multi-CV merge behavior, and human fallback chat timing.
- Token counts from audit logs are currently estimates unless the LLM provider returns exact usage in every call.
- Prompt version comparison depends on representative test variables; admins should test with realistic student contexts.
