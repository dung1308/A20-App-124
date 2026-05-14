# Issues Found - 14/05/2026

This file compiles the issues found after testing the ChatBox human fallback flow and the expected fixes for the next implementation pass.

## 1. Human Counsellor Chat Should Open In A Pop-Up Window

### Current behavior

- User can request a human counsellor from ChatBox.
- Admin/editor can see pending fallback jobs.
- The human reply is written back into the normal AI chat session.
- The user experience does not clearly separate AI chat from human-to-human chat.

### Problem

Students cannot easily tell whether they are talking to AI or a real counsellor. This weakens trust and makes the fallback flow feel like another AI answer instead of a live support session.

### Expected behavior

- When a human counsellor accepts a handoff job, the student should see a dedicated pop-up chat window.
- The pop-up should be clearly labeled as human counsellor support.
- The pop-up should show only messages between the student and the assigned admin/editor.
- AI should not answer inside this pop-up.
- AI chat and human chat should be separate surfaces.

### Suggested implementation

Backend:

- Add a dedicated human handoff conversation model or message type, for example:
  - `handoff_conversations`
  - `handoff_messages`
- Store:
  - `handoff_id` or `trace_id`
  - `student_user_id`
  - `staff_user_id`
  - `status`: `pending`, `accepted`, `closed`
  - `created_at`, `accepted_at`, `closed_at`
- Add student/staff APIs:
  - `GET /api/handoff-status`
  - `GET /api/handoff/{trace_id}/messages`
  - `POST /api/handoff/{trace_id}/messages`
  - `POST /api/admin/handoff/{trace_id}` for accept/busy/close
- Ensure human messages are not routed through `Pipeline.run_chat`.

Frontend:

- Add a `HumanCounsellorPopup.jsx` component.
- Show it when `/api/handoff-status` returns `pending` or `accepted`.
- Keep the normal AI ChatBox available but visually separate.
- Poll or stream human messages independently from AI messages.

### Acceptance criteria

- Student requests human help.
- Admin/editor sees a pending job.
- Admin/editor accepts the job.
- Student sees a pop-up human chat window.
- Messages in the pop-up are only student and human counsellor messages.
- Sending messages in the pop-up never calls `/api/chat` or the AI pipeline.

---

## 2. Human Counsellor Name Shows Mojibake / Email Instead Of Full Name

### Current behavior

The human reply can appear like:

```text
ChuyÃªn viÃªn tÆ° váº¥n (admin@vinuni.edu.vn): ...
```

### Problems

- Vietnamese text is mojibake, which makes the UI look broken.
- The counsellor is identified by email instead of the full name already entered during signup.
- Students should see a human-friendly staff display name.

### Expected behavior

Human counsellor messages should display:

```text
<Staff full name>: <message>
```

Example:

```text
Nguyen Van A: Minh da xem ho so cua ban...
```

If `full_name` is missing, fallback order should be:

1. `full_name`
2. email local-part
3. role label such as `VinUni counsellor`

### Suggested implementation

Backend:

- When admin/editor sends a handoff reply, load staff profile from `users`.
- Use `full_name` from signup instead of `current_user["email"]`.
- Return message payload with separate structured fields:
  - `sender_id`
  - `sender_name`
  - `sender_role`
  - `content`
  - `timestamp`
- Avoid prefixing the content string with the staff name. Let frontend render the label.

Frontend:

- Render `sender_name` in the message header.
- Render `content` separately.
- Avoid hardcoded mojibake Vietnamese labels in human message content.

### Acceptance criteria

- Staff reply displays the staff full name from signup.
- Email is not shown as the primary display name.
- No mojibake appears in the visible sender label.

---

## 3. Human Fallback Job Creation Should Be Deterministic

### Current behavior

Asking `Please call human counsellor` may still look like an AI fallback answer if the UI does not surface the human handoff state clearly.

### Problem

The student needs confirmation that a real support job was created. Admin/editor also needs the job to appear reliably.

### Expected behavior

- Explicit human-help intent should create a pending handoff job immediately.
- The response should include:
  - `handoff_status: pending`
  - `trace_id`
  - `fallback_card`
  - next action text such as "Waiting for counsellor"
- The frontend should show the human popup or a waiting banner.

### Suggested implementation

- Keep direct detection for phrases like:
  - `Please call human counsellor`
  - `I need a human`
  - `connect me to advisor`
  - `tu van vien`
  - `chuyen vien`
- After job creation, immediately refresh `/api/handoff-status`.
- Admin/staff page should poll pending handoffs or refresh after accept/reply.

### Acceptance criteria

- Typing a direct human request creates exactly one pending job.
- Admin/editor sees the job without needing to inspect audit logs manually.
- Student sees clear waiting state.

---

## 4. Human Chat Must Not Be Mixed With AI Chat History

### Current behavior

Human staff replies are saved into the same chat session as assistant messages.

### Problem

This makes it hard to distinguish AI-generated content from human counselling. It also risks future AI context using private human-to-human messages unintentionally.

### Expected behavior

- Human chat should use a separate message table or a strict `agent_type = human_staff` filter.
- Normal AI chat should not ingest or respond to human-only messages unless explicitly summarized and approved.
- The pop-up should fetch only human handoff messages.

### Suggested implementation

Short-term:

- Continue using `chat_messages`, but filter the pop-up to:
  - `agent_type = human_staff`
  - `agent_type = handoff_student`
- Exclude these from `/api/chat` history sent to AI.

Better long-term:

- Add dedicated `handoff_messages` table and endpoints.

### Acceptance criteria

- AI chat history and human chat history render separately.
- AI does not automatically answer inside the human counsellor popup.
- Human messages are not used as AI context unless explicitly designed.

---

## Priority

1. Create dedicated student-facing human handoff popup.
2. Add human-only message endpoint and stop sending popup messages to `/api/chat`.
3. Display staff `full_name` instead of email.
4. Fix mojibake labels in human fallback text.
5. Keep admin/editor pending jobs reliable and easy to refresh.

## Files Likely Affected

Backend:

- `app/backend/main.py`
- `app/backend/models/schemas.py`
- `app/backend/services/db_service.py`
- `app/backend/orchestrator/pipeline.py`

Frontend:

- `app/frontend/components/Chat/ChatBox.jsx`
- `app/frontend/components/Chat/HumanCounsellorPopup.jsx`
- `app/frontend/pages/StaffDashboard.jsx`
- `app/frontend/services/api.js`

Docs:

- `14_05_Summary.md`
- `JOURNAL.md`
- `app/guide/PRD.md`
- `app/guide/Guideline_v3.md`

---

## Implementation Update

Status: implemented in backend and frontend.

- Added dedicated `handoff_messages` storage for human-only counsellor transcripts.
- Added `GET /api/handoff/{trace_id}/messages` and `POST /api/handoff/{trace_id}/messages`.
- Changed student handoff creation to return `trace_id` and save the initial request in the human-only transcript.
- Changed staff replies to save structured `sender_name`, `sender_role`, and `content` instead of prefixing the message with mojibake text.
- Added `HumanCounsellorPopup.jsx` for the student-side human chat window.
- Updated Staff Dashboard to read/write the human-only transcript and poll for new messages.
- Kept normal AI chat and human counsellor popup separate so popup sends never call `/api/chat`.
