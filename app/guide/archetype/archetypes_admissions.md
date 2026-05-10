---
type: skill-reference
skill: prd-to-screens
purpose: The 7 AI-app UI patterns adapted for Smart Educational Consultant / Admissions Counselor AI systems. Per-pattern Stage 0 / +T / +T+C / +T+C+R surfaces + traps — with admissions-specific examples and an additional honesty rule for AI-generated admissions data. The skill reads this to fill GUIDELINE.md.
---

# The 7 UI patterns — Admissions Counselor AI reference card

Teaching order: simplest → most complex. Every screen in an admissions or educational consulting AI maps to exactly one.

> When filling GUIDELINE.md, **copy the pattern structure** (Stage 0 shape, what +T/+C/+R add, the traps) and **use admissions-specific examples**. Don't paste illustrative strings verbatim — adapt to the user's specific app (school type, student type, counselor workflow).

> **Admissions honesty rule (applies to every pattern):** AI match scores, acceptance probability estimates, program rankings, and requirements checks must be labeled as AI-generated estimates unless the app is grounded on verified, official school data. Default label: *"AI-estimated — verify with official sources."* This rule is non-negotiable and appears in the T layer of every pattern below.

---

## 1 · Chat + Context Panel

**Shape:** single chat bubble stream + evidence panel (match scores, citations, checklist, ranked programs).
**Core UX problem in admissions:** students can't tell if AI advice is grounded in real school data or guessed. A confident-sounding answer about acceptance rates that's actually hallucinated is worse than no answer.
**Production refs:** Perplexity (for the citation model), any RAG-based school search tool.

- **Stage 0:** single-column chat. Student asks "Am I competitive for MIT?". AI answers confidently. No evidence panel. No disclaimer. No visible reasoning. Out-of-scope questions (e.g., visa procedures) get answered with equal confidence anyway.
- **+T:** layout splits ~60/40 — chat left, evidence panel right. Each AI message shows 1–2 honest trust signals:
  - If RAG on real school corpus: "Source: MIT Admissions page · retrieved {date}" with a link.
  - If logic-based scoring (no corpus): "AI-estimated fit: 67/100 · AI estimate — verify with official sources." Traffic-light color: green ≥70 / yellow 40–69 / red <40.
  - If checklist-based: ✓ GPA meets requirement / ⚠ TOEFL borderline / ✗ GRE below cutoff.
  Streaming status line: "Checking requirements…", "Analyzing your profile…".
  Label each signal honestly — never display an AI-estimated score as "MIT acceptance probability."
- **+T+C:** trust signals are interactive (click requirement → see school's official requirement). "Why this score?" button requests reasoning from LLM and shows it inline. Flag/report button under each AI message for student to say what was wrong. Stop button during loading. Edit-last-question.
- **+T+C+R:** out-of-scope questions blocked or flagged ("This is outside my expertise — consult an immigration lawyer") without wiping conversation. try/catch around LLM call → error bubble with retry. Pre-flight: if student profile (GPA, scores) is missing, nudge before answering fit questions — warn, don't block. Network fail preserves conversation.

**Traps:**
1. Agent writes `fetch` directly instead of using `src/llmService.js` (breaks hinge rule).
2. Match score shown as a single number with no label, no disclaimer — student interprets it as official acceptance probability.
3. Out-of-scope block is a modal that wipes the conversation.
4. Retry loses pinned requirements or edit history.
5. Evidence panel shows history of all answers — overwhelms. Show latest only.
6. **Admissions trap:** Fake citations ("Source: Harvard Admissions 2024") when the app has no corpus and is generating the answer from training data. If no retrieval, use logic-based scoring or checklist — never fake sources.

---

## 2 · Upload → Dashboard

**Shape:** file drop → wait → summary tiles/cards derived from uploaded student documents.
**Core UX problem in admissions:** AI transcript/CV parsing fails silently. Student sees a profile with wrong GPA or missing test scores — and doesn't know it's wrong. Every downstream recommendation is then built on bad data.
**Production refs:** Julius AI (document analysis model), any transcript parser tool.

- **Stage 0:** student drops transcript/CV → spinner → 3 profile tiles with extracted data. No progress. No per-field confidence. No source reference. Student can't tell what was extracted from where.
- **+T:** live progress during parsing ("Parsing transcript… page 2 of 4 · Extracting GPA… Done · Extracting test scores… Done"). Each extracted field has a source reference ("GPA: 3.85 · page 1, academic record column · confidence: high") and a confidence indicator. Failed-to-extract fields shown explicitly: "Test scores: Not found — enter manually."
- **+T+C:** all extracted fields are editable — student corrects AI mistakes inline. "Re-analyze this field" button re-extracts from the original file. Before running analysis on a large or complex document (multi-school transcript, foreign-language document), show a preview: "This will process N pages — Continue?" Manual entry form as fallback for any failed field.
- **+T+C+R:** pre-flight file validation (type/size/non-empty — reject non-PDF/non-image with guidance). Partial-success banner: "Extracted 8 of 10 fields · 2 fields need manual entry." Resumable upload on network fail. Keep previous successful extraction if new upload fails.

**Traps:**
1. Progress bar is fake (`setInterval`) not tied to real parse progress — student waits 20s and sees "Done" but half the fields are wrong.
2. Profile completeness metric counts fields that were extracted but wrong (e.g., extracted course titles as GPA).
3. Upload blocks all interaction — student can't browse the dashboard while re-uploading.
4. **Admissions trap:** AI extracts a GPA from a foreign transcript using the wrong scale (4.0 vs 5.0 vs 10.0) and displays it without flagging the ambiguity. Always show the extraction context so the student can verify the scale.
5. "Confidence: high" shown for all fields regardless of actual confidence — defeats the purpose.

---

## 3 · Query → Structured Result

**Shape:** text input → program list / comparison table / cohort chart (not prose).
**Core UX problem in admissions:** generated filter criteria can misinterpret the student's question. "Good CS programs in the US" → filters for "CS department exists" rather than "CS ranking top 50." Student sees a misleading list and doesn't know the filter was wrong.
**Production refs:** program search tools, counselor cohort analytics dashboards.

- **Stage 0:** search input + Run → table of programs or student list appears. No filter criteria visible. No confidence. No raw data access. No explanation of why these results appeared.
- **+T:** filter criteria shown above results in plain language: "Showing programs where: GPA req ≤ 3.5 · major includes CS · country = US · data from 2024." Confidence/clarity badge ("All criteria matched" / "2 of 4 criteria had uncertain interpretation"). Meta line: "N results · query time X ms · data as of {date}." Disclaimer if mock data: "For demo purposes — verify with official sources."
- **+T+C:** filter criteria shown as editable chips — student removes or modifies a chip and re-runs. Query history (last 5 via dropdown). Confirm modal for any destructive operation (exporting all student data).
- **+T+C+R:** empty-result explanation ("0 programs matched — most restrictive criterion: TOEFL ≥ 110 · try relaxing to ≥ 100"). Retry on fail. "Rephrase question" button feeds error back to LLM. Timeout (15s).

**Traps:**
1. Sample query chips removed in Stage C because "they conflict with editable criteria" — keep them, they help students understand what the tool can do.
2. Filter chips collapse on re-run — student loses their edits.
3. **Admissions trap:** query interprets "acceptance rate" as a filter when the app has no verified acceptance rate data — shows hallucinated rates in the results table without a disclaimer.
4. "Re-run" re-calls the LLM instead of re-running cached filter against data.
5. Chart redraws from scratch on every chip edit — wait for explicit re-run.

---

## 4 · Wizard + Inline Audit

**Shape:** multi-step student profile builder or application checklist with AI per-field requirement checking.
**Core UX problem in admissions:** student fills out a profile, clicks Submit, and only then learns they're below the TOEFL minimum for all target schools. Too late, too late.
**Production refs:** Common App profile builder (manual version of this), any compliance form with inline validation.

- **Stage 0:** N-step profile form. AI pre-fills fields from uploaded documents. "Submit" clickable. No per-field requirement indicators. No summary. Student doesn't know which fields pass program requirements.
- **+T:** each field has an inline status indicator (✓/⚠/✗) + a chip naming the requirement (e.g., "MIT CS: GRE ≥ 165 · your score: 158 · ⚠ borderline"). Click chip → sidecar shows official requirement text (or "per AI estimate — verify" if no corpus). AI-pre-filled fields show "AI pre-filled" badge + confidence. Header: "N requirements met · M borderline · K missing."
- **+T+C:** hover field → "Regenerate this field only" without touching other fields. "Override" checkbox + required reason textbox. Back/forward without data loss. Save draft.
- **+T+C+R:** Submit disabled while any ✗ field exists — tooltip lists which and why. Autosave banner. Regen failure isolates to that field. Preview + edit before final submit. Placeholder text ("e.g., 3.85") blocked from submission.

**Traps:**
1. Regenerate replaces ALL fields — wipes student's manual corrections.
2. Requirement chip sidecar is a modal that blocks the form.
3. Autosave stores to localStorage only — lost if student switches device.
4. "Override" checkbox requires no reason → students disable every failing check to pass. Always require a reason textbox.
5. ✓/⚠/✗ is the only signal — fails for colorblind users. Pair with text labels or icons.
6. **Admissions trap:** "Requirement met" shown based on requirements the AI made up, not verified data. If no corpus, label: "AI-estimated requirement — verify with official sources."

---

## 5 · Draft → Approve → Send

**Shape:** AI draft of personal statement / recommendation letter / admission email + mandatory human review + hard-confirm send.
**Core UX problem in admissions:** irreversible. A personal statement with hallucinated facts (clubs the student didn't join, scores they don't have) submitted to 10 schools cannot be recalled.
**Production refs:** Mailchimp test-send (for the review flow model), any email assistant with preview.

- **Stage 0:** AI generates draft in a single text blob. Single "Send" button. No diff. No per-section confidence. No verification against student's actual profile. No hard confirm.
- **+T:** draft shown as diff vs. last-approved version (+ green, - red). Per-section confidence. Flag: "⚠ This claim could not be verified against your uploaded profile — please confirm it's accurate." Generation meta (model, date, "based on profile fields: GPA, extracurriculars, intended major"). Recipient preview (school name, admissions email).
- **+T+C:** each section independently editable. Regenerate-per-section preserves the others. Template-locked fields (school name, program name) show lock icon — editing requires "Unlock" + confirmation. Mandatory preview step before send. "Save as draft" alternative.
- **+T+C+R:** Send behind hard confirm (type school name or "SEND" / "GỬI"). Dry-run to a test recipient first, shows delivery receipt. Undo window (10–30s) after send. Mid-send failure: "sent N / failed M → retry M only." Keep draft on any failure. Block send if document contains unverified flagged sections (from T layer) without counselor acknowledgment.

**Traps:**
1. Dry-run accidentally goes to the real admissions office — always verify the send path in QA.
2. Undo tries to recall an already-delivered email (impossible) instead of cancelling a queued send.
3. Confirm accepts lowercase "send" — too easy to trigger accidentally.
4. Regenerate-per-section re-runs the full LLM call for untouched sections too — wastes tokens and risks changing approved content.
5. **Admissions trap:** AI-drafted personal statement contains specific claims ("I led the robotics team to a state championship") that aren't in the student's profile. Prompt T must flag unverified claims — Prompt R must block send without counselor acknowledgment of flagged sections.

---

## 6 · Queue + Approval Dashboard

**Shape:** list of AI-flagged student cases + per-case counselor action (approve, escalate, request info) + bulk ops.
**Core UX problem in admissions:** counselor throughput. N flagged students → burnout if reviewed one-at-a-time. Low-confidence AI flags get buried under high-confidence ones.
**Production refs:** any counseling center student management tool; content moderation consoles (structural model).

- **Stage 0:** N student cards sorted by urgency. Each has Approve/Escalate. No AI reasoning shown. No confidence. No bulk ops. No deadline visibility.
- **+T:** each card shows: confidence dot (green: AI-confident / yellow: borderline / red: needs human review), one-line AI reasoning ("Flagged: GPA 2.9 · below minimum for all selected schools"), upcoming deadline badge (red if ≤14 days). Header counts: N pending · M high-confidence · K borderline. Low-confidence cases sort to top within each urgency tier.
- **+T+C:** bulk-select + shift-click range. Filter by flag reason, school, deadline proximity, confidence threshold. "Select all borderline" shortcut. Bulk actions: Schedule session / Request more info / Escalate. Per-case override with required reason. Keyboard: J/K nav, A/R/E/U actions.
- **+T+C+R:** undo every action (10-action stack). "Request more info" as alternative to rejection — holds case in "Waiting" state. Re-surface case when student updates profile ("Profile updated — re-review?" badge). Classification-failed cases show distinct "Manual review required" marker and sort to top.

**Traps:**
1. Bulk approve processes N students in one LLM call → timeout. Batch in smaller groups.
2. Undo restores the case but not its original position in the sorted queue.
3. Low-confidence cases sort to top, but deadline sort wins — counselor never sees borderline cases approaching deadlines.
4. Override changes the counselor's assessment but doesn't re-run AI confidence — card shows new category but old reasoning.
5. "Manual review required" cases pile at bottom — counselor misses them. Sort to top.
6. **Admissions trap:** "Auto-approvable" flag on high-confidence cases leads counselors to bulk-approve without reading. Reserve auto-approval only for explicitly low-stakes actions (e.g., "schedule a check-in call") — never for decisions that affect a student's application.

---

## 7 · Real-time Streaming

**Shape:** voice advising session or live essay feedback → partial output streams → student can interrupt.
**Core UX problem in admissions:** sub-second latency budget. Any lag >~800ms feels broken. Silence in a live advising session destroys trust.
**Production refs:** ChatGPT Voice, any live interview coach tool, real-time essay feedback tools.

- **Stage 0:** "Start" button. After a delay, full transcript + AI reply appear. No activity indicator. No confidence. No interrupt.
- **+T:** output streams word-by-word. Low-confidence suggestions underlined (dashed, lower opacity) — hover for alternatives. Live status: "Listening…", "Thinking…", "Speaking…". Session meta (model, latency, duration). If the AI reaches the edge of its admissions knowledge: "I'm not certain about this — I recommend verifying with [school name]'s official admissions page."
- **+T+C:** spacebar/tap interrupts mid-reply. "Switch to text" fallback without losing context. Pause/resume for transcription.
- **+T+C+R:** disconnect → "Disconnected · Reconnecting (N/3) · Hold on". Preserve transcript on reconnect. Low-confidence segments hoverable for alternatives. Mic/camera permission-denied gracefully falls to text with clear message. Auto-reconnect capped at 3.

**Traps:**
1. Simulated streaming uses `setInterval` — real streaming needs WebSocket or streaming HTTP.
2. Interrupt cuts audio but leaves the network call running → next student input queues behind it.
3. "Switch to text" loses the last partial transcript instead of seeding the text input.
4. Reconnect shows "ready" when TCP reconnects, before LLM stream has resumed — student speaks, AI is deaf.
5. **Admissions trap:** live AI gives confident acceptance probability estimates ("You have a 78% chance of getting into Stanford") that are hallucinated. Real-time context makes it harder for students to mentally flag AI estimates. The "I'm not certain" signal from +T is load-bearing — it must appear for any numerical predictions.

---

## Mapping decision table — Admissions domain

| Story's core UX moment | UI pattern |
|---|---|
| Student/counselor types question, AI answers with match scores / citations / checklist visible | 1 |
| Student uploads transcript/CV/test scores → AI extracts structured profile or insight tiles | 2 |
| User types a question, AI produces a program comparison table or cohort chart (not prose) | 3 |
| Student fills multi-step profile or application checklist, each field AI-checked against requirements | 4 |
| AI drafts personal statement / letter / email, counselor or student approves, system sends | 5 |
| Counselor processes batch of AI-flagged student cases (approve / escalate / request info) | 6 |
| Student or counselor speaks/streams, AI responds <1s, can interrupt (live advising) | 7 |

**Admissions borderline disambiguators:**
- Chat that returns a ranked school list → pattern 1 (panel = ranked list; output is prose + panel data, not a pure interactive chart).
- Profile wizard that ends with "AI drafts personal statement → counselor approves → sends" → pattern 5 (irreversible send dominates).
- Student asks "compare GPA requirements for CS programs" → pattern 3 (output is a table, not prose).
- Upload that returns a chat-style Q&A advisor, not a dashboard → pattern 1 (file as context), not pattern 2.

**Multi-actor split (very common in admissions):**
PRDs for admissions systems almost always have two distinct actors: student (asks, uploads, fills) and counselor (reviews, approves, manages queue). These are typically different patterns:
- Student side → usually pattern 1 (chat advisor) or pattern 4 (profile wizard)
- Counselor side → usually pattern 6 (student queue) or pattern 5 (document review + send)

Never fuse both actors into one screen. Pick the primary actor's screen for Demo 1. Note the counselor screen as Demo 2 in the GUIDELINE.

## Meta-pattern — "Conversational UI + Evidence Panel" (Admissions edition)

Pattern 1 is a meta-pattern. Swap what the panel shows and it covers the admissions space:
- panel = **match scores** → program fit advisor (no corpus, logic-based — label as AI estimate)
- panel = **citations** → school handbook RAG chatbot (needs real corpus)
- panel = **checklist** → requirements tracker alongside chat
- panel = **ranked program list** → school recommendation advisor
- panel = **student profile summary** → counselor context panel while advising

When in doubt between patterns 1, 3, and 6, default to 1 and choose the admissions panel payload. The panel payload decision determines the trust signal type, which determines what data the app actually needs to build.
