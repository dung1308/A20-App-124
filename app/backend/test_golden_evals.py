import json
import os
import sys
from agents.judgeGold import JudgeAgentGoldenAns
from orchestrator.pipeline import Pipeline
from utils.logger import get_logger
from config import PROMPT_VERSION

logger = get_logger(__name__)

def run_golden_evaluation(prompt_version: str = PROMPT_VERSION):
    """
    Script chạy kiểm thử chất lượng Chatbot dựa trên bộ Golden Answers.
    """
    # 1. Load Golden Answers
    gold_path = os.path.join(os.path.dirname(__file__), "data", "golden_answers", "chat_evals.json")
    if not os.path.exists(gold_path):
        print(f"❌ Không tìm thấy file golden answers tại: {gold_path}")
        return

    with open(gold_path, "r", encoding="utf-8") as f:
        eval_cases = json.load(f)

    # 2. Khởi tạo Pipeline (Chatbot) và JudgeAgent (Giám khảo)
    # Đảm bảo Pipeline của bạn nhận prompt_version trong __init__
    chatbot = Pipeline(prompt_version=prompt_version)
    judge = JudgeAgentGoldenAns(prompt_version=prompt_version)
    
    results = []
    print("\n" + "="*80)
    print(f"🚀 ĐÁNH GIÁ VERSION: {prompt_version} | {len(eval_cases)} TEST CASES")
    print("="*80)

    test_user = "eval_tester@vinuni.edu.vn"

    for case in eval_cases:
        case_id = case.get("id")
        query = case.get("query")
        category = case.get("category")
        
        print(f"\n[CASE {case_id}] Category: {category}")
        print(f"❓ Query: {query}")

        # 3. Chatbot trả lời
        chat_res = chatbot.run_chat(
            user_id=test_user,
            message=query,
            history=[],
            session_id=f"eval_{case_id}"
        )
        
        # Xử lý response format (tùy theo pipeline trả về string hay dict)
        bot_text = chat_res["response"] if isinstance(chat_res, dict) else chat_res

        # 4. Giám khảo chấm điểm
        eval_result = judge.evaluate(query, bot_text, case)
        
        # 5. Lưu kết quả
        status_icon = "✅ PASS" if eval_result.get("pass") else "❌ FAIL"
        score = eval_result.get("score", 0)
        
        print(f"🤖 Bot Response: {bot_text[:100]}...")
        print(f"⚖️ Result: {status_icon} | Score: {score}/100")
        print(f"📝 Reasoning: {eval_result.get('reasoning')}")
        
        results.append({
            "id": case_id,
            "category": category,
            "query": query,
            "bot_response": bot_text,
            "eval": eval_result
        })

    # 6. Tổng kết
    print("\n" + "="*80)
    print("📊 BÁO CÁO TỔNG KẾT")
    avg_score = sum(r["eval"]["score"] for r in results) / len(results)
    pass_count = sum(1 for r in results if r["eval"]["pass"])
    
    print(f"- Tổng số test case: {len(results)}")
    print(f"- Tỷ lệ đạt (Pass): {pass_count}/{len(results)}")
    print(f"- Điểm trung bình: {avg_score:.2f}/100")
    print("="*80 + "\n")

    # Xuất ra file kết quả để audit
    report_filename = f"eval_results_{prompt_version}.json"
    with open(report_filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"💾 Đã lưu báo cáo chi tiết vào: {report_filename}")

if __name__ == "__main__":
    run_golden_evaluation()