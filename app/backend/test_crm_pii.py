import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Đảm bảo thư viện backend nằm trong Python path để import được các agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.crm import CRMAgent

class TestCRMAgentPIIMasking(unittest.TestCase):
    """
    Unit test để kiểm tra tính năng bảo vệ thông tin cá nhân (PII Masking) 
    trong CRMAgent trước khi gửi dữ liệu sang LLM.
    """

    @patch('agents.crm.DBService')
    @patch('agents.crm.LLMClient')
    def setUp(self, mock_llm, mock_db):
        # Khởi tạo agent với các service đã được mock để cô lập logic của agent
        self.agent = CRMAgent()

    def test_pii_masking_logic(self):
        """
        Kiểm tra logic ẩn thông tin nhạy cảm trong phương thức nội bộ _build_crm_prompt.
        """
        # 1. Chuẩn bị hồ sơ học sinh chứa các thông tin nhạy cảm (PII)
        test_profile = {
            "full_name": "Nguyễn Văn A",
            "email": "nguyenvana@gmail.com",
            "phone": "0912345678",
            "address": "123 Đường ABC, Hà Nội",
            "id_number": "001203004567",
            "gpa": 3.9,
            "interests": ["Công nghệ", "Âm nhạc"]
        }
        question = "Hồ sơ của tôi có những thông tin gì?"

        # 2. Gọi phương thức xây dựng prompt (nơi thực hiện masking)
        prompt = self.agent._build_crm_prompt(test_profile, question)

        # 3. Kiểm tra các thông tin nhạy cảm ĐÃ BỊ LOẠI BỎ khỏi prompt
        self.assertNotIn("nguyenvana@gmail.com", prompt, "Lỗi: Email vẫn còn trong prompt!")
        self.assertNotIn("0912345678", prompt, "Lỗi: Số điện thoại vẫn còn trong prompt!")
        self.assertNotIn("123 Đường ABC", prompt, "Lỗi: Địa chỉ vẫn còn trong prompt!")
        self.assertNotIn("001203004567", prompt, "Lỗi: Số ID/CCCD vẫn còn trong prompt!")

        # 4. Kiểm tra xem chuỗi thay thế có xuất hiện đúng vị trí không
        self.assertIn("[ĐÃ ẨN ĐỂ BẢO MẬT]", prompt)
        # Xác minh có đúng 4 trường nhạy cảm đã bị ẩn (email, phone, address, id_number)
        self.assertEqual(prompt.count("[ĐÃ ẨN ĐỂ BẢO MẬT]"), 4)

        # 5. Kiểm tra các thông tin an toàn vẫn được giữ lại để AI có thể làm việc
        self.assertIn("Nguyễn Văn A", prompt)
        self.assertIn("3.9", prompt)
        self.assertIn("Công nghệ", prompt)
        self.assertIn(question, prompt)

    @patch('agents.crm.DBService')
    @patch('agents.crm.LLMClient')
    def test_pii_masking_during_run(self, mock_llm_class, mock_db_class):
        """
        Kiểm tra tích hợp: Đảm bảo khi gọi hàm run(), prompt thực tế gửi tới LLM đã được mask.
        """
        mock_db = mock_db_class.return_value
        mock_llm = mock_llm_class.return_value
        
        # Giả lập DB trả về hồ sơ có chứa PII
        mock_db.get_student_profile.return_value = {"email": "secret@vinuni.edu.vn", "full_name": "Tester User"}
        mock_llm.generate.return_value = "Xin chào Tester User!"

        agent = CRMAgent()
        agent.run(user_id="test_user", message="Xem email của tôi")

        # Lấy nội dung prompt thực tế mà agent đã gửi vào hàm generate của LLM client
        called_prompt = mock_llm.generate.call_args[0][0]
        self.assertNotIn("secret@vinuni.edu.vn", called_prompt)
        self.assertIn("[ĐÃ ẨN ĐỂ BẢO MẬT]", called_prompt)

if __name__ == '__main__':
    unittest.main()