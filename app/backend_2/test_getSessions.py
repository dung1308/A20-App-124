import json
import uuid
from fastapi.testclient import TestClient
from main import app, create_access_token

def test_list_user_sessions():
    """
    Kiểm tra endpoint GET /api/chat/sessions/{user_id}
    Mục tiêu: Đảm bảo dữ liệu trả về có đủ ID và Title để Frontend hiển thị Sidebar.
    """
    print("\n" + "="*50)
    print("BẮT ĐẦU KIỂM TRA LẤY DANH SÁCH SESSIONS")
    print("="*50)

    # Sử dụng context manager để kích hoạt các sự kiện startup (bao gồm init_database)
    with TestClient(app) as client:
        user_email = "tester_sessions@vinuni.edu.vn"

        # 0. Đảm bảo user tồn tại trong DB (Tránh lỗi ForeignKeyViolation)
        signup_payload = {
            "full_name": "Session Tester",
            "email": user_email,
            "password": "TestPassword123!",
            "admin_key": "dev-admin-key"
        }
        # Chúng ta gọi signup, nếu user đã tồn tại (400) thì cũng không sao
        client.post("/api/auth/signup", json=signup_payload)

        # 1. Tạo Token cho User test
        token = create_access_token({"sub": user_email, "role": "user"})
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Tạo một session mới bằng cách gửi tin nhắn đầu tiên
        # Điều này đảm bảo Database có dữ liệu để trả về
        test_message = "Xin chào, tôi muốn tìm hiểu về các ngành kỹ thuật."
        chat_payload = {
            "userId": user_email,
            "text": test_message,
            "sessionId": "new"
        }
        
        print(f"Đang tạo phiên mới cho user: {user_email}...")
        chat_res = client.post("/api/chat", json=chat_payload, headers=headers)
        assert chat_res.status_code == 200, "Không thể tạo tin nhắn chat đầu tiên."
        
        created_session_id = chat_res.json().get("sessionId")
        print(f"✓ Đã tạo thành công phiên: {created_session_id}")

        # 3. Gọi API lấy danh sách sessions
        print(f"Đang gọi API list sessions cho {user_email}...")
        response = client.get(f"/api/chat/sessions/{user_email}", headers=headers)
        
        # 4. Kiểm tra phản hồi
        assert response.status_code == 200, f"Lỗi API: {response.status_code}"
        data = response.json()
        
        print("\n[DỮ LIỆU PHẢN HỒI TỪ API]")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        assert data["status"] == "success"
        assert "sessions" in data and isinstance(data["sessions"], list)
        assert len(data["sessions"]) > 0, "API trả về danh sách session rỗng."

    # 5. Kiểm tra cấu trúc của Session đầu tiên
    first_session = data["sessions"][0]
    
    # Kiểm tra ID (có thể là 'id' hoặc 'sessionId')
    session_id_key = "id" if "id" in first_session else "sessionId"
    # Kiểm tra Title (có thể là 'title' hoặc 'sessionTitle')
    title_key = "title" if "title" in first_session else "sessionTitle"

    print(f"\n✓ Tìm thấy ID qua key: '{session_id_key}' -> {first_session.get(session_id_key)}")
    print(f"✓ Tìm thấy Title qua key: '{title_key}' -> {first_session.get(title_key)}")
    print("="*50 + "\n")

if __name__ == "__main__":
    test_list_user_sessions()