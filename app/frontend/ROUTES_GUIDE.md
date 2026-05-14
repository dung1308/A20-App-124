# Hướng dẫn các Tuyến đường (Routes) Frontend - Trợ lý Tuyển sinh VinUni

Tài liệu này giải thích cấu trúc và mục đích của từng tuyến đường (route) được định nghĩa trong `app/frontend/App.jsx`.

## 🚪 Truy cập & Xác thực
- **`/login`**: Điểm truy cập chính để người dùng xác thực thông qua Google OAuth.
- **`/wizard`**: (Pattern 4) Quy trình khảo sát nhiều bước nơi sinh viên cung cấp sở thích và tải lên tài liệu trước khi vào bảng điều khiển chính.

## 🎓 Tính năng cho Sinh viên (Đã xác thực)
Các tuyến đường này được bao bọc trong `AuthenticatedLayout` và chủ yếu dành cho người dùng là sinh viên.

- **`/dashboard`**: Trung tâm chính để sinh viên xem tóm tắt hồ sơ và các hành động nhanh.
- **`/consultant`**: (Pattern 1) Chatbot Tư vấn Tuyển sinh AI tương tác. Đây là nơi sinh viên đặt câu hỏi và nhận câu trả lời kèm theo bảng bằng chứng hỗ trợ.
- **`/profile`**: (Pattern 2) Hiển thị dữ liệu học tập đã trích xuất (GPA, Điểm thi) và cho phép người dùng quản lý CV cũng như thông tin cá nhân.
- **`/report`**: Hiển thị phân tích AI chi tiết và có cấu trúc về khả năng cạnh tranh của sinh viên đối với các chương trình cụ thể.
- **`/pricing`**: Thông tin về các gói dịch vụ và các tính năng hiện có.

## 👔 Tính năng cho Nhân viên & Hệ thống (Bảo vệ theo vai trò)
Các tuyến đường này bị giới hạn cho người dùng có vai trò `admin` (Quản trị viên) hoặc `editor` (Nhân viên/Biên tập viên).

- **`/staff`**: (Pattern 6) Bảng điều khiển dành cho Tư vấn viên. Được nhân viên sử dụng để phân loại hồ sơ sinh viên, xem xét các cảnh báo của AI và thực hiện phê duyệt thủ công.
- **`/admin`**: Giao diện quản lý cấp cao dành cho quản trị viên hệ thống để cấu hình ứng dụng.
- **`/system/tokens`**: Công cụ minh bạch để theo dõi việc sử dụng token LLM và chi phí trên toàn hệ thống.
- **`/system/database`**: Các công cụ để quản lý và xác minh dữ liệu trường học và kho dữ liệu RAG cơ sở.

## 🛠 Kiến trúc Kỹ thuật

### Bảo vệ Tuyến đường
- **`AuthenticatedLayout`**: Đảm bảo người dùng đã đăng nhập và cung cấp thanh điều hướng `LeftPanel` tiêu chuẩn.
- **`StaffRoute`**: Giới hạn quyền truy cập cho vai trò Nhân viên (Editor) hoặc Quản trị viên (Admin).
- **`AdminRoute`**: Giới hạn quyền truy cập nghiêm ngặt chỉ dành cho vai trò Quản trị viên (Admin).

### Tham chiếu UI Patterns
Các tuyến đường được thiết kế xoay quanh **7 pattern UI** được định nghĩa trong `archetypes_admissions.md`, đảm bảo rằng các tương tác AI có tính minh bạch (Transparency - T), khả năng kiểm soát (Control - C) và khả năng phục hồi (Resilience - R).

---
*Hướng dẫn này được tạo ra để hỗ trợ việc phát triển và hiểu rõ cấu trúc điều hướng của ứng dụng.*