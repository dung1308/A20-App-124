---
name: ui-pattern
description: "Brainstorm partner for a new AI app idea in the Smart Educational Consultant / Admissions Counselor domain. Takes a 1-paragraph idea, clarifies it through a short conversation, picks one of 7 UI patterns, then writes PRD.md + GUIDELINE.md into the repo. Use when user says 'help me spec this app', 'brainstorm my idea', 'viết spec / PRD cho app', 'chọn pattern / UI cho idea', 'bắt đầu app mới', 'blank page', 'I have an idea, help me turn it into a plan', 'app em sẽ như thế nào', or is at the blank-page moment before any code exists. Domain focus: admissions counseling, student profiling, program matching, document guidance, school applications."
---

# UI Pattern — From idea to PRD + GUIDELINE in one conversation
# Domain: Smart Educational Consultant / Admissions Counselor AI

User has an idea for an AI-powered admissions or educational consulting app and wants to start building. This skill runs a **short brainstorm conversation** with the user, picks **one of 7 UI patterns**, then writes two files into the repo:

- `PRD.md` — problem, users, stories, data model, **tech stack (from user's brief)**, constraints, API surface, success criteria
- `GUIDELINE.md` — chosen UI pattern, T·C·R checklist, what NOT to build yet (references `PRD §Tech stack` for tech — doesn't restate it)

Stack is a **product decision**, not a UX decision. If the user briefs a stack in their paragraph (e.g., "Stack: React + Vite + Express mock + Claude 3.5 Sonnet"), the skill **records it verbatim into PRD**. The skill does NOT invent stack. If the user didn't mention one, the skill asks once before writing.

## Domain context — Admissions Counselor AI

This skill is tuned for the admissions counseling and educational consulting domain. Common actors:

- **Students** — ask about programs, requirements, deadlines, essays, fit
- **Counselors / Advisors** — review AI-generated recommendations, manage student portfolios
- **Parents** — monitor progress, understand timelines and financial aid
- **Administrators** — review queued student cases flagged for human attention

Common AI tasks in this domain:
- Program matching (student profile → ranked school list with rationale)
- Document review (personal statement, CV, essays — AI drafts + human refines)
- Deadline tracking (NL query → structured calendar output)
- Eligibility checking (student data → criteria match per school)
- Counselor queue (AI pre-screens student cases, counselor approves/rejects/escalates)

## What this skill does

1. Accepts a 1-paragraph idea from the user (or asks for one)
2. Asks 2–3 clarifying questions — adaptive, not a canned script — **admissions-specific defaults shown below**
3. Picks one of the 7 UI patterns, explains why in one line
4. Writes `PRD.md` + `GUIDELINE.md` to the repo root
5. Tells the user what to paste next into Claude Code to start building

## When to use it

- User has an admissions/consulting app idea but no PRD and no code
- User has a backend (student data, school database) and wants the frontend
- User is re-spec'ing an abandoned counseling tool
- Team needs a paved path from idea to "ready to build"

If the team already has working UI, route them to `/tcr-apply` instead — that skill retrofits T·C·R on existing code.

## The 7 UI patterns — admissions domain mapping

Memorize names — `/tcr-apply` and `/prd-to-screens` use the same list.

1. **Chat + context panel** — student or counselor asks a question; AI answers with visible evidence. **Most common admissions pattern.** Examples: student asks "Am I competitive for MIT?", panel shows match score + key criteria breakdown. Or: counselor asks "What programs fit this student?", panel shows ranked list with reasoning.
2. **Upload → dashboard** — student uploads transcript/CV/test scores → AI extracts structured profile → dashboard shows profile completeness, predicted GPA band, subject strengths. Also: counselor uploads batch student files → insight tiles per cohort.
3. **Query → structured result** — NL question → table/chart. "Show me all students with GPA > 3.5 applying to Ivy League" → filterable table. Or: "Compare admission rates for CS programs in the US" → chart.
4. **Wizard + inline audit** — multi-step student profile builder or application checklist. AI pre-fills each step from uploaded documents; each field is checked against program requirements in real time. "Does your TOEFL meet this school's cutoff?" inline.
5. **Draft → approve → send** — AI drafts personal statement / recommendation letter / email to admissions office → counselor or student reviews → system sends. Irreversible send dominates.
6. **Queue + approval** — AI pre-screens a batch of student applications or flags at-risk students → counselor clears the queue (approve, escalate, request more info). Used in counseling centers handling many students.
7. **Real-time streaming** — live voice Q&A ("talk to your admissions advisor"), live transcript of mock interview, or real-time essay feedback as student types.

### Meta-pattern — "Conversational UI + Evidence Panel"

Pattern 1 is the most versatile for admissions:

- panel = **match scores** → program fit chatbot
- panel = **checklist status** → requirements tracker alongside chat
- panel = **document citations** → RAG on school handbooks / program pages
- panel = **timeline** → deadline calendar driven by chat
- panel = **student profile summary** → counselor seeing student context while chatting

When in doubt between patterns 1, 3, and 6, default to **1** and choose the panel payload.

## Step 1 — Get the idea

**Language rule:** match the user's input language. If Vietnamese, ask in Vietnamese. If English, ask in English. Every user-facing string in this skill follows this rule.

If the user has already pasted an idea, summarize it back in one sentence to confirm. If they haven't, ask:

> EN: **Briefly describe your idea:** what does the app do, who uses it, what problem does it solve? If you've already picked a stack, mention it. (Admissions / educational consulting context assumed.)
> VN: **Mô tả ngắn ý tưởng của bạn:** app làm gì, ai dùng, giải quyết vấn đề gì? Nếu đã định stack rồi thì nói luôn. (Ngữ cảnh: tư vấn tuyển sinh / hướng nghiệp.)

## Step 2 — Clarify through conversation

Based on the idea, pick **2–3 things that are actually unclear**. Use the **AskUserQuestion tool** (multi-choice, with suggested options) — never print plain-text questions and wait for chat reply.

**Admissions-domain clarification pool** (pick only what's unclear):

- **Primary actor** — is the AI-facing user a student, a counselor, or both? Which is Demo 1?
- **Input/Output shape** — does user ask questions (chat), upload documents, fill a form, or review a list?
- **Reversibility** — does any AI action send something irreversible (submit application, send email to admissions office, publish recommendation letter)?
- **Trust signal type** — does the panel show match scores (proprietary logic), citations from school handbooks (RAG), or checklist status (rule-based)?
- **School data** — is the app grounded on a real school database / corpus, or does it use mock/static data?
- **Constraints** — UX lab, no auth, Vietnamese UI, single-school vs. multi-school?
- **Stack** — if user hasn't specified, ask before assuming.

For each question, give 2–4 suggested options + "Other". Phrase in user's language.

**Admissions-specific example question:**

> AskUserQuestion
> - question: "What should the context panel show when student asks about their fit for a school?"
> - options:
>   1. "Match score + key criteria breakdown (no real corpus — logic-based)"
>   2. "Citations from school's official handbook / website (RAG)"
>   3. "Checklist: which requirements met vs. missing"
>   4. "Other — I'll say"

If the idea paragraph already covered everything, skip to Step 2.5 with one short confirmation.

## Step 2.5 — Pick UI style

Use **AskUserQuestion** with these options (ask unless the user already stated a preference). Phrase in the user's language:

> AskUserQuestion
> - question: "UI style direction for this admissions app?"
> - options:
>   1. "Minimal clean — Linear / Notion feel, lots of whitespace, professional"
>   2. "Playful educational — bright accents, rounded corners, approachable for students"
>   3. "Data-dense professional — compact, dashboard feel for counselors managing many students"
>   4. "Just functional — inline styles, unpolished, demo-grade"

Save the answer — it goes into `GUIDELINE.md §Visual style`.

## Step 3 — Pick the UI pattern

Apply priority rules (top wins):

1. **Irreversible action** (submit application, send email to school, publish letter) → pattern 5.
2. **Batch of students to triage** (counselor queue, at-risk flagging) → pattern 6.
3. **Live voice advising / real-time essay feedback** → pattern 7.
4. **Multi-step profile form** (student onboarding, application wizard) → pattern 4.
5. **Document upload** (transcript, CV, test scores → structured profile) → pattern 2.
6. **NL question → chart/table** (compare programs, filter student cohort) → pattern 3.
7. **NL question → text + evidence** (chat with school context, advisor Q&A) → pattern 1.
8. **Still ambiguous** → default to 1 and set panel payload for this domain.

**Admissions borderline cases:**
- Chat that also shows a ranked school list → pattern 1 with panel = ranked list (output shape is prose + panel data, not pure chart).
- Profile wizard that ends with "AI drafts personal statement → counselor approves → sends" → pattern 5 (irreversible send dominates).
- Student asks NL question, gets a filterable comparison table of programs → pattern 3 (output shape is table, not prose).

Tell the user the pattern + one-line reason. Offer the runner-up if the pick feels forced.

## Step 4 — Write PRD.md

Write to `<repo-root>/PRD.md`. Overwrite if exists (warn + show diff first).

```markdown
# PRD — {product name}

## Problem + context
{1–2 sentences on the admissions pain. Add scope: single school, multi-school, UX lab, counseling center.}

## Users
- **Primary:** {Student / Counselor / Parent — the AI-facing actor for Demo 1}
- **Secondary:** {if any — e.g., counselor reviewing AI output, admin}

## User stories
3–5 stories. Tag each with **(Demo 1)**, **(Demo 2)**, or **(Later)**.

1. **(Demo 1)** As a {student/counselor}, {action} so that {outcome}.
2. **(Demo 1)** ...
3. **(Demo 2)** ...
4. **(Demo 2)** ...
5. **(Later)** ...

## Data model
{Minimal — only entities needed by the Demo 1 stories. For admissions apps, common entities:}
- **Student profile** — id, name, GPA, test_scores, intended_major, target_schools[], status
- **Schools** — id, name, program, requirements{}, admission_rate, deadlines{}
- **Applications** — id, student_id, school_id, status, essay_draft, submitted_at
- **Flags / notes** — id, student_id, counselor_id, note, created_at
{Add only what the stories actually need. Don't over-model.}

## Tech stack
{Verbatim from user's brief. If user didn't specify: ask once. Do not invent.}

## Constraints
{Verbatim from user's brief — UX lab, no auth, mock data, single-school, language, etc.}

## API surface
{Operations only — no URLs. Examples for admissions domain:}
- **ask counselor** — student sends question → returns answer text + panel payload (match score / checklist / citations)
- **upload documents** — student uploads transcript/CV → returns structured profile fields
- **get school list** — NL query → returns filtered/ranked list of schools with match rationale
- **flag student** — counselor flags student case with reason → appears in review queue
- **draft document** — AI drafts personal statement / letter from student profile → returns draft text

## Success criteria
{2–3 testable criteria. Examples:}
- Student asks 3 questions, session history preserved, panel updates per answer
- Counselor loads queue, filters by flag type, approves/escalates items without page reload
- Swapping LLM provider = edit 1 file (src/llmService.js), UI unchanged

## Out of scope
- Auth / login (unless explicitly in scope)
- Real school database integration (mock data is sufficient for UX lab)
- Mobile layout, i18n, dark mode, polish CSS
- Production deployment
```

## Step 5 — Write GUIDELINE.md

Write to `<repo-root>/GUIDELINE.md`. Overwrite if exists (warn + show diff first).

```markdown
# GUIDELINE — {product name}

> Tech stack: see `PRD §Tech stack`.

## UI pattern
**{N}. {pattern name}**

Why this pattern: {1–2 lines tying user's answers to the pick — use admissions-specific language}

{If pattern 1: add "Conversational UI + Evidence Panel" note. For admissions apps:
- panel = match scores → logic-based, NOT fake school data. Label honestly: "AI-estimated fit".
- panel = citations → RAG on school corpus. Label: "Source: [school name] admissions page".
- panel = checklist → rule-based requirements check. Label: "Requirements status".
- panel = ranked list → program recommendations. Label: "Suggested programs".
Never fake school data or admission statistics. If no real corpus, use self-assessed fit scores and label them as such.}

## Visual style
{From Step 2.5 answer: Minimal clean / Playful educational / Data-dense professional / Just functional}

Concrete rules:
- {4–5 bullets specific to this style and the admissions context}

## User flow (3 steps)
1. {Student/Counselor} {input action — e.g., "types a question about program requirements"}
2. App {AI processing — name the LLM call, what it receives, what it returns — e.g., "sends question + student profile context to src/llmService.js → returns {answer, match_score, checklist_items[]}"}
3. {Student/Counselor} {interacts with output — e.g., "reads answer in chat, sees match score + checklist in panel"}

{If two roles: add a second flow block for Demo 2.}

## T·C·R checklist for this pattern

### T — Transparency (what AI work is visible)
- [ ] {pattern-specific T item — admissions context, e.g. "match score labeled as AI estimate, not official data"}
- [ ] {T item 2}
- [ ] {T item 3}

### C — Control (what user can stop / edit / override)
- [ ] {pattern-specific C item}
- [ ] {C item 2}
- [ ] {C item 3}

### R — Recovery (validation + retry + undo)
- [ ] {pattern-specific R item}
- [ ] {R item 2}
- [ ] {R item 3}

**Honesty rule for admissions AI:**
AI match scores, admission probability estimates, and school comparisons must be labeled as AI-generated estimates, never as official statistics. If the app has no access to real admission data, display: "AI-estimated fit — verify with official sources." Never invent acceptance rates or requirements.

## Hinge rule
All LLM calls go through `src/llmService.js` (or equivalent named in `PRD §Tech stack`). UI never imports a provider SDK directly. Swap providers = edit one file.

## What NOT to build yet
- Auth, login, role-based access (unless scoped in PRD)
- Real school database — mock JSON is sufficient for UX lab
- Mobile layout, responsive polish
- Dark mode, i18n, loading skeleton states
- Official admission statistics integration
- T·C·R features in full (run `/tcr-apply` after baseline)
- {admissions-specific deferred features — e.g., "payment/subscription for premium counseling", "multi-language support", "live integration with Common App"}
```

Fill the T·C·R checklist from the matrix in Step 5.1 — copy, don't invent.

## Step 5.1 — T·C·R matrix for admissions domain

Use to fill the GUIDELINE checklist. Adapted for admissions context.

### 1. Chat + context panel (admissions Q&A)
- **T:** Panel shows 2–4 items: match score OR source citations OR checklist status (depending on trust signal type agreed in Step 2). Streaming status line ("Checking requirements…"). Confidence or source label on each panel item. Disclaimer: "AI estimate — verify with official sources."
- **C:** Stop button during streaming. Edit last question. Clear chat (Cmd+K). Student can flag an answer as incorrect.
- **R:** Error bubble with retry on LLM fail. Pre-flight: warn if question is too vague for admissions context. Preserve chat history on network fail.

### 2. Upload → dashboard (document ingestion)
- **T:** Parse progress ("Extracting GPA… Done. Parsing test scores… Done."). Per-field source link back to uploaded file page. Extraction confidence per field ("GPA: 3.85 · extracted from page 1, confidence: high").
- **C:** Cancel during processing. Preview before "Analyze" if file is large. Ability to manually correct extracted fields.
- **R:** Pre-flight: reject non-PDF/image files with clear error. "Try re-upload" on parse fail. Keep previous extraction result if new upload fails.

### 3. Query → structured result (program search / cohort filter)
- **T:** Show generated filter criteria above results ("Filtering by: GPA > 3.5, major: CS, country: US"). Confidence badge. Meta line (N programs matched / query time).
- **C:** Edit generated filter before re-run. Confirm modal for any destructive action (e.g., "export all matched students"). Query history.
- **R:** Retry on fail. "Rephrase question" button on error. Timeout guard (15s).

### 4. Wizard + inline audit (student profile builder / application checklist)
- **T:** Per-field indicator (✓ meets requirement / ⚠ borderline / ✗ below cutoff) with the specific requirement shown (e.g., "TOEFL ≥ 100 — your score: 92 ⚠"). End-of-wizard summary: "N requirements met · M borderline · K missing."
- **C:** Back/forward without data loss. Save draft. Override AI warning with a reason textbox. "Regenerate this field only" without touching others.
- **R:** Submit disabled if any ✗ remains — tooltip lists which. Autosave banner. Don't reset wizard on submit failure.

### 5. Draft → approve → send (personal statement / letter / email)
- **T:** Diff vs. previous draft. Per-section confidence. Generation meta (model, timestamp, "based on student profile fields: GPA, extracurriculars, intended major"). Recipient/destination preview.
- **C:** Mandatory preview step before send. Edit any section. Save as draft. Template-locked fields (school name, program name) show lock icon.
- **R:** Hard confirm before send (type "SEND" or "GỬI"). Dry run to test recipient first. Undo toast with 10s window. Keep draft on send failure.

### 6. Queue + approval (counselor review dashboard)
- **T:** Per-student confidence dot (green: AI-confident recommendation / yellow: borderline / red: needs human review). One-line AI reasoning ("Flagged: GPA below program minimum"). Header counts: N pending · M auto-approvable · K needs review.
- **C:** Bulk select + shift-click. Keyboard (J/K/A/R/U). Filter by flag reason, school, student segment. "Escalate to senior counselor" option.
- **R:** Undo stack (10 actions). "Request more info from student" as alternative to reject. Re-surface case if student updates profile.

### 7. Real-time streaming (live voice advising / real-time essay feedback)
- **T:** Live status ("Listening…" / "Analyzing your essay…"). Token-by-token output. Latency bar.
- **C:** Stop button. Pause/resume for transcription. Space/Esc shortcuts.
- **R:** Auto-reconnect (max 3). Preserve transcript on reconnect. Manual restart button.

## Step 6 — Hand off

Tell the user briefly in their language:

> EN:
> Wrote PRD + GUIDELINE at repo root.
> - **PRD** — problem, users, stories, tech stack, constraints, API surface
> - **GUIDELINE** — chosen UI pattern, visual style, T·C·R checklist, hinge rule
>
> Next: baseline build from these two files. Run `/tcr-apply` after baseline to layer T·C·R.

> VN:
> Xong PRD + GUIDELINE ở repo root.
> - **PRD** — problem, users, stories, tech stack, constraints, API surface
> - **GUIDELINE** — UI pattern đã chọn, visual style, T·C·R checklist, hinge rule
>
> Tiếp theo: build baseline từ 2 file này. Chạy `/tcr-apply` sau baseline để layer T·C·R.

Stop there. Claude Code handles planning and coding from the two files.

## Anti-patterns — do NOT do these

- **Don't invent a stack.** If user didn't brief one, ask.
- **Don't restate the stack in GUIDELINE.** GUIDELINE references `PRD §Tech stack`. One source of truth.
- **Don't pick 2 patterns.** Commit to one. "Hybrid" = confused users.
- **Don't write any code.** Only `PRD.md` + `GUIDELINE.md`.
- **Don't invent school data or admission statistics.** If no real corpus, use mock data and label AI estimates honestly.
- **Don't add T·C·R features in the baseline build prompt.** Baseline = skeleton. T·C·R = separate prompts.
- **Don't invent a new pattern.** Default to 1 and adjust panel payload if nothing fits.
- **Don't skip the admissions honesty rule.** AI match scores are estimates — label them as such every time.

## Principles

- **Idea → short brainstorm → PRD + GUIDELINE → build prompt.** Four artifacts, one flow.
- **PRD owns product + stack. GUIDELINE owns UX.**
- **Skill records, doesn't invent.** User's stack and constraints go in PRD verbatim.
- **Skeleton before T·C·R.** Two phases, two prompts, two commits.
- **Admissions honesty is load-bearing.** AI estimates ≠ official data. Label every trust signal honestly.
- **Commit to the pick.** Ambiguous case → pattern 1 with adapted panel payload for admissions domain.

---

## Reference — worked example

For a full end-to-end walk-through, see `./references/example-admissions-counselor.md` (to be written for this domain). Illustrative only — domain-specific strings and thresholds don't transfer to other apps.
