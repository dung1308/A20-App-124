import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app, create_access_token

class TestProfileChatImpact(unittest.TestCase):
    """
    Test suite to verify that student profile data (GPA, IELTS, CV Persona) 
    correctly impacts the Chatbot and Matching logic.
    """

    def setUp(self):
        self.client = TestClient(app)
        self.user_email = "outstanding_student@vinuni.edu.vn"
        # Generate a valid token for the test user
        self.token = create_access_token({"sub": self.user_email, "role": "user"})
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @patch("main.pipeline")
    def test_persona_summary_injection_into_chat(self, mock_pipeline):
        """
        Verify that specific academic signals (GPA 4.0 scale, IELTS 9.0 scale) 
        reach the orchestrator via the persona_summary.
        """
        # Simulate a persona generated from a CV upload and high-achieving profile
        # Note: GPA is on 4.0 scale, IELTS on 9.0 scale as requested
        persona_summary = (
            "Student with perfect academic record (GPA 4.0/4.0), "
            "native-level English (IELTS 9.0/9.0). "
            "CV indicates leadership in Robotics and AI research."
        )
        
        chat_payload = {
            "text": "What are my chances for the Computer Science major?",
            "personaSummary": persona_summary,
            "sessionId": "test-session-123"
        }

        # Mock the pipeline response
        mock_pipeline.run_chat.return_value = {
            "response": "With a 4.0 GPA and 9.0 IELTS, your chances are excellent!",
            "sessionId": "test-session-123"
        }

        response = self.client.post("/api/chat", json=chat_payload, headers=self.headers)

        # Assertions
        self.assertEqual(response.status_code, 200)
        
        # Verify that the orchestrator's run_chat was called with the persona context
        mock_pipeline.run_chat.assert_called_once()
        _, kwargs = mock_pipeline.run_chat.call_args
        
        passed_persona = kwargs.get('persona_summary')
        self.assertIn("GPA 4.0/4.0", passed_persona)
        self.assertIn("IELTS 9.0/9.0", passed_persona)
        self.assertIn("AI research", passed_persona)

    @patch("main.pipeline")
    def test_match_profile_persistence(self, mock_pipeline):
        """
        Verify that academic signals provided during the matching wizard 
        are correctly persisted to the student profile.
        """
        match_payload = {
            "user_id": self.user_email,
            "answers": {
                "gpa": 3.85,
                "test_scores": {"ielts": 8.5},
                "interests": ["Computer Science", "Data Science"]
            },
            "cv_text": "Full-stack developer internship at TechCorp...",
            "cv_signals": {
                "persona_summary": "Technical profile with industrial internship experience."
            }
        }

        mock_pipeline.run_match.return_value = {"top3": [{"major_id": "cs", "match_score": 98}]}

        response = self.client.post("/api/match", json=match_payload, headers=self.headers)

        self.assertEqual(response.status_code, 200)
        
        # Verify the DB Service received the high-value academic signals for saving
        mock_pipeline.db_service.upsert_student_profile.assert_called_once()
        call_args = mock_pipeline.db_service.upsert_student_profile.call_args[0]
        
        saved_data = call_args[1]
        self.assertEqual(saved_data["gpa"], 3.85)
        self.assertEqual(saved_data["test_scores"]["ielts"], 8.5)

if __name__ == "__main__":
    unittest.main()
