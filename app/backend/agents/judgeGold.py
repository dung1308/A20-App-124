"""
agents/judgeGold.py
-------------------
Responsibility: Evaluation Agent for Ground Truth (Golden Answers).
Compares the Chatbot's response against "Golden Answer" criteria (Key points, behavior, tone).
"""

import json
from typing import Dict, Any, List
from services.llm_client import LLMClient
from services.prompt_service import PromptService
from config import USE_MOCK, PROMPT_VERSION
from utils.logger import get_logger

logger = get_logger(__name__)

GOLDEN_JUDGE_SYSTEM_PROMPT = """
Bạn là chuyên gia kiểm định chất lượng AI (QA Auditor). Nhiệm vụ của bạn là đánh giá câu trả lời của Chatbot dựa trên tiêu chuẩn "Golden Answer".

Dữ liệu đầu vào:
1. Câu hỏi (Query)
2. Câu trả lời của Chatbot (Chatbot Response)
3. Hành vi kỳ vọng (Expected Behavior)
4. Các ý chính bắt buộc (Key Points)
5. Giọng điệu yêu cầu (Required Tone)

Tiêu chí chấm điểm (Score 0-100):
- Độ chính xác (Accuracy): Thông tin có đúng với thực tế và Expected Behavior không?
- Đầy đủ (Completeness): Có bao quát đủ các Key Points không?
- Minh chứng (Evidence): Chatbot có cung cấp nguồn (Source/Link) để chứng minh thông tin không? (Trừ 20 điểm nếu thiếu link).
- Giọng điệu (Tone): Có phù hợp với yêu cầu (Professional, Encouraging,...) không?

Yêu cầu đầu ra (Chỉ trả về JSON thuần):
{
  "score": 85,
  "pass": true,
  "reasoning": "Giải thích chi tiết bằng tiếng Việt. Nêu rõ ý nào đạt, ý nào thiếu.",
  "missing_points": ["Danh sách các ý chính bị thiếu nếu có"]
}
"""

class JudgeAgentGoldenAns:
    """
    Agent chuyên trách đánh giá câu trả lời dựa trên bộ câu hỏi chuẩn (Golden Answers).
    """
    def __init__(self, prompt_version: str = PROMPT_VERSION):
        self.llm = None if USE_MOCK else LLMClient()
        self.prompt_service = PromptService()
        self.system_prompt = self.prompt_service.get_prompt("judge_gold", prompt_version)

    def evaluate(self, query: str, response: str, gold_data: Dict[str, Any]) -> Dict[str, Any]:
        """So sánh phản hồi của bot với ground truth."""
        if USE_MOCK:
            return {
                "score": 100, 
                "pass": True, 
                "reasoning": "MOCK: Đạt yêu cầu chất lượng.", 
                "missing_points": []
            }

        prompt = (
            f"{self.system_prompt}\n\n"
            f"DỮ LIỆU CẦN ĐÁNH GIÁ:\n"
            f"- Query: {query}\n"
            f"- Chatbot Response: {response}\n"
            f"- Expected Behavior: {gold_data.get('expected_behavior')}\n"
            f"- Key Points: {', '.join(gold_data.get('key_points', []))}\n"
            f"- Required Tone: {gold_data.get('required_tone', 'N/A')}"
        )

        try:
            raw_res = self.llm.generate(prompt)
            # Làm sạch JSON nếu model trả về markdown blocks
            clean_text = raw_res.strip()
            start_idx = clean_text.find('{')
            end_idx = clean_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("Không tìm thấy JSON trong phản hồi của Judge LLM")
                
            return json.loads(clean_text[start_idx:end_idx])

        except Exception as e:
            logger.error(f"JudgeAgentGoldenAns error: {e}")
            return {"score": 0, "pass": False, "reasoning": f"Lỗi hệ thống đánh giá: {str(e)}", "missing_points": []}