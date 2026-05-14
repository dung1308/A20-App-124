# Guideline v3 - Pain-Point Driven LLM Implementation Guide

Use this guide when refining, extending, or auditing the VinUni Major Match backend and frontend. It updates `Guideline_v2.md` with a stronger product-quality layer from:

- `app/Pain_Point.md`
- `app/Pain_Point_skills.md`
- `app/guide/PRD.md`
- `app/guide/GUIDELINE.md`

The app is a production-ready MVP for VinUni major recommendation and admissions support. Preserve the core behavior while improving trust, recovery, clarity, speed, and safety.

---

## 1. North Star

VinUni Major Match is an AI-assisted decision support tool for high school students considering VinUni majors.

The product must help students:

- Narrow suitable majors.
- Understand why each major fits.
- Review and control profile/CV data.
- Recover safely when AI confidence is low.
- Escalate to a human advisor when needed.

The app must not behave like an admissions guarantee engine. Do not promise admission, scholarship, or exact outcomes. Clearly separate AI guidance from human counseling.

---

## 2. Pain-Point Implementation Rules

When proposing or implementing a feature, optimize for:

- Trust: make AI reasoning visible.
- Recovery: let users retry, revise, continue later, or escalate safely.
- Clarity: show what happened and why.
- Speed: prefer features that can be shipped and verified in under 3 days.
- Safety: stay within approved admissions boundaries.

For every new feature or fix, document these six items before implementation:

1. Pain point addressed.
2. Smallest useful fix.
3. Backend files likely affected.
4. Frontend files likely affected.
5. Fallback behavior.
6. Test or verification steps.

If a feature does not improve at least one of Trust, Recovery, Clarity, Speed, or Safety, deprioritize it.

---

## 3. Pain-Point Priority Map

### 3.1 Weak Confidence Feels Like Failure

Problem: Low-confidence answers can feel incomplete or generic.

Required UX:

- Show a structured fallback card.
- Explain the reason for low confidence.
- Offer next actions such as retry, refine profile, open resources, or request human fallback.

Backend expectation:

- Return confidence, fallback reason, and recommended next action where possible.
- Keep escalation signals explicit in the response payload.

Frontend expectation:

- Never show only a generic error or apology.
- Provide a visible recovery path on chat, wizard, and report screens.

### 3.2 Recommended Majors Feel Like A Black Box

Problem: Students may not understand why top majors were recommended.

Required UX:

- Add a "Why this matches you" explanation for each major.
- Show 3 to 5 matched signals.
- Show 1 to 2 tradeoffs or missing signals.
- Label whether each signal came from profile, CV, wizard answers, or RAG context.

Backend expectation:

- Return structured match reasons and evidence.
- Avoid vague language such as "good fit" without supporting signals.

### 3.3 Profile And CV Edits Need Clear Control

Problem: Users may worry CV extraction overwrites profile data incorrectly.

Required UX:

- Use a review-and-confirm diff before merge.
- Show what will be added, kept, changed, or skipped.
- Let users edit structured CV fields before saving.

Backend expectation:

- Store CV document versions.
- Preserve the uploaded PDF for later review.
- Keep `cv_document_id` attached to wizard/match/profile flows.
- Merge only after explicit confirmation.

### 3.4 Retry And Recovery Are Too Hidden

Problem: Network, parsing, or AI failures can leave users stuck.

Required UX:

- Add visible retry, reset, and continue-later actions.
- Keep partial progress when possible.
- Avoid dead-end states.

Backend expectation:

- Make failures typed and actionable.
- Return enough context for the UI to show the correct recovery action.

### 3.5 Citations Are Hard To Scan

Problem: Citations may exist but still be hard to understand quickly.

Required UX:

- Use a compact source panel.
- Label sources as official, derived, profile-based, or generated.
- Show enough metadata to verify the claim.

Backend expectation:

- Return citation metadata consistently for RAG answers and recommendation claims.

### 3.6 Chat And Report Feel Disconnected

Problem: Users may want follow-up questions after reading recommendations.

Required UX:

- Add contextual "ask about this major" actions on major cards.
- Open chat with the selected major and report context.
- Preserve the report context in follow-up prompts.

Backend expectation:

- Accept context from report actions without trusting it blindly.
- Re-ground admissions facts through RAG when needed.

### 3.7 Handoff Status Is Unclear

Problem: Users may not know whether a human advisor has been engaged.

Required UX:

- Show queue state, timestamp, and latest staff message.
- Make accepted/in-progress/closed states clear.
- Provide next-step guidance while waiting.

Backend expectation:

- Store handoff status, owner, accepted time, and messages.
- Staff/admin/editor pages must expose pending handoff jobs.

### 3.8 Wizard Progress Is Too Abstract

Problem: Students may not understand what remains in the flow.

Required UX:

- Show step labels, estimated time, and completion hints.
- Make the Wizard button visible from Profile so users can change answers later.
- If a user has not answered the wizard, make the Profile CTA obvious.

Backend expectation:

- Support updating answers without corrupting previous profile or CV data.

### 3.9 Empty States Must Teach

Problem: Blank pages feel like dead ends.

Required UX:

- Profile, report, chat, resources, admin, and staff pages need educational empty states.
- Each empty state should give one clear action.

### 3.10 Admin Tools Need Product Quality

Problem: Admin tools are useful but can feel like developer-only utilities.

Required UX:

- Use plain labels and clear actions.
- Show health/status badges for token usage, prompt version, RAG ingest, handoff volume, and database state.
- For RAG ingest, clearly distinguish scheduled/periodic ingestion from immediate ingestion.

Backend expectation:

- Expose admin endpoints with clear status fields and audit logs.

### 3.11 Feature Explainability Is Required

Problem: Staff and developers need to know which rule or signal triggered behavior.

Required UX:

- Admin/staff views should show a lightweight decision trace when useful.

Backend expectation:

- Attach decision trace objects for routing, fallback, escalation, recommendation, and prompt-version selection.

### 3.12 Resources Must Be Intent-Aware

Problem: Help pages can become generic documentation.

Required UX:

- Add Resources content that explains how to use the product.
- Link resources from Profile, Wizard, Report, and Chat based on the user's current task.
- Prefer short just-in-time snippets over long static documentation.

---

## 4. Current System Shape

Backend stack:

- FastAPI entrypoint: `app/backend/main.py`
- Multi-agent logic: `app/backend/agents/`
- Orchestration: `app/backend/orchestrator/`
- Guardrails: `app/backend/guards/`
- Services: `app/backend/services/`
- Schemas: `app/backend/models/schemas.py`
- Database utilities: `app/backend/database.py`, `app/backend/services/db_service.py`
- LLM provider boundary: `app/backend/config.py`, `app/backend/services/llm_client.py`

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
- CV extraction supports embedded PDF text, OCR fallback, structured parsing, and saved document versions.
- Staff/admin views support handoff, prompt versioning, audit logs, token metrics, and RAG ingestion.

---

## 5. Non-Negotiable Engineering Rules

### 5.1 Hinge Rule

All LLM provider calls must remain behind the backend LLM service boundary. Do not import OpenAI, Gemini, or any provider SDK directly from React, route handlers, agents, or random utilities.

Allowed provider-specific locations:

- `app/backend/config.py`
- `app/backend/services/llm_client.py`
- Existing approved LLM wrapper/service files.

If adding a new agent capability, route the prompt through the existing LLM abstraction and keep model/provider selection configurable.

### 5.2 Safety And Admissions Claims

Do not allow generated content to:

- Promise admission, scholarship, ranking, or guaranteed outcomes.
- Invent VinUni policies.
- Present unsupported facts without citations.
- Treat the recommendation as a final decision.
- Store or expose PII unnecessarily.

When confidence is low, prefer fallback, clarification, RAG citation, or human handoff.

### 5.3 Profile And CV Data

CV-derived data is draft data until the user confirms it.

Required behavior:

- Keep raw PDF/document version history available from Profile.
- Keep structured parse results editable.
- Preserve existing user profile data unless the user confirms a merge.
- Keep `cv_document_id` through Wizard, Profile, Match, and Report flows.
- Show data provenance when a recommendation uses CV/profile signals.

### 5.4 Prompt Versioning

Prompt versioning must support:

- Agent selection from a clear list.
- Add/update prompt version by number or name.
- Compare rendered outputs between versions.
- Select the active version for use.
- Show which active prompt version served a response where practical.

Do not make admins type unknown agent names from memory. Provide dropdowns or discoverable lists.

### 5.5 Token And Database Admin

System admin pages should be understandable without reading code.

Required capabilities:

- `/system/tokens`: filter by user/date/source, show usage records, and graph frequency.
- `/system/database`: inspect important records and use clear actions such as add admin, add editor, grant/revoke permission, blacklist user, and prompt versioning controls.
- All destructive or permission-changing actions need confirmation and audit logging.

---

## 6. Backend Implementation Guidance

When adding backend behavior:

- Prefer extending existing services instead of creating parallel logic.
- Keep route payloads typed with Pydantic schemas.
- Keep database writes auditable for admin/staff actions.
- Return structured error and fallback payloads.
- Do not hide important state only in logs.

For agent changes:

- Keep prompts versionable where admin control matters.
- Include sources, confidence, reasoning labels, and decision trace where useful.
- Keep RAG-grounded facts separate from profile-derived inferences.

For CV changes:

- Use embedded PDF text first.
- Fall back to OCR for image-based PDFs.
- Return parse metadata and extraction confidence.
- Store document versions and connect them to user profile updates.

For human fallback:

- Create a pending job when escalation is required.
- Allow admin/editor/staff to accept the job.
- Store the staff reply in the user-visible chat/session history.
- Close or update job status explicitly.

---

## 7. Frontend Implementation Guidance

When adding UI behavior:

- Match existing React, Vite, Tailwind, routing, and state patterns.
- Build the actual workflow screen, not a marketing or placeholder page.
- Prefer compact, operational UI for admin/staff pages.
- Use visible recovery actions on failure states.
- Avoid empty screens without a next action.

Required student-facing expectations:

- Profile shows Wizard CTA clearly.
- Profile shows saved CV PDF/document versions.
- Profile exposes Summary, Career goals, Skills, Education, and Experience.
- Wizard can update answers and keep the active `cv_document_id`.
- Report cards explain why a major matches and how to ask follow-up questions.
- Chat can suggest when to use Wizard, Profile, Resources, or human fallback.

Required admin/staff expectations:

- Staff page shows human fallback jobs and active sessions.
- Admin pages use understandable labels and action buttons.
- Prompt versioning includes add/update, compare, select, and agent dropdowns.
- Token page includes filters and frequency graph.
- RAG ingest labels distinguish periodic ingest from immediate ingest.

---

## 8. Feature Proposal Template

Use this template before asking another LLM or agent to implement a feature:

```md
## Feature
<short name>

## Pain Point
<which pain point this solves>

## Smallest Useful Fix
<the smallest shippable behavior>

## Backend Files
- <likely files>

## Frontend Files
- <likely files>

## Fallback Behavior
<what happens when data/API/AI fails>

## Safety Rules
<admissions, PII, confidence, citation constraints>

## Verification
- <backend checks>
- <frontend build/UI checks>
- <manual QA path>
```

---

## 9. Testing And Verification

Minimum verification for backend changes:

- Run targeted Python compile or tests for touched modules.
- Exercise the relevant API path manually or through tests.
- Verify fallback/error payloads, not only success cases.

Minimum verification for frontend changes:

- Run the frontend production build after user-facing UI changes.
- Check layout at desktop and mobile widths for changed screens.
- Confirm empty, loading, success, and error states.

Manual QA paths to prioritize:

- Student uploads scanned CV -> OCR parse -> reviews structured fields -> confirms merge -> sees Profile update.
- Student opens Profile -> sees Wizard CTA -> updates answers -> report uses new context.
- Student receives low-confidence answer -> sees fallback card -> requests human help.
- Staff opens `/staff` -> accepts fallback job -> replies -> student sees new chat message.
- Admin opens `/system/database` -> creates prompt version -> compares output -> selects active prompt.
- Admin opens `/system/tokens` -> filters usage -> checks frequency graph.

---

## 10. PR And Review Checklist

Before considering work complete:

- The feature maps to at least one pain point.
- User-facing AI behavior has a recovery path.
- Admissions claims are bounded and cited where needed.
- Profile/CV data changes require user control.
- Admin/staff actions are clear and auditable.
- Prompt/version/token/handoff changes expose state in the UI.
- Docs are updated when behavior changes.
- Build or targeted verification has been run, or the reason it was not run is documented.
