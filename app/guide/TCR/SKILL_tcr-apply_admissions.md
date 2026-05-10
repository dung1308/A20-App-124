---
name: tcr-apply
description: "Apply T-C-R pattern to an existing AI app UI in the Smart Educational Consultant / Admissions Counselor domain. Detects UI pattern from code, generates 3 follow-up prompts (Transparency, Control, Recovery) tailored to what's already built. Use when student says 'thêm T-C-R', 'apply tcr', 'tcr apply', 'làm UX tốt hơn', 'retrofit ux pattern', 'upgrade chat to have sources panel', 'add transparency', 'add confidence score', 'show AI reasoning', 'add undo/retry', or anytime they want to layer T-C-R on a baseline admissions/counseling app. Also trigger after a working MVP is demoed and student asks 'tiếp theo làm gì để UX tốt hơn'."
---

# TCR Apply — Retrofit T-C-R onto existing UI
# Domain: Smart Educational Consultant / Admissions Counselor AI

Student already has a working baseline (chat advisor, student queue, profile wizard, document drafter — anything in the admissions/counseling domain). This skill reads the code, guesses which of the 7 UI patterns it matches, and hands back 3 copy-paste prompts — **Prompt T** (Transparency), **Prompt C** (Control), **Prompt R** (Recovery) — tailored to the code on disk and the admissions context.

The goal is not to rewrite the app. The goal is to layer T-C-R **additively** so the student feels the pattern click in the admissions domain.

## What this skill does

1. Reads the repo — finds the key UI file(s) and guesses the UI pattern
2. Generates 3 short, additive prompts (T, C, R) tailored to the admissions/counseling context
3. Explains *why* each prompt was chosen for this UI pattern

## When to use it

Student has a demo that runs. They say "bây giờ em muốn thêm T-C-R" / "UX còn thô" / "retrofit theo pattern workshop". Run `/tcr-apply` from the repo root.

## T-C-R definitions (admissions-adapted)

- **T = Transparency.** Show the user what the AI is doing — and what the AI can and can't claim. In admissions: match score with "AI estimate" label, extraction confidence per profile field, sources from school handbooks (if RAG), checklist status per program requirement. Status lines ("Checking requirements…", "Analyzing your profile…"). Critical: **never display AI estimates as official statistics.**
- **C = Control.** User can stop, edit, override before the AI acts irreversibly. In admissions: stop button, edit-last-question, manual correction of AI-extracted profile fields, counselor override of AI recommendation with required reason, "save as draft" before any send. Mandatory preview step before any document is sent.
- **R = Recovery.** Pre-flight validation + post-hoc retry + undo. In admissions: validate student profile completeness before sending to AI, retry button on LLM fail (preserve question/context), undo last counselor queue action (undo stack of 10), "flag as uncertain" instead of outright reject, keep draft intact on send failure.

**Admissions-specific R concern:** any AI output that influences an irreversible admissions action (submitting application, sending email to school, finalizing personal statement) needs hard-confirm + undo or cancel window. Design R for the high-stakes path first.

If a prompt you generate doesn't obviously map to one of T / C / R, rewrite it until it does.

## Step 1: Detect the UI pattern

Read the repo. Look for the main UI file. Match against this table (admissions signals added):

| UI pattern | Signals in code | Typical files |
|---|---|---|
| 1. Chat + context panel | `message`, `chat`, `thread`, `useChat`, `role: "user"`, `role: "assistant"`, advisor Q&A, `match_score`, `program_fit`, `st.chat_message` | `chat.tsx`, `AdvisorChat.jsx`, `counselor.py` |
| 2. Upload → dashboard | `upload`, `fileInput`, `FormData`, `multer`, `st.file_uploader`, transcript/CV parsing, `extractGPA`, `parseTranscript` | `upload.py`, `ProfileDashboard.tsx`, ingestion code |
| 3. Query → structured result | `query`, `filter`, `programSearch`, chart/table render, `st.dataframe`, `recharts`, `comparePrograms` | `ProgramSearch.tsx`, `cohort_query.py` |
| 4. Wizard + inline audit | Multi-step profile form, step indicator, `currentStep`, `wizard`, `stepper`, requirement check per field, `meetsRequirement` | `ProfileWizard.tsx`, `ApplicationChecklist.jsx` |
| 5. Draft → approve → send | `draft`, `approve`, `send`, `personalStatement`, `recommendationLetter`, `POST /send`, destination (email/school API) | `DocumentDraft.tsx`, `StatementEditor.jsx` |
| 6. Queue + approval | Array of students + approve/escalate/request buttons, `pending`, `review_queue`, `counselorQueue`, `flaggedStudents` | `CounselorQueue.tsx`, `student-review-list.tsx` |
| 7. Real-time streaming | `stream`, `eventsource`, `SSE`, `audio`, `transcription`, `on_chunk`, live essay feedback, voice advising | `LiveAdvisor.tsx`, `EssayStream.ts` |

Fallback: if nothing matches, print the 7 names with admissions examples and ask which fits best.

### Pattern transfers wider (important insight)

Chat + context panel is **"Conversational UI + Evidence Panel."** In admissions, swap the panel payload:

- panel = **match scores** → program fit advisor
- panel = **checklist status** → requirements tracker alongside chat
- panel = **citations from school handbook** → RAG-grounded school Q&A
- panel = **ranked program list** → school recommendation chat
- panel = **student profile summary** → counselor context panel while chatting with student

When detected pattern is Chat + panel, always add this note:

> Your baseline is also adaptable to: match-score panel (program fit), checklist panel (requirements tracker), citations panel (RAG school handbook), ranked-list panel (recommendations). Same shell, swap the panel payload.

## Step 2: Generate the 3 prompts

**Language rule:** detect the app's existing UI language (button labels, placeholder text, copy in JSX) and match it. If app is in English, use English. If Vietnamese, use Vietnamese. If `GUIDELINE.md` exists (written by `/ui-pattern`), read it for language + trust signal type.

**Admissions honesty rule — applies to every Prompt T you write:** if the app has no real school corpus, the trust signal must be labeled as an AI estimate, not as official data. Insert the appropriate label in the prompt: `"AI-estimated fit — verify with official sources"` or `"Điểm phù hợp do AI ước tính — hãy kiểm tra với nguồn chính thức"`.

---

### UI pattern 1 — Chat + context panel (Student/Counselor Advisor)

> **Before generating prompts:** Read `GUIDELINE.md` if it exists. Pick the trust signal type from there (match scores / citations / checklist / ranked list). If no GUIDELINE, ask the user one question to pick before writing Prompt T.
>
> **Honesty rule:** If app has RAG / real school corpus → show real source citations. If no retrieval → do NOT fake citations. Use match scores, checklist status, or program tags instead — and label them honestly ("AI-estimated fit"). Never show invented acceptance rates or requirements as facts.

**Prompt T (Transparency):**
> Add Transparency features. Build a two-column layout: chat left (~60%), context panel right (~40%). For each AI message, the panel shows 1–2 honest trust signals appropriate for this admissions app — choose what fits: match score (if logic-based, label as "AI-estimated fit · X/100"), source citations (if RAG on school corpus, label as "Source: [school name] admissions page"), checklist status (requirements met/borderline/missing per program), or ranked program list with brief rationale. Traffic-light color coding for match scores (green ≥70 / yellow 40–69 / red <40) or requirement status (✓/⚠/✗). Include a streaming status line ("Checking requirements…", "Analyzing your profile…"). If switching to JSON output from the LLM, update `src/llmService.js` to request structured output with the shape this app needs (e.g., `{answer, match_score, checklist_items[], disclaimer}`). Additive only — no refactor of existing chat.

*Why:* Students can't tell if AI advice is grounded in real data or guessed. Visible match scores + honest labels build trust. The admissions honesty rule is load-bearing: a hallucinated acceptance rate shown as fact could mislead a student's entire application strategy.

**Prompt C (Control):**
> Add Control features. (1) Stop button visible during loading — use AbortController to cancel in-flight fetch. On abort, render a neutral placeholder. (2) Flag / "This seems wrong" button under each AI message — opens inline form for student or counselor to say what was incorrect. Submit → persist to storage (new endpoint or in-memory log). Show "Reported" badge after submit. (3) Edit-last-question: hover last user turn → edit icon → click to edit and resubmit without retyping. (4) If the app shows match scores, add a "Why this score?" button that requests reasoning from the LLM service and shows it inline. Additive only.

*Why:* Students need to correct AI advice that doesn't fit their situation. The flag mechanism creates a low-friction correction loop. "Why this score?" is especially important in admissions — a student who can see the reasoning can fact-check it and build their own judgment.

**Prompt R (Recovery):**
> Add Recovery features. (1) Wrap the LLM service call in try/catch. On error: render an error bubble with error message + retry button. Store the last user message in state BEFORE the failing request so retry can resubmit it. (2) Pre-flight: if student's profile data (GPA, test scores, intended major) is missing and the question requires it (e.g., "Am I competitive for Harvard?"), show an inline nudge: "Add your GPA and test scores to your profile for a more accurate answer" — warn, don't block. (3) No automatic retry — user clicks retry. Do not modify the success path.

*Why:* Admissions advice without student context produces generic answers. The profile nudge — warn, don't block — respects autonomy while improving answer quality. Manual retry keeps the student in control.

---

### UI pattern 2 — Upload → dashboard (Transcript / Document Ingestion)

**Prompt T:**
> Add Transparency. After upload, show a progress panel with stepped status: "Parsing file… Extracting GPA… Extracting test scores… Analyzing subject strengths… Done." Check each step as it completes. For each extracted field on the profile dashboard, show the source location (e.g., "GPA: 3.85 · from page 1, transcript column 3") and an extraction confidence indicator (high/medium/low). If any field failed to extract, show a "Could not extract — enter manually" state with an editable input. Additive only.

*Why:* Students need to trust that the AI read their documents correctly. Showing source location + confidence turns the profile from "trust me" into "I can verify this." Wrong extracted GPA = wrong school recommendations = real harm.

**Prompt C:**
> Add Control. During processing, show a "Cancel" button — aborts the fetch + clears pending state. After extraction, make every extracted field editable — student can correct AI mistakes inline. Add a "Re-analyze" button per field that re-runs extraction for that field only. Before running analysis on a large file (>5MB or >10 pages), show a preview: "This will process N pages and extract M fields — Continue or Cancel?" Additive only.

*Why:* AI extraction errors on transcripts are common (especially non-standard formats). If the student can't correct the extracted GPA, the entire downstream experience is wrong. Control here is not optional.

**Prompt R:**
> Add Recovery. Pre-flight: reject unsupported file types (non-PDF, non-image) with a clear error and file format guidance. On extraction failure: show "Extraction failed — try re-uploading or enter fields manually" with a manual entry form as fallback. Keep the previously successfully extracted profile if a new upload fails. If partial extraction (some fields succeed, some fail), show exactly which succeeded and which need manual entry.

*Why:* Transcript parsing fails on scanned documents, non-Latin scripts, and unusual layouts. A graceful manual fallback means the student can still use the app even when AI extraction fails.

---

### UI pattern 3 — Query → structured result (Program Search / Cohort Filter)

**Prompt T:**
> Add Transparency. Above the results table or chart, show the generated filter criteria in plain language: "Showing programs where: GPA requirement ≤ 3.5 · major includes CS · country = US · admission rate data available." Confidence badge on the result ("All N fields matched" / "2 of 4 criteria had low confidence"). Meta line: "N programs found · query time X ms · data as of [date]". Add a disclaimer if data is mock/static: "Program data is for demo purposes — verify with official sources."

*Why:* Students need to know whether the filter correctly understood their question. In admissions, a wrongly interpreted query ("schools with good CS" → "schools with any CS program") can produce a misleading list.

**Prompt C:**
> Add Control. Show the generated filter as editable chips above results — student can remove or modify a chip and re-run without retyping. Add a "View as table / View as chart" toggle. Program list includes an "Add to my list" action per row. If the query could affect school-specific data (rare in a read-only search), confirm before executing. Enter/Esc shortcuts on the query input.

*Why:* Students often want to tweak one filter without redoing the whole query. Editable chips make refinement fast and keep the student in control of what they're actually searching for.

**Prompt R:**
> Add Recovery. Retry on LLM fail. "Rephrase question" button feeds the error + original query back to the LLM with a prompt to self-correct the filter. Timeout guard (15s via `Promise.race`). If zero results, show why (which criterion was most restrictive) and suggest relaxing it. Query history (last 5) accessible via dropdown.

*Why:* Zero-result queries are common in admissions search when students set strict criteria. Explaining which criterion filtered everything out saves the student from thinking the app is broken.

---

### UI pattern 4 — Wizard + inline audit (Student Profile Builder / Application Checklist)

**Prompt T:**
> Add Transparency. For each field or step, show an inline status indicator: ✓ (meets requirement) / ⚠ (borderline) / ✗ (below cutoff) with the specific requirement shown: "TOEFL: your score 92 · minimum required 100 · ⚠ borderline." The requirement reference should name the source: "per [School Name] 2024 requirements." Header summary: "N requirements met · M borderline · K missing." For AI-pre-filled fields, show a small "AI pre-filled" badge and the confidence ("Extracted from uploaded transcript · confidence: high").

*Why:* Students need to see exactly which requirement they're failing and why. A ✗ with no explanation is anxiety-inducing and useless. Naming the source also lets the student go verify it.

**Prompt C:**
> Add Control. Back/forward navigation between wizard steps without data loss. Save draft button visible at all times — persist to localStorage or server. For AI-pre-filled fields, add "Regenerate this field" button (re-extracts from uploaded document) without touching other fields. "Override" checkbox per requirement check with a required reason textbox ("I have additional coursework not shown on transcript"). Additive only.

*Why:* Students fill out profiles over multiple sessions. Auto-save + back/forward is non-negotiable. The override with reason creates an audit trail — important if a counselor later reviews the profile.

**Prompt R:**
> Add Recovery. Submit disabled while any ✗ field exists — tooltip lists each one. Autosave banner ("Draft saved 5 seconds ago"). If regeneration of one field fails, show error for that field only — don't wipe others. Block submission if any required field is empty. Before final submit, show a summary card of all answers with "Edit" jump-backs per section.

*Why:* In admissions, a submitted profile with missing or wrong data can propagate errors into every downstream recommendation. Blocking submit on ✗ fields is the right call here — unlike most wizards, the cost of wrong data is high.

---

### UI pattern 5 — Draft → approve → send (Personal Statement / Letter / Email)

> **Critical:** This pattern involves irreversible sends. Every prompt in this pattern must preserve the mandatory human review step. Do not generate any prompt that enables "generate and auto-send" without counselor/student approval.

**Prompt T:**
> Add Transparency. In the draft view, show AI confidence per section (introduction, body, conclusion) and flag any sections that contain information not found in the student's profile ("⚠ This claim could not be verified against your uploaded profile — please confirm it's accurate"). Show a diff vs. last saved draft (+ green, - red). Before send, show a meta panel: recipient (school name + admissions email), document type (personal statement / recommendation / email), word count, generation meta ("Generated from profile fields: GPA, extracurriculars, intended major · model: claude-sonnet · {date}"). Add disclaimer: "AI-drafted — review carefully before submission."

*Why:* A personal statement with hallucinated facts (clubs the student didn't join, scores they don't have) is a serious problem. The "could not verify" flag gives the student a last chance to catch errors before submission.

**Prompt C:**
> Add Control. Force a preview step before send — no "generate & send" in one click. Allow editing any section in preview. Template-locked fields (school name, program name, deadlines) show a lock icon — editing requires clicking "Unlock" with a confirmation. Add "Save as draft instead of send" button. If counselor-reviewed app: add "Request counselor review" button that puts the draft in the counselor queue before sending. Keyboard: Cmd+Enter = send (requires preview step to have been shown), Esc = back to edit.

*Why:* The #1 failure in admissions doc tools is sending to the wrong school or with wrong content. Forced preview + locked fields prevent the most common mistakes.

**Prompt R:**
> Add Recovery. Send behind hard confirm: show a modal asking the student/counselor to type the school name or the word "SEND" / "GỬI" before dispatching. After send, show an "Undo" toast with a 10–30s window to cancel (if the send is queued, not instant). If send fails, keep the draft intact and show the error with a retry button. Log all sends in a "Sent documents" list with status (sent / failed / pending). If a draft contains flagged sections (from Prompt T), warn before allowing send.

*Why:* Submitting a personal statement is one of the most consequential actions in a student's life. Hard confirm + undo window + sent log are non-negotiable here.

---

### UI pattern 6 — Queue + approval (Counselor Student Review Dashboard)

**Prompt T:**
> Add Transparency. Each student card in the queue shows: confidence dot (green: AI-confident assessment / yellow: borderline / red: needs human attention), one-line AI reasoning ("Flagged: GPA 2.9 · below minimum for all selected schools"), and the date/time of the flag. At the top of the queue, show counts: N pending · M high-confidence (auto-approvable) · K borderline (need review). Sort: low-confidence bubbles up within urgency tier. If a student's deadline is within 14 days, show a red deadline badge.

*Why:* Counselors managing many students need to triage fast. Confidence + deadline badges let them scan the queue and decide in seconds who needs immediate attention.

**Prompt C:**
> Add Control. Bulk-select checkboxes + shift-click range. Filter toolbar: by AI flag reason, by school, by confidence threshold, by upcoming deadline. "Select all borderline (yellow)" shortcut. Bulk actions: Schedule session / Request more info / Escalate to senior counselor. Per-student override: counselor can change AI assessment category with a required reason (text field). Keyboard shortcuts: J/K = next/prev student, A = approve/schedule, R = request info, U = undo last action, E = escalate.

*Why:* A counselor queue without keyboard + bulk is unusable at scale. The mandatory reason for override creates an audit trail — important for accountability in an admissions context.

**Prompt R:**
> Add Recovery. Every action creates an undo toast with a 10s window. Undo stack of 10 actions. "Request more info from student" as an alternative to reject — sends a predefined info-request form to the student (or logs it for manual follow-up) and holds the case in a "Waiting" state. If a student updates their profile after being reviewed, re-surface the case with a "Profile updated — re-review?" badge. Classification-failed cases (AI couldn't assess) show a distinct "Manual review required" marker and sort to the top.

*Why:* Counselors misclick under time pressure. Undo + "request info" (instead of outright reject) protects students from being incorrectly dismissed. Re-surfacing on profile update ensures no student falls through the cracks.

---

### UI pattern 7 — Real-time streaming (Live Voice Advising / Real-time Essay Feedback)

**Prompt T:**
> Add Transparency. Show live status ("Listening…", "Transcribing… (N sec)", "Analyzing response…"). Stream partial output token-by-token. For essay feedback mode: underline low-confidence suggestions (dashed line, lower opacity) — hover to see alternatives. Meta bar: model · latency ms · session duration. If the AI reaches a question it can't answer with confidence, show: "I'm not certain about this — I recommend verifying with [school name]'s official admissions page."

*Why:* In a live advising session, silence = broken app. Visible status keeps the student oriented. The "I'm not certain" signal is critical in admissions — live AI advice can be wrong, and the student needs to know when to verify.

**Prompt C:**
> Add Control. Stop button (stop listening / stop stream) — aborts fetch or WebSocket connection. Allow pause/resume for transcription sessions. "Switch to text" fallback swaps to chat UI without losing session context. Keyboard: Space = pause/resume, Esc = stop, T = switch to text mode.

*Why:* Students in a live session need instant control. An open mic that can't be stopped is uncomfortable and untrustworthy.

**Prompt R:**
> Add Recovery. If stream disconnects, auto-reconnect up to 3 times, show "Disconnected · Reconnecting (N/3) · Hold on". Preserve the full transcript buffer on reconnect — append, don't reset. Add a "Restart session" button that clears and starts cleanly. Permission-denied (mic/camera) falls back to text mode gracefully with a clear "Mic not available — switching to text" message.

*Why:* Network hiccups happen. A reconnected session that loses the conversation is worse than a dropped call. Preserved buffer + graceful text fallback keeps the advising session salvageable.

---

## Step 3: Output format

Print this, nothing else:

```
━━━ TCR Apply — UI pattern detected: {UI pattern name} ━━━

Evidence: {1-2 lines of what files/code patterns led to this guess}

{If pattern 1, include the "Pattern transfers wider" note with admissions panel options}

━━━ Prompt T (Transparency) ━━━
{prompt text in a code block}

Why: {1-2 sentences — admissions-specific reasoning}

━━━ Prompt C (Control) ━━━
{prompt text in a code block}

Why: {1-2 sentences — admissions-specific reasoning}

━━━ Prompt R (Recovery) ━━━
{prompt text in a code block}

Why: {1-2 sentences — admissions-specific reasoning}

━━━ How to use ━━━
Paste 1 prompt at a time into Claude Code. After each one: review the diff, test in browser, commit. Then paste the next. Don't paste all 3 at once — T-C-R compound when added in sequence.

━━━ Admissions honesty reminder ━━━
Any AI output that influences an irreversible action (submitting an application, sending a document to a school) must have: (1) an "AI-generated" label, (2) a mandatory human review step before send, and (3) a hard confirm + undo window. Check Prompt R covers this if your app has a send action.
```

## Anti-patterns — do NOT do these

- **Don't rewrite from scratch.** Every prompt must be additive.
- **Don't bundle T+C+R into one prompt.** Sequential paste-review-commit is the point.
- **Don't fake school data.** If the app has no real corpus, the trust signal must be an AI estimate, labeled honestly. Generating a prompt that displays hallucinated acceptance rates as facts violates the admissions honesty rule.
- **Don't skip the mandatory review step for pattern 5.** Never generate a prompt that enables "generate and auto-send" without human approval — this is non-negotiable in admissions.
- **Match the app's existing UI language.** English app → English strings. Vietnamese app → Vietnamese strings.
- **Don't skip the "Why."** The reasoning builds the mental model.
- **Don't prescribe a specific component library.** Say *what*, not *which npm package*.
- **Don't guess the pattern silently.** If signals are weak, ask. Wrong pattern = wrong prompts.

## Principles

- **Additive, not transformative.** Same app + 3 focused admissions-aware upgrades.
- **One pattern, 3 prompts.** Pick one, commit.
- **Admissions honesty is load-bearing.** Every Prompt T in this domain must enforce honest labeling of AI estimates. Every Prompt R for a send action must include hard confirm + undo.
- **Copy-paste ready.** If the student has to edit the prompt before pasting, you failed.
- **Match the app's language.** Read existing UI strings and mirror the language.
