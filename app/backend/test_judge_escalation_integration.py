import unittest
from unittest.mock import MagicMock

from agents.judge import JudgeAgent


class TestJudgeEscalationIntegration(unittest.TestCase):
    def setUp(self):
        self.judge = JudgeAgent()
        self.judge.llm = MagicMock()

    def test_judge_adds_escalation_metadata_and_rejects(self):
        self.judge.llm.generate.return_value = (
            '{"pass": true, "reason": "Looks safe", "score": 95}'
        )

        result = self.judge.evaluate(
            "Em có đậu không?",
            "Em chắc chắn đậu nếu nộp hồ sơ hôm nay.",
        )

        self.assertFalse(result["pass"])
        self.assertEqual(result["escalation_level"], "HIGH")
        self.assertIn("admission", result["escalation_reason"])
        self.assertLessEqual(result["score"], 40)

    def test_safe_response_preserves_none_escalation(self):
        self.judge.llm.generate.return_value = (
            '{"pass": true, "reason": "Grounded and cautious", "score": 90}'
        )

        result = self.judge.evaluate(
            "Em có cơ hội không?",
            "Hồ sơ có thể được xem xét, nhưng kết quả cần xác nhận từ hội đồng tuyển sinh.",
        )

        self.assertTrue(result["pass"])
        self.assertEqual(result["escalation_level"], "NONE")
        self.assertEqual(result["escalation_reason"], "")


if __name__ == "__main__":
    unittest.main()
