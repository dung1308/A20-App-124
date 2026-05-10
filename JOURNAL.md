# Weekly Journal

Ghi lại hành trình xây dựng sản phẩm mỗi tuần — những gì đã làm, học được gì, AI giúp như thế nào.

> **Cập nhật mỗi cuối tuần** (trước khi tạo PR). Không cần dài, chỉ cần thật.

---

## Template

```markdown
## Tuần N — DD/MM/YYYY

### Đã làm
-

### Khó nhất tuần này
-

### AI tool đã dùng
| Tool | Dùng để làm gì | Kết quả |
|---|---|---|
| Claude Code | | |

### Học được
-

### Nếu làm lại, sẽ làm khác
-

### Kế hoạch tuần tới
-
```

---

## Ví dụ

### Tuần 1 — 31/03/2026

**Thành viên:** Nguyễn Văn A, Trần Thị B, Lê Văn C

#### Đã làm
- Setup project TypeScript + cấu hình `.env`
- Xây dựng agent loop cơ bản: nhận input → gọi Claude API → in output
- Thêm tool `search_web` đầu tiên (dùng Brave Search API)
- Viết README cho repo nhóm

#### Khó nhất tuần này
- Tool call response của Claude trả về sai format — mất 2 tiếng debug mới phát hiện ra thiếu `"type": "tool_result"` trong message history.
- Lần đầu dùng TypeScript nên type error khá nhiều, phải học cách dùng `as` và generic.

#### AI tool đã dùng
| Tool | Dùng để làm gì | Kết quả |
|---|---|---|
| Claude Code | Giải thích Anthropic tool use API, debug message format | Giải quyết được bug trong 15 phút |
| Cursor | Autocomplete TypeScript types | Tiết kiệm khoảng 30% thời gian gõ |

#### Học được
- Tool use trong Claude hoạt động theo vòng lặp: model gọi tool → app trả kết quả → model tiếp tục. Cần giữ đúng message history.
- `zod` rất hữu ích để validate tool input schema.
- Nên đặt timeout cho API call ngay từ đầu, không để sau mới thêm.

#### Nếu làm lại, sẽ làm khác
- Setup TypeScript strict mode ngay từ đầu thay vì thêm sau (refactor mệt hơn).
- Viết unit test cho `parseToolCall()` trước khi tích hợp vào agent loop.

#### Kế hoạch tuần tới
- Thêm tool `read_file` và `write_file`
- Implement memory: lưu conversation history vào file JSON
- Thử chạy agent giải 1 bài tập thực tế

---

### Tuần 2 — 07/04/2026

**Thành viên:** Nguyễn Văn A, Trần Thị B, Lê Văn C

#### Đã làm
- Thêm tool `read_file`, `write_file`, `list_dir`
- Agent có thể tự đọc file trong repo và đề xuất refactor
- Implement conversation memory: lưu 20 message gần nhất
- Thử nghiệm: cho agent tự fix 3 bug đơn giản → thành công 2/3

#### Khó nhất tuần này
- Memory bị lỗi khi conversation quá dài (vượt context window). Phải implement sliding window: chỉ giữ system prompt + 20 message gần nhất.
- Agent đôi khi loop vô hạn khi tool trả lỗi — chưa có stop condition tốt.

#### AI tool đã dùng
| Tool | Dùng để làm gì | Kết quả |
|---|---|---|
| Claude Code | Thiết kế sliding window memory, review code agent loop | Phát hiện thêm edge case khi tool throw exception |
| Gemini CLI | So sánh approach lưu memory: file JSON vs SQLite | Tư vấn dùng JSON cho prototype, SQLite khi cần query |

#### Học được
- Context window là resource có hạn — cần thiết kế memory strategy từ sớm.
- Stop condition quan trọng không kém gì agent logic: `max_iterations`, `no_new_tool_calls`, `explicit_done`.
- AI agent review code của mình rất có ích: Claude Code tìm ra 2 potential null pointer mà mình bỏ sót.

#### Nếu làm lại, sẽ làm khác
- Viết interface `Memory` trước, rồi implement sau — thay vì hard-code array từ đầu.
- Log tất cả tool call ra file ngay từ đầu để debug dễ hơn.

#### Kế hoạch tuần tới
- Fix vòng lặp vô hạn: thêm `max_iterations = 10`
- Thêm tool `run_tests` để agent tự kiểm tra code sau khi sửa
- Demo cho instructor cuối tuần

### Tuần 23 — 05/09/2026
Thành viên: Nhóm A20-124
#### Đã làm
- Hoàn tất chuyển đổi LLM provider từ Google Gemini sang OpenAI (gpt-4o-mini).
- Thay thế thư viện PyPDF2 đã lỗi thời bằng pdfplumber với chế độ layout=True, giúp trích xuất thông tin từ CV đa cột chính xác hơn đáng kể.
- Cấu hình lại RAGService với 3 collection ChromaDB chuyên biệt: admissions, faq, và cvs.
- Tối ưu hóa quy trình tìm kiếm với Query Expansion và LTR (Learning-to-Rank) reranker.
- Loại bỏ triệt để các dependency không cần thiết và giải quyết lỗi nạp model mặc định của ChromaDB trên Railway.

#### Khó nhất tuần này
- Debug lỗi log 307 Temporary Redirect khi deploy lên Railway. Nguyên nhân do ChromaDB tự động cố gắng tải model từ HuggingFace dù đã cấu hình dùng OpenAI embeddings. Đã xử lý bằng cách set embedding_function=None khi khởi tạo collection.
- Đảm bảo tính nhất quán của EMBEDDING_MODEL (text-embedding-3-small) trên toàn bộ hệ thống để tránh sai lệch vector.

#### AI tool đã dùng
| Tool | Dùng để làm gì | Kết quả |
|---|---|---|
| Gemini Code Assist | Phân tích log Railway, refactor logic RAG và tư vấn chuyển đổi thư viện PDF | Giải quyết lỗi startup và tối ưu hóa hiệu suất trích xuất dữ liệu |
| OpenAI API | Cung cấp Embeddings và Generation | Phản hồi nhanh, giá rẻ và độ chính xác cao hơn model cũ |

#### Học được
- Khi sử dụng ChromaDB với manual embeddings, việc khai báo explicit embedding_function=None là bắt buộc để tránh server tự download model nặng hàng trăm MB.
- Layout-aware parsing (pdfplumber) là chìa khóa để trích xuất dữ liệu từ các mẫu hồ sơ hiện đại.

#### Nếu làm lại, sẽ làm khác
- Sẽ đóng gói các hằng số cấu hình model (embedding vs chat) vào một file constants.py ngay từ đầu để tránh việc hard-code trong các service.

#### Kế hoạch tuần tới
- Triển khai UI theo pattern "Chat + Context Panel" để hiển thị Match Score và bằng chứng đi kèm.
 - Hoàn thiện hệ thống Guardrails để bảo vệ dữ liệu PII của sinh viên.

### Cập nhật ngày 06/09/2026
#### Đã làm
- Triển khai trọn bộ Backend Session API: hỗ trợ lưu, đổi tên, xóa và tải xuống lịch sử hội thoại dưới dạng file .txt.
- Xây dựng logic `migrate_db()` trong `DBService` giúp tự động cập nhật schema (thêm cột `title`) khi khởi chạy server.
- Tối ưu hóa các Agent: Tách biệt `ADVISOR_CHAT_SYSTEM_PROMPT` cho hội thoại tự nhiên, cải tiến khả năng parse JSON bền bỉ cho Advisor và Judge Agent.
- Bảo mật dữ liệu: Thực hiện PII Masking (ẩn Email, SĐT) trong `CRMAgent` và viết unit test xác thực tại `test_crm_pii.py`.
- Cải tiến UI/UX: Thêm "Trust Badge" bảo mật tại trang Profile, cập nhật giao diện `MajorCard` và xử lý lỗi crash Google Login khi thiếu cấu hình Client ID.
- Fix lỗi SyntaxError: Xử lý triệt để các lỗi docstring chưa đóng trong các file agent.

#### Khó nhất tuần này
- Đảm bảo tính nhất quán của dữ liệu khi thực hiện migration schema tự động trên SQLite và PostgreSQL mà không làm gián đoạn dịch vụ.

#### AI tool đã dùng
| Tool | Dùng để làm gì | Kết quả |
|---|---|---|
| Gemini Code Assist | Hỗ trợ refactor Agent prompts, viết code migration và unit test PII | Hệ thống hoạt động ổn định, bảo mật và chuyên nghiệp hơn |

#### Học được
- Việc tách biệt rõ ràng giữa prompt trả về dữ liệu (JSON) và prompt trò chuyện (Text) giúp hệ thống AI hoạt động tin cậy hơn, tránh được các lỗi hiển thị không mong muốn cho người dùng cuối.