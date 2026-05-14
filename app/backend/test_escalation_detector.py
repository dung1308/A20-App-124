import unittest

from guards.escalation_detector import EscalationDetector


class TestEscalationDetector(unittest.TestCase):
    def setUp(self):
        self.detector = EscalationDetector()

    def test_high_admission_promise(self):
        level, reason = self.detector.detect_overcommitment(
            "Với hồ sơ này, em chắc chắn đậu ngành Khoa học Máy tính."
        )

        self.assertEqual(level, "HIGH")
        self.assertIn("admission", reason)

    def test_high_scholarship_guarantee(self):
        level, reason = self.detector.detect_overcommitment(
            "Em 100% có học bổng nếu nộp hồ sơ sớm."
        )

        self.assertEqual(level, "HIGH")
        self.assertIn("guarantee", reason)

    def test_medium_unverified_policy(self):
        level, reason = self.detector.detect_overcommitment(
            "Trường có quy định bắt buộc mọi ứng viên phải phỏng vấn."
        )

        self.assertEqual(level, "MEDIUM")
        self.assertIn("policy", reason)

    def test_safe_uncertainty(self):
        level, reason = self.detector.detect_overcommitment(
            "Hồ sơ của em có điểm mạnh, nhưng kết quả tuyển sinh cần được VinUni xác nhận chính thức."
        )

        self.assertEqual(level, "NONE")
        self.assertEqual(reason, "")


if __name__ == "__main__":
    unittest.main()
