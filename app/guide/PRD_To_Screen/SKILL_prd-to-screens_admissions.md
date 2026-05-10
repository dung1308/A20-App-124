---
name: prd-to-screens
description: "Read a PRD for a Smart Educational Consultant or Admissions Counselor AI system, pick the highest-value screen to build first, map it to one of 7 AI-app UI patterns, write GUIDELINE.md into the repo. Use when user has a PRD (link, path, or pasted text) and asks 'what should I build first', 'which screen matters most', 'turn this PRD into a UI', 'help me scope this app', or shows up with a spec but no code. Domain: admissions counseling, student profiling, program matching, document review, school applications."
license: MIT
argument-hint: "[PRD path or pasted PRD text]"
---

# /prd-to-screens — PRD in, GUIDELINE out
# Domain: Smart Educational Consultant / Admissions Counselor AI

User has a PRD for an admissions counseling or educational consulting AI system. They need to know which one screen matters most and how to build it. This skill reads the PRD, applies a valuable-story filter (with admissions-specific gate criteria), picks **one UI pattern**, and writes **`GUIDELINE.md`** into the repo.

Use when:
- User brings a PRD (file path, pasted text, URL) for an admissions/consulting system and wants to start building
- Team has too many stories — needs to pick the highest-value admissions interaction first
- PRD exists for a counseling platform but there's no UI plan yet

If the user has only a vague idea (no PRD yet), route to `/ui-pattern` instead.

## What it writes

**One file:** `<repo-root>/GUIDELINE.md`

- UI pattern choice + why (admissions framing)
- Visual style
- User flow (3 steps, admissions roles)
- T·C·R checklist for this pattern (admissions-specific)
- Hinge rule (`src/llmService.js`)
- What NOT to build yet (admissions-specific deferrals)

## The 7 UI patterns — admissions domain mapping

Full reference: `./references/archetypes.md`. Every screen in an admissions/counseling AI maps to one:

1. **Chat + context panel** — student or counselor asks a question; AI answers with match scores, citations, checklists, or ranked programs visible in the panel.
2. **Upload → dashboard** — student uploads transcript/CV/test scores → AI extracts structured profile → dashboard shows completeness, strengths, school fit.
3. **Query → structured result** — NL question → filterable table of programs or student cohort. Text-to-filter, program comparison charts.
4. **Wizard + inline audit** — student profile builder or application checklist, AI pre-fills each field from documents and checks against program requirements.
5. **Draft → approve → send** — AI drafts personal statement / recommendation letter / admission email → counselor or student approves → irreversible send.
6. **Queue + approval** — batch of AI-flagged student cases, counselor clears queue (approve, escalate, request more info).
7. **Real-time streaming** — live voice advising session, real-time essay feedback as student types, live mock interview transcription.

## Flow

```
STEP 1   Load PRD (path, pasted, or URL).
STEP 2   Read ./references/archetypes.md.
STEP 3   Extract candidate stories. Apply valuable-story filter (Gates A/B/C — admissions adapted).
STEP 4   If >1 story survives, AskUserQuestion to pick the first one to ship.
         If 1 survives, skip.
         If 0 survive, surface the problem.
STEP 5   Ask UI style (AskUserQuestion, 4 options).
STEP 6   Map story → UI pattern (admissions decision table).
STEP 7   Write GUIDELINE.md. Hand off.
```

Total user interaction: 1–2 `AskUserQuestion` popups max.

---

## STEP 1 — Load PRD

Input forms:
- Path → `Read` it
- Pasted text → use as-is
- URL → fetch with `WebFetch`
- Nothing → ask once in the user's language, e.g. "Paste the PRD or give me a path." / "Dán PRD hoặc cho mình đường dẫn."

Extract silently:
- **App slug** — from PRD title, lowercase-hyphenated (e.g. `admissions-counselor`, `program-matcher`, `student-profile-builder`)
- **Language** — detect from PRD + user's messages (EN / VN / mixed / other). Drives all user-facing prompts + GUIDELINE.md prose. Code identifiers stay English.
- **Primary actor** — is it the student, the counselor, or both? If both, which is Demo 1?
- **Domain sub-type** — undergraduate admissions, graduate admissions, scholarship matching, transfer counseling, international student advising, or general educational consulting
- **Data grounding** — is the app grounded on a real school database / corpus (RAG), or using mock/static data?

If PRD is long-form with strategy sections, skim for Personas / User Stories / Use Cases / Features. Skip market sizing.

## STEP 2 — Read local references

Read `./references/archetypes.md` into context. This has the 7 pattern definitions + per-pattern Stage 0 / +T / +T+C / +T+C+R surfaces + traps.

If the file is missing, STOP and tell the user. Don't hallucinate pattern content from memory.

## STEP 3 — Apply the valuable-story filter (admissions-adapted)

List every user story in the PRD (explicit "As a X, I want Y" AND implicit ones in Feature / Use Case lists). A story survives only if it passes all three gates:

### Gate A — Core admissions loop, not admin CRUD

Drop: user management, login, role/permission setup, data import pipelines (unless pattern 2), admin dashboards for managing the counseling platform itself, analytics about the counseling system.

Keep: the thing the student or counselor does to get the value the PRD promised. The moment AI is doing work a human couldn't do alone at scale — matching students to programs, reviewing documents, screening a queue of applicants, drafting a personal statement.

**Admissions Gate A examples:**
- KEEP: "Student asks about their fit for a program → AI returns match score + key criteria breakdown"
- KEEP: "Counselor reviews AI-flagged at-risk students and decides who gets a session"
- DROP: "Admin configures which schools are in the database"
- DROP: "User changes their password"

### Gate B — Visible AI hand-off

Drop: no AI in the loop, or AI is only backend with no user-visible moment.

Keep: student asks / uploads / speaks → AI processes → user sees AI output. This is the pattern trigger.

**Admissions Gate B examples:**
- KEEP: Student uploads transcript → AI extracts GPA, test scores, subject strengths → student sees structured profile
- KEEP: Counselor asks "which students need attention this week?" → AI ranks and reasons → counselor sees ranked list with reasoning
- DROP: Counselor manually enters student data into a form (no AI hand-off)
- DROP: System sends automated reminder emails on schedule (no visible AI reasoning)

### Gate C — Failure mode worth designing R for

Drop: failures are impossible (static content) or silent (cached lookup). Every error is "retry the form".

Keep: AI can be wrong, slow, or unavailable, AND the user needs a visible recovery path. Wrong output has cost.

**Admissions Gate C examples:**
- KEEP: AI match score is wrong → student applies to schools they're not competitive for. Cost: wasted application fees, missed deadlines.
- KEEP: AI-drafted personal statement contains hallucinated facts about the student. Cost: submitted to schools with false information.
- KEEP: AI fails to flag an at-risk student → counselor doesn't schedule a session → student misses a deadline. Cost: missed application cycle.
- DROP: AI returns a slightly wrong program ranking on a "which school should I look at?" query. Cost: low, user can re-ask.

**Admissions-specific R concern:** any AI output that directly influences an irreversible action (submitting an application, sending an email to an admissions office, finalizing a personal statement) MUST have recovery designed in. Flag these stories as high-priority.

## STEP 4 — Narrow to the one story to ship first

All prompts in the user's language (detected in STEP 1).

- If exactly 1 story survived: skip, proceed with it.
- If ≥2 survived: use `AskUserQuestion`:
  > "N stories passed the filter. Which one ships first?"
  > Options: [survivor numbers + one-line each]
  
  **Admissions tiebreaker hint:** when two stories are equally valuable, prefer the one that involves the primary student-facing interaction over the counselor-facing one. The student chat / profile builder is usually more foundational — counselor tools build on top of it.

- If 0 survived: use `AskUserQuestion`:
  > "No story passed the filter. PRD is heavy on {admin CRUD / missing AI hand-off / no failure case}. What now?"
  > Options:
  >   - "Loosen Gate C (drop the R requirement) to surface 1–2 stories"
  >   - "PRD isn't ready — send back to author"
  >   - "Other"

## STEP 5 — Pick UI style

Always ask — translate to user's language:

> `AskUserQuestion`
> "UI style direction for this admissions app?"
> - "Minimal clean — professional, Linear / Notion feel, lots of whitespace"
> - "Playful educational — bright accents, rounded corners, approachable for students"
> - "Data-dense professional — compact, dashboard feel for counselors"
> - "Just functional — inline styles, unpolished, demo-grade"

## STEP 6 — Map story to UI pattern

Apply in order, first match wins:

| If the story's core UX moment is… | UI pattern |
|---|---|
| Student or counselor types a question, AI answers with match scores / citations / checklist visible | 1 Chat + panel |
| Student uploads transcript / CV / test scores, waits, sees structured profile or insight tiles | 2 Upload → dashboard |
| User types a question, AI produces a filterable program table or cohort chart (not prose) | 3 Query → structured |
| Student fills multi-step profile or application checklist, each field AI-checked against requirements | 4 Wizard + audit |
| AI drafts personal statement / letter / email, counselor or student approves, system sends | 5 Draft → approve → send |
| Counselor processes batch of AI-flagged student cases (approve / escalate / request info) | 6 Queue + approval |
| Student or counselor speaks / streams, AI responds <1s, can interrupt (live advising session) | 7 Real-time streaming |

**Admissions borderline cases:**
- Chat that returns a ranked school list → pattern 1 (output is prose + panel data, not a pure interactive chart)
- Profile wizard that ends with "AI drafts statement → counselor approves → sends to school" → pattern 5 (irreversible send dominates)
- Student asks "compare GPA requirements for CS programs" → pattern 3 (output is a comparison table, not prose)
- Upload that returns a chat-style Q&A advisor, not a dashboard → pattern 1 (with uploaded file as context), not pattern 2

Never fuse two patterns on one screen. If two actors need two screens (student + counselor), pick the primary actor's screen and note the second is out of scope for now.

## STEP 7 — Write GUIDELINE.md

Write to `<repo-root>/GUIDELINE.md`. Warn + show diff if exists.

```markdown
# GUIDELINE — {app name}

> PRD: see {path or "pasted, saved to PRD.md"}

## UI pattern
**{N}. {pattern name}**

Why this pattern: {1–2 lines tying the student/counselor story to the pick — admissions-specific framing}

{If pattern 1: add Conversational UI + Evidence Panel note.
For admissions apps, the panel payload choices are:
- panel = match scores → AI-estimated fit per program. MUST label as "AI estimate — verify with official sources." If no real school corpus, this is a logic-based score, not a retrieval result.
- panel = citations → RAG on school handbooks / program pages. Label: "Source: [school name] admissions page".
- panel = checklist → live requirements check per program (GPA cutoff, test score, deadlines). Label: "Requirements status".
- panel = ranked list → top program recommendations with rationale.
- panel = student profile summary → counselor sees student context while chatting.
Never invent acceptance rates or requirements. If no real corpus, say "AI-estimated fit" and link to official sources.}

## Visual style
{Minimal clean / Playful educational / Data-dense professional / Just functional — from STEP 5}

Concrete rules:
- {4–5 bullets specific to this style and the admissions context}

## User flow (3 steps)
1. {Student/Counselor} {input action — admissions-specific, e.g., "types 'Am I competitive for MIT CS?' into the chat input"}
2. App {AI processing — name the LLM call, what it receives, what it returns — e.g., "sends question + student profile context to src/llmService.js → returns {answer, match_score, checklist_items[], disclaimer}"}
3. {Student/Counselor} {interacts with output — e.g., "reads answer on the left, sees match score (67/100 · AI estimate) and requirements checklist on the right panel"}

{If two roles (student + counselor): add a second flow block for Demo 2.}

## T·C·R checklist for this pattern

### T — Transparency (what AI work is visible)
- [ ] {pattern-specific T item — use admissions language, e.g., "match score shown with 'AI estimate' disclaimer" or "extraction confidence shown per profile field"}
- [ ] {T item 2}
- [ ] {T item 3}

### C — Control (what user can stop / edit / override)
- [ ] {pattern-specific C item — e.g., "counselor can override AI recommendation with a reason field" or "student can manually correct extracted transcript field"}
- [ ] {C item 2}
- [ ] {C item 3}

### R — Recovery (validation + retry + undo)
- [ ] {pattern-specific R item — e.g., "error bubble with retry on LLM fail, preserves student question in state" or "undo last counselor decision (10-action stack)"}
- [ ] {R item 2}
- [ ] {R item 3}

**Admissions honesty rule:** AI match scores, program rankings, and eligibility assessments must be labeled as AI-generated estimates, never as official data. If the app has no real admission corpus, display: "AI-estimated fit — verify with official sources." Never invent acceptance rates, requirements, or deadlines.

## Hinge rule
All LLM calls go through `src/llmService.js` (or the equivalent file named in PRD §Tech stack). UI never imports a provider SDK directly. Swap providers = edit one file.

## What NOT to build yet
- {features from PRD that aren't the valuable story — admin console, auth beyond mock, real school database integration, payment/subscription for premium counseling}
- T·C·R features come in sequence, not all at once. Baseline first, then layer T → C → R.
- {admissions-specific traps to avoid:}
  - Don't surface AI acceptance rate predictions without clearly labeling them as estimates
  - Don't auto-send any document or communication without a mandatory human review step (pattern 5 rule)
  - Don't build the counselor dashboard before the student-facing core loop is working
  - {pull 1–2 additional traps from references/archetypes.md for the chosen pattern}
```

Fill the T·C·R checklist by reading `./references/archetypes.md` for the chosen pattern — copy, don't invent. Use the admissions-adapted language from the `/ui-pattern` skill's T·C·R matrix.

## STEP 8 — Hand off

Tell the user briefly in their language:

> EN:
> GUIDELINE.md written to repo root. Locked UI pattern {N} ({name}) for story: {1-line admissions framing}.
>
> Claude Code has enough context to plan + build baseline. Once baseline runs, run `/tcr-apply` to layer T·C·R.

> VN:
> Xong GUIDELINE.md ở repo root. Chốt UI pattern {N} ({name}) cho story: {1-line}.
>
> Claude Code có đủ context để plan + build baseline. Khi baseline chạy được, chạy `/tcr-apply` để layer T·C·R.

Stop there. Do NOT tell the user to "open a fresh session" or reveal this is a scripted flow.

---

## Anti-patterns — do NOT do these

- **Don't write PRD.md.** The user brought a PRD. If they pasted text, save it verbatim as PRD.md and reference it. Don't restructure.
- **Don't invent a stack.** GUIDELINE references PRD for stack. If PRD doesn't specify, ask once.
- **Don't pick 2+ patterns.** One story, one pattern, one screen.
- **Don't write build prompts.** The skill's job ends at GUIDELINE.md.
- **Don't invent school data.** If no corpus, use mock and label AI estimates honestly. This is load-bearing for admissions AI.
- **Don't build the counselor dashboard first** if the student-facing core loop isn't validated — the counselor tool has no value without student data flowing through it.
- **Don't skip the admissions honesty rule** in the T·C·R checklist. Every pattern in this domain needs a disclaimer on AI-generated estimates.
- **Match the PRD's language** for user-facing strings. Code stays English.

## Principles

- **One story, one pattern, one GUIDELINE.** The filter cuts to the screen that matters most — in admissions, usually the student-facing AI interaction.
- **Skill records, doesn't invent.** PRD's stack, constraints, and school data scope go into GUIDELINE verbatim.
- **Baseline before T·C·R.** GUIDELINE lists T·C·R as a checklist, not as things to build in Prompt 0.
- **Admissions honesty is non-negotiable.** Any AI output that influences an irreversible admissions action must have transparent labeling and human review.
- **Match the PRD's language.** UX strings follow the PRD. Code stays English.
