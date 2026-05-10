# Error processed in Backend
1. **Error in Chat API**: `422 Unprocessable Entity`
   - **Symptom**: Backend log reports `POST /api/chat HTTP/1.1" 422 Unprocessable Entity`. The UI (as seen in `Chat_API_1.png`) shows a generic connection error message: "Xin lỗi, tôi gặp chút trục trặc khi kết nối."
   - **Root Cause**: Request validation failure. The JSON payload from the frontend does not conform to the expected schema. 
   - **Technical Details**: 
     - Expected schema: `{"user_id": string, "message": string}`.
     - Likely issues: The frontend is missing the `user_id` field or using a different key for the user's input (e.g., `prompt` or `text` instead of `message`).
   - **Solution**:
     - **Frontend**: Ensure the `fetch` or `axios` call to `/api/chat` sends the correct keys. 
     - **Backend**: In `main.py`, verify the `ChatRequest` Pydantic model. If `user_id` is not strictly required for logic (other than rate limiting), it can be made optional: `user_id: Optional[str] = None`.
   - **Verification**: Test with `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"user_id": "test_user", "message": "Chào bạn"}'`.
   - **Status**: Fixed. Updated `ChatRequest` in `main.py` to set `user_id` as an optional field with a default value of "anonymous".

2. **Match API 422 Error (Schema Mismatch)**:
   - **Issue**: `WizardPage` sends `cv_signals` but backend `MatchRequest` didn't accept it.
   - **Fix**: Added `cv_signals` to `MatchRequest` in `main.py`. Updated `AuthPage` to sync `userId` to global store.

3. **Consultant Chat Connectivity Issue**:
   - **Symptom**: UI shows "trục trặc khi kết nối" upon sending messages after a page refresh.
   - **Root Cause**: Session loss. `userId` in Zustand store was cleared, leading to invalid API payloads.
   - **Fix**: Implemented `localStorage` persistence for `user_email` and added a `useEffect` hook in `ConsultantPage.jsx` to re-hydrate the session.
   - **Status**: Fixed.

4. **Chat API Safety Rejection (Mock Mode)**:
   - **Symptom**: API returns `status: "rejected"` with a safety warning message even in dev mode.
   - **Root Cause**: `JudgeAgent.evaluate` was being called during `USE_MOCK=True`, but the judge was failing/rejecting mock responses.
   - **Fix**: Updated `Pipeline.run_chat` in `pipeline.py` to mock a successful `judge_result` when `USE_MOCK` is enabled.
   - **Status**: Fixed.

5. **Chat API Persistent Fallback/Rejected Status**:
   - **Symptom**: API returns `status: "rejected"` despite calling valid endpoints.
   - **Root Cause**: Inconsistent `USE_MOCK` handling across agents and strict safety judge evaluation when `USE_MOCK=False` with missing/invalid API keys.
   - **Fix**: Updated `AdvisorAgent` and `RAGAgent` to be fully `USE_MOCK` aware, providing high-quality mock strings that bypass LLM calls.
   - **Solution**: Refactored `run_chat` in `pipeline.py` to ensure `judge_result` is safely initialized and added mode-verification logging.
   - **Recommendation**: Check backend logs for "Pipeline operating in ..." to confirm `.env` settings are correctly loaded.
   - **Status**: Resolved.
