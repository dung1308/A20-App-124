# Guideline v2 - LLM Fine-Tuning Guide for Backend and Frontend

This document is an operating guide for an LLM that must refine, extend, or audit the VinUni Major Match skill across backend and frontend code. Use it together with:

- `app/guide/GUIDELINE.md`
- `app/guide/PRD.md`
- `14_05_Summary.md`
- Backend implementation under `app/backend`
- Frontend implementation under `app/frontend`

The baseline app is a production-ready MVP for VinUni major recommendation and admissions support. Preserve the core product behavior while improving reliability, UX, safety, and maintainability.

---

## 1. Project North Star

VinUni Major Match is an AI-assisted decision support tool for high school students considering VinUni majors. It must help students narrow choices, understand why each major fits, and recover safely when AI confidence is low.

The app must not behave like an admissions guarantee engine. It must not promise admission, scholarship, or exact outcomes. It must clearly distinguish AI recommendations from human counseling.

Core principles:

- Transparency: show what the AI used, what it inferred, and where information came from.
- Control: let users review, edit, retry, reset, and choose whether to confirm profile/CV data.
- Recovery: fail soft, provide fallback paths, and escalate risky cases to staff.

---

## 2. Current System Shape

Backend stack:

- FastAPI entrypoint: `app/backend/main.py`
- Multi-agent logic: `app/backend/agents/`
- Orchestration: `app/backend/orchestrator/`
- Guardrails: `app/backend/guards/`
- Services: `app/backend/services/`
- Schemas: `app/backend/models/schemas.py`
- Database utilities: `app/backend/database.py`, `app/backend/services/db_service.py`
- Configuration and LLM provider boundary: `app/backend/config.py`, `app/backend/services/llm_client.py`

Frontend stack:

- React + Vite + Tailwind CSS
- App entry: `app/frontend/App.jsx`
- Auth layout: `app/frontend/layouts/AuthenticatedLayout.jsx`
- Sidebar and shell: `app/frontend/components/panels/`
- Chat: `app/frontend/components/Chat/`
- CV upload: `app/frontend/components/CVUpload/CVUpload.jsx`
- Report cards: `app/frontend/components/Report/MajorCard.jsx`
- Wizard steps: `app/frontend/components/Wizard/`
- Pages: `app/frontend/pages/`
- API client: `app/frontend/services/`
- Shared state: `app/frontend/state/`

Important baseline features:

- LLM router routes requests to RAG, CRM, or Advisor.
- Advisor recommends among VinUni majors.
- RAG answers from handbook/FAQ corpus with retrieval and citations.
- CRM/profile agent handles student data and PII.
- Judge and guardrails detect hallucination, overcommitment, unsafe admissions claims, and escalation cases.
- CV extraction supports embedded PDF text and OCR fallback.
- Staff/admin views support dashboard, handoff, prompt versioning, audit logs, and token metrics.

---

## 3. Non-Negotiable System Rules

### 3.1 Hinge Rule

All LLM provider calls must remain behind the backend LLM service boundary. Do not import OpenAI or any other provider SDK directly from React, route handlers, agents, or random utilities.

Allowed places for provider-specific code:

- `app/backend/config.py`
- `app/backend/services/llm_client.py`
- Existing project-approved LLM wrapper/service files

If adding a new agent capability, route the prompt through the existing LLM abstraction and keep model/provider selection configurable.

### 3.2 Fixed Domain Boundary

Recommendation logic must stay constrained to the official VinUni major set used by the app. If the AI returns unknown majors, invalid IDs, unsupported claims, or insufficient confidence, trigger fallback instead of fabricating a result.

### 3.3 Safety Boundary

The system must never:

- Guarantee admission, scholarships, jobs, grades, or visa outcomes.
- Invent official policy, deadlines, or program facts without a cited source.
- Expose raw PII in public logs, audit views, or frontend debug output.
- Overwrite existing user profile data with empty extracted CV fields.
- Hide failure states behind fake confident answers.

---

## 4. Backend Fine-Tuning Instructions

### 4.1 Routing and Orchestration

When modifying backend request flow:

- Keep user intent routing explicit and testable.
- Preserve the route categories used by the app: RAG/admissions answer, Advisor/major matching, CRM/profile, staff handoff, system/admin.
- Make fallback and escalation states first-class response states, not string-only side effects.
- Keep orchestration readable enough that another engineer can trace user input through guards, agent call, judge, persistence, and response.

Expected files:

- `app/backend/orchestrator/router.py`
- `app/backend/orchestrator/pipeline.py`
- `app/backend/main.py`

Acceptance checks:

- Ambiguous user intent gets routed to a safe default or clarification path.
- Risky admissions claims reach judge/escalation logic.
- Agent failures return controlled fallback responses.

### 4.2 Advisor and Major Matching

Advisor output must be specific to the student's wizard answers, profile, and confirmed CV context where available.

Required output qualities:

- Top recommendations use only known VinUni major IDs.
- Each recommendation includes a fit rationale connected to user signals.
- Scores are bounded integers from 0 to 100.
- Low-confidence or contradictory input can return fallback instead of Top 3.
- The result includes the standard disclaimer.

Do not allow generic statements such as "this is a good major" without connecting to user-provided interests, strengths, dislikes, work style, or CV signals.

Expected files:

- `app/backend/agents/advisor.py`
- `app/backend/models/schemas.py`
- `app/backend/services/db_service.py`
- `app/backend/main.py`

Acceptance checks:

- Unknown major IDs are rejected.
- Empty, contradictory, or weak inputs do not produce fake certainty.
- Confirmed CV/profile data improves recommendations without overriding wizard answers.

### 4.3 RAG and Citations

RAG answers must stay grounded in retrieved sources. Prefer a shorter answer with citations over a long answer with weak grounding.

Required behavior:

- Include citations/source metadata for admissions facts.
- Distinguish retrieved official content from AI interpretation.
- Use query expansion and reranking only if it improves grounding.
- If retrieval confidence is weak, say so and offer a human/staff path.
- When user profile/CV context is used, separate "based on your profile" from "official source says".

Expected files:

- `app/backend/agents/rag.py`
- `app/backend/services/rag_service.py`
- `app/backend/services/ltr.py`
- `app/backend/services/reranker.py`
- `app/backend/data/`

Acceptance checks:

- Source list is present for policy/admissions answers.
- No admissions policy is invented when retrieval returns no support.
- User-specific context does not pollute shared Chroma collections.

### 4.4 CV Extraction and Profile Merge

CV upload is a profile feature, not only a wizard attachment.

Required behavior:

- Extract embedded PDF text first.
- Use OCR fallback when text is missing or too short.
- Return raw extracted text, structured CV data, CV signals, extraction metadata, and `cv_document_id`.
- Let the frontend show a review/edit step before confirmation.
- Merge only non-empty extracted fields into profile.
- Preserve existing useful profile data when CV extraction is partial.
- Track CV document versions with view, confirm, and delete actions.
- Use active confirmed CV/profile context for chat, RAG, and matching where available.

Expected files:

- `app/backend/services/pdf_loader.py`
- `app/backend/services/cv_parser.py`
- `app/backend/agents/cv_agent.py`
- `app/backend/models/schemas.py`
- `app/backend/services/db_service.py`
- `app/backend/services/rag_service.py`
- `app/backend/main.py`

Acceptance checks:

- Scanned CVs do not fail silently.
- LLM parsing timeout still returns local fallback structured data.
- Empty arrays or blank strings never erase existing profile fields.
- Repeated uploads use non-colliding document IDs and safe collection names.

### 4.5 Guardrails, Audit, and Handoff

Guardrails are part of product behavior, not optional middleware.

Required behavior:

- Detect overcommitment claims such as guaranteed admission, scholarship certainty, or "100% chance".
- Mask PII in logs and public audit views.
- Rate limit abusive traffic.
- Create pending handoff jobs when fallback or safety escalation occurs.
- Save human staff replies into the student's chat session as human advisor messages.
- Keep audit logs useful for staff without exposing sensitive raw data.

Expected files:

- `app/backend/guards/input_guard.py`
- `app/backend/guards/output_guard.py`
- `app/backend/guards/escalation_detector.py`
- `app/backend/guards/rate_limiter.py`
- `app/backend/guards/admin_audit.py`
- `app/backend/agents/judge.py`
- `app/backend/services/db_service.py`
- `app/backend/main.py`

Acceptance checks:

- Escalation test cases create staff-visible jobs.
- PII examples are masked in logs.
- Human fallback messages appear in student chat without page reload dependency when polling is implemented.

### 4.6 Admin, Prompt, and Token Operations

Admin/system features must be operational tools, not placeholder pages.

Required behavior:

- `/system/tokens` shows request count, prompt tokens, completion tokens, total tokens, and usage over time.
- Token counts can be estimated if provider counters are unavailable, but the UI/API must label estimates clearly.
- `/system/database` supports prompt versioning where implemented.
- Prompt versions include agent name, version, content, comparison output, and selected runtime alias.
- Runtime prompt replacement must only be enabled where the backend agent actually supports it.

Expected files:

- `app/backend/services/metric_service.py`
- `app/backend/services/prompt_service.py`
- `app/backend/services/seed_prompts.py`
- `app/backend/services/db_service.py`
- `app/backend/main.py`
- Related frontend system/admin pages

Acceptance checks:

- Admin can inspect token usage by time window, user email, and route/tool.
- Prompt version selection is persisted and visible in PostgreSQL.
- Unsupported live prompt replacement is disabled or clearly unavailable.

---

## 5. Frontend Fine-Tuning Instructions

### 5.1 UX Pattern

The primary user experience is a guided AI decision workflow, not a generic chatbot-first app.

Preserve these patterns:

- Wizard for structured student inputs.
- Report for Top 3 recommendations.
- Chat/RAG for follow-up admissions questions.
- Profile/CV for persistent student context.
- Staff/Admin dashboards for operational review.

Do not replace the wizard with open-ended chat unless explicitly requested. Chat can supplement the workflow but should not become the only path.

### 5.2 Visual Style

Use a clean, professional student-facing style:

- Background: white or very light neutral.
- Text: high contrast, readable, not decorative.
- Layout: practical app shell with clear navigation.
- Cards: use for repeated items or reports, not nested decorative sections.
- Buttons: clear primary/secondary states.
- Match score colors:
  - High: green
  - Medium: amber
  - Low: red
- Loading, empty, and error states must be visible and specific.

Keep mobile and desktop both usable. Avoid layouts where sidebars trap scrolling or hide content.

### 5.3 Wizard

Required behavior:

- Show progress across the 4-step flow.
- Validate each step inline.
- Preserve answers when moving backward.
- Do not use blocking browser alerts for normal validation.
- Include CV/profile context in match request when the user has selected or confirmed it.
- Show a clear loading state while matching.
- On network or AI error, allow retry without losing answers.

Expected files:

- `app/frontend/components/Wizard/`
- `app/frontend/pages/WizardPage.jsx`
- `app/frontend/state/store.js`
- `app/frontend/services/api.js`

Acceptance checks:

- Back/next does not reset selections.
- Invalid step shows inline message.
- Retry keeps current answers.
- Match request includes `cv_document_id` or structured profile context where supported.

### 5.4 Report

Required behavior:

- Recover latest generated result after refresh for logged-in users.
- Show summary header with number of recommendations, average match score, and verified-source count when available.
- Keep Top 3 major cards focused on fit rationale, student experience, score, and official source status.
- Include next actions:
  - Update Profile/CV
  - Rerun Wizard
  - Ask AI follow-up questions
  - Request human consultation
- Show fallback UX instead of fake recommendations when backend returns fallback.

Expected files:

- `app/frontend/pages/ReportPage.jsx`
- `app/frontend/components/Report/MajorCard.jsx`
- `app/frontend/services/api.js`
- `app/frontend/state/store.js`

Acceptance checks:

- Refresh does not erase the latest report when backend has persisted result.
- Fallback state has human consultation CTA.
- Report distinguishes official-source facts from AI fit rationale.

### 5.5 Profile and CV Review

Required behavior:

- CV upload displays extraction status.
- User can inspect raw text summary, structured fields, extracted skills/signals, and metadata.
- User can edit extracted fields before confirming.
- Profile shows uploaded CV versions.
- User can view, confirm, and delete CV documents.
- Confirming CV merges data without deleting useful existing data.

Expected files:

- `app/frontend/components/CVUpload/CVUpload.jsx`
- `app/frontend/pages/ProfilePage.jsx`
- `app/frontend/services/api.js`
- `app/frontend/state/store.js`

Acceptance checks:

- Empty extracted fields are visibly empty and do not overwrite profile on confirm.
- OCR/fallback metadata is shown in a human-readable way.
- Upload, confirm, view, and delete actions have loading/error states.

### 5.6 Chat and Human Fallback

Required behavior:

- Chat displays AI messages, citations, fallback notices, and human advisor replies distinctly.
- Student chat refreshes periodically when a handoff is active.
- Staff/admin can accept pending jobs and reply.
- User-visible text should be honest about whether the answer is AI-generated or human-authored.

Expected files:

- `app/frontend/components/Chat/ChatBox.jsx`
- `app/frontend/components/Chat/SourceList.jsx`
- `app/frontend/hooks/useChat.js`
- Staff/admin pages under `app/frontend/pages/`

Acceptance checks:

- Human messages are visually distinct but not noisy.
- Citation list is attached to grounded admissions answers.
- Active handoff state does not require manual full-page reload to receive staff response.

### 5.7 Resources Page

Required behavior:

- Add or maintain a student-facing `Tai nguyen` page.
- Explain when to use Wizard, Profile/CV PDF, AI Consultant, and Report.
- Make it accessible from the student sidebar without staff/admin permissions.
- Keep it practical and short; do not make it a marketing page.

Expected files:

- Sidebar/navigation components
- Student resource page under `app/frontend/pages/`

Acceptance checks:

- Student can find usage docs from normal app navigation.
- Page content maps to real app features and routes.

---

## 6. Cross-Cutting Data Contracts

Whenever an LLM changes either side of the stack, it must check the API contract from both directions.

For every touched endpoint:

- Backend request schema accepts exactly what frontend sends.
- Backend response schema includes exactly what frontend reads.
- Error and fallback shapes are handled explicitly.
- Loading, empty, and permission states have UI coverage.
- Auth/user ID assumptions are documented in code or route behavior.

Common contracts to verify:

- Match request and report result.
- CV upload, CV document list, confirm, view, and delete.
- Chat message send and poll.
- Staff handoff accept/reply.
- Token metrics filters and results.
- Prompt version create/compare/select.

---

## 7. Test and Verification Strategy

Backend checks:

- Run focused pytest files for touched agents, guards, services, or routes.
- Add tests when changing guardrails, prompt output validation, persistence merge rules, or handoff behavior.
- Test both successful and fallback paths.

Useful existing test areas:

- `app/backend/test_escalation_detector.py`
- `app/backend/test_judge_escalation_integration.py`
- `app/backend/test_guardrails_scenarios.py`
- `app/backend/test_crm_pii.py`
- `app/backend/test_pmf_handoff.py`
- `app/backend/test_profile_chat_impact.py`
- `app/backend/test_golden_evals.py`

Frontend checks:

- Run build or lint where available.
- Manually verify key flows in browser when changing layouts, forms, chat, or report.
- Check mobile width and desktop width for sidebar, scroll, and button wrapping.

Suggested commands:

```bash
cd app/backend
pytest
```

```bash
cd app/frontend
npm run build
```

If full test suites are too slow, run focused tests first and state what was not run.

---

## 8. Prompting Another LLM With This Guide

Use this prompt template when asking another LLM to refine the project:

```text
You are refining VinUni Major Match. Read app/guide/Guideline_v2.md, app/guide/GUIDELINE.md, app/guide/PRD.md, and 14_05_Summary.md first.

Goal:
<specific backend/frontend task>

Constraints:
- Preserve TCR: Transparency, Control, Recovery.
- Preserve the LLM hinge rule.
- Do not invent admissions facts or unsupported VinUni policy.
- Keep API contracts aligned between backend and frontend.
- Add or update focused tests for changed backend behavior.
- Verify frontend build for changed UI behavior.

Deliverables:
- Summary of changes.
- Changed files.
- Verification run and result.
- Any remaining risks or follow-up tasks.
```

For backend-only tasks, add:

```text
Focus on route schemas, agent/service boundaries, guardrails, persistence, and fallback behavior.
Do not edit frontend unless needed to keep the API contract working.
```

For frontend-only tasks, add:

```text
Focus on user flow, loading/error/fallback states, responsive layout, and accurate display of backend state.
Do not mock backend fields that are not returned by the API; update the API client contract if needed.
```

For full-stack tasks, add:

```text
Start from the API contract. Update backend schema/route/service behavior first, then frontend API client/state/UI, then verify the end-to-end flow.
```

---

## 9. LLM Review Checklist

Before finalizing any backend/frontend change, the LLM must answer:

- Did I preserve the LLM hinge rule?
- Did I keep recommendations constrained to known VinUni majors?
- Did I add or preserve citations for admissions facts?
- Did I handle fallback and escalation states without fake certainty?
- Did I avoid leaking PII in logs or UI?
- Did I preserve existing profile data during CV merge?
- Did I align frontend request/response handling with backend schemas?
- Did I keep loading, empty, error, and retry states usable?
- Did I verify with relevant backend tests or frontend build?
- Did I list changed files and residual risks?

---

## 10. Pull Request Requirements

Before creating a PR, ensure repository hooks are installed:

```bash
bash scripts/setup_hooks.sh
```

PR description must include:

```text
## Summary
<description of changes>

## Changes
- <list of changed files>
```

Do not commit `.ai-log/*.jsonl` files.

