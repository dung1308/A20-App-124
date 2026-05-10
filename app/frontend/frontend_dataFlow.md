# VinUni Frontend Data Flow Summary

This document describes the data lifecycle within the React frontend, from user input capture to API integration and state persistence.

## 1. Global State & Context (`state/store.js`)
The frontend utilizes a centralized state (via Zustand or Redux as per the skeleton) to maintain:
- **User Profile**: Persistent `userId` for session tracking.
- **Authentication**: Token-based authentication using `token` and `userEmail` from the backend.
- **Wizard Progress**: Temporary storage of answers from Steps 1–4.
- **UI Configuration**: `IS_DEMO_MODE` toggle which controls the display of the "Demo Mode" banner and simulates latency.

---

## 2. Recommendation Wizard Flow (`WizardPage.jsx`)
**Objective**: Collect student data and navigate to the Major Report.

1.  **Input Collection**: `Step1.jsx` through `Step4.jsx` collect:
    - Interests and Strengths (Arrays).
    - Dislikes and Work Style (Strings).
    - Optional CV (File/Text) processed via `api.js`.
2.  **Submission**: On finishing Step 4, the combined `answers` object is sent via `services/api.js` to `POST /api/match`.
3.  **Redirection**: Upon receiving the `Top 3` majors JSON, the user is navigated to `ReportPage.jsx`.
4.  **Display**: `ReportPage.jsx` iterates over the `top3` array, rendering `MajorCard.jsx` components enriched with match scores and reasons.

---

## 3. Conversational Chat Flow (`ChatBox.jsx`)
**Objective**: Real-time interaction with the AI Assistant.

1.  **Hook Interaction**: `ChatBox.jsx` consumes the `useChat.js` custom hook.
2.  **Message Dispatch**: 
    - User types a message → `sendMessage(input)` is called.
    - Local state is immediately updated with the user message (Optimistic UI).
    - `loading` state is set to `true`, triggering the "VinUni Bot đang soạn câu trả lời..." indicator.
3.  **API Request**: The hook calls `POST /api/chat` including the current `message` and `history`.
4.  **Response Handling**:
    - Success: The `messages` array in the hook state is updated with the assistant's response.
    - Error: A fallback error message is added to the chat history.
5.  **Scroll Management**: `useEffect` in `ChatBox.jsx` monitors the `messages` and `loading` states to trigger `scrollToBottom()`, ensuring the latest interaction is visible.

---

## 4. Safety & Formatting
- **PII Masking**: The frontend displays redacted text returned by the backend's `OutputGuard`.
- **Sanitization**: Content is rendered safely to prevent XSS from potential AI-generated artifacts.
- **Demo Visuals**: When `IS_DEMO_MODE` is active, a top-level amber banner is rendered to inform the user that results are simulated.

---

## Key API Contracts
- `POST /api/match`: Returns `{ top3: [...], fallback: boolean, disclaimer: string }`.
- `POST /api/chat`: Returns `{ response: string, intent: string, status: string }`.