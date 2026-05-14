# RAG Changes Summary

## Summary

Các thay đổi tập trung vào 3 vấn đề chính:

- Sửa lỗi RAG dùng nhầm ngữ cảnh cũ khiến câu hỏi về học bổng bị truy vấn thành học phí.
- Gắn link nguồn VinUni cho tài liệu được RAG truy xuất và hiển thị nguồn trên giao diện.
- Sửa lỗi audit log do schema `AuditLog` không khớp với dữ liệu pipeline đang ghi.

## Backend Changes

### `app/backend/agents/rag.py`

- Không còn nhét toàn bộ conversation history vào query chính khi retrieve.
- Truyền câu hỏi hiện tại (`message`) vào `RAGService.retrieve()` và truyền `history` riêng.
- `RAGAgent.run()` trả về object gồm:
  - `answer`
  - `sources`
- Thêm logic build nguồn tài liệu từ metadata:
  - `title`
  - `url`
- Nếu tài liệu thiếu URL, fallback về các trang VinUni phù hợp:
  - FAQ: `https://admissions.vinuni.edu.vn/vi/dai-hoc/cau-hoi-thuong-gap/`
  - Admissions: `https://admissions.vinuni.edu.vn/vi/dai-hoc/`
  - Default: `https://vinuni.edu.vn/`

### `app/backend/services/rag_service.py`

- Intent classification ưu tiên câu hỏi hiện tại trước câu đã expand.
- Nếu câu hỏi hiện tại không xác định được intent, mới fallback sang expanded query.
- Mục tiêu là tránh việc lịch sử chat kéo intent sang chủ đề cũ.

Ví dụ lỗi cũ:

- User hỏi: `có các chương trình học bổng nào tôi có thể apply`
- History trước đó nói về học phí.
- Query bị expand thành học phí và intent thành `tuition`.

Sau sửa:

- Câu hiện tại được classify trước.
- Intent đúng là `scholarship`.

### `app/backend/orchestrator/pipeline.py`

- Pipeline đọc response dạng dict từ agent:
  - `answer`
  - `sources`
- Trả `sources` vào `response_data` để frontend nhận được link nguồn.

### `app/backend/main.py`

- Endpoint `/api/chat` được flatten response.
- Trước đó response có thể bị bọc nested:

```json
{
  "response": {
    "response": "...",
    "sources": [...]
  }
}
```

- Sau sửa, API trả trực tiếp:

```json
{
  "response": "...",
  "sources": [...],
  "session_id": "..."
}
```

### `app/backend/models/schemas.py`

- Bổ sung các cột audit log mà pipeline đang sử dụng:
  - `input_text`
  - `output_text`
  - `judge_result`
  - `route`
  - `response_time_ms`
  - `ai_resolved`
  - `fallback`

### `app/backend/database.py`

- Thêm `_ensure_audit_log_columns()` để tự bổ sung các cột audit log còn thiếu khi app khởi động.
- Lý do: `Base.metadata.create_all()` không tự thêm cột mới cho bảng đã tồn tại.

### `requirements.txt`

- Thêm dependency:

```txt
rank-bm25>=0.2.2
```

- Lý do: `rag_service.py` đang import `rank_bm25.BM25Okapi`.

## Frontend Changes

### `app/frontend/hooks/useChat.js`

- Lưu `sources` từ backend vào assistant message.
- Đọc nguồn từ cả dạng response mới và dạng nested cũ:
  - `res.sources`
  - `res.response?.sources`
- Thêm `skipNextHistoryLoad` để tránh mất `sources` ngay sau khi tạo session mới.

Nguyên nhân lỗi không thấy nguồn:

- Backend đã trả `sources`.
- Frontend nhận xong đổi session từ `new` sang UUID.
- `useEffect(loadHistory)` chạy lại và nạp message từ DB.
- DB chỉ lưu text, không lưu `sources`, nên nguồn bị mất khỏi state.

### `app/frontend/pages/ConsultantPage.jsx`

- Thêm render block `Nguồn tham khảo` dưới câu trả lời assistant.
- `getSources()` đọc nguồn từ nhiều vị trí để tương thích:
  - `msg.sources`
  - `msg.raw.sources`
  - `msg.raw.response.sources`
  - `msg.content.sources`

### `app/frontend/components/Chat/ChatBox.jsx`

- Thêm render `sources` nếu component này được dùng ở màn hình chat khác.
- Hỗ trợ content dạng string và object.

## Verification

Đã chạy các kiểm tra:

```bash
venv\Scripts\python.exe -c "import ast,pathlib; files=['app/backend/main.py','app/backend/agents/rag.py','app/backend/orchestrator/pipeline.py']; [ast.parse(pathlib.Path(f).read_text(encoding='utf-8')) for f in files]; print('backend syntax ok')"
```

Kết quả:

```txt
backend syntax ok
```

```bash
npm run build
```

Kết quả:

```txt
✓ built
```

Vite có warning chunk lớn hơn 500 kB, không liên quan đến các thay đổi RAG/source link.

## Runtime Notes

- Cần restart backend để các thay đổi trong `/api/chat`, RAG và audit schema có hiệu lực.
- Cần reload frontend hoặc restart Vite dev server để UI mới được dùng.
- Các message cũ trong DB sẽ không có `sources` vì trước đây chỉ lưu text.
- Sources chỉ hiện cho các câu trả lời mới sau khi frontend/backend đã được reload.

## Expected API Shape

Ví dụ response mong muốn:

```json
{
  "response": "VinUni có các ngành đào tạo như sau...",
  "intent": "rag",
  "status": "success",
  "major": null,
  "sources": [
    {
      "title": "FAQ",
      "url": "https://admissions.vinuni.edu.vn/vi/dai-hoc/cau-hoi-thuong-gap/tuyen-sinh/"
    }
  ],
  "sessionId": "a2d5a83e-6450-4f3a-82ce-ddca4f661000",
  "sessionTitle": "cho tôi biết về các ngành học của vinuni",
  "session_id": "a2d5a83e-6450-4f3a-82ce-ddca4f661000"
}
```

## Changed Files

- `app/backend/agents/rag.py`
- `app/backend/services/rag_service.py`
- `app/backend/orchestrator/pipeline.py`
- `app/backend/main.py`
- `app/backend/models/schemas.py`
- `app/backend/database.py`
- `app/frontend/hooks/useChat.js`
- `app/frontend/pages/ConsultantPage.jsx`
- `app/frontend/components/Chat/ChatBox.jsx`
- `requirements.txt`

