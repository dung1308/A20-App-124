import json
import os

def load_results(version):
    filepath = f"eval_results_{version}.json"
    if not os.path.exists(filepath):
        print(f"❌ Không tìm thấy file kết quả cho version {version}: {filepath}")
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return {item["id"]: item for item in json.load(f)}

def compare_versions(v1_tag="v1", v2_tag="v2"):
    """
    So sánh kết quả đánh giá giữa hai phiên bản prompt.
    """
    results_v1 = load_results(v1_tag)
    results_v2 = load_results(v2_tag)

    if not results_v1 or not results_v2:
        return

    all_ids = sorted(list(set(results_v1.keys()) | set(results_v2.keys())))
    
    print("\n" + "="*90)
    print(f"📊 SO SÁNH HIỆU QUẢ PROMPT: {v1_tag.upper()} vs {v2_tag.upper()}")
    print("="*90)
    print(f"{'ID':<10} | {'Category':<20} | {v1_tag:<8} | {v2_tag:<8} | {'Delta':<8} | {'Status'}")
    print("-" * 90)

    v1_total_score = 0
    v2_total_score = 0
    v1_pass_count = 0
    v2_pass_count = 0
    improvements = 0
    regressions = 0

    for cid in all_ids:
        r1 = results_v1.get(cid, {})
        r2 = results_v2.get(cid, {})

        s1 = r1.get("eval", {}).get("score", 0)
        s2 = r2.get("eval", {}).get("score", 0)
        cat = r2.get("category") or r1.get("category", "N/A")
        
        v1_total_score += s1
        v2_total_score += s2
        if r1.get("eval", {}).get("pass"): v1_pass_count += 1
        if r2.get("eval", {}).get("pass"): v2_pass_count += 1

        delta = s2 - s1
        if delta > 0:
            status = "📈 IMPROVED"
            improvements += 1
        elif delta < 0:
            status = "📉 REGRESSED"
            regressions += 1
        else:
            status = "☁️ STABLE"

        print(f"{cid:<10} | {cat[:20]:<20} | {s1:<8} | {s2:<8} | {delta:<+8} | {status}")

    # Tổng kết
    num_cases = len(all_ids)
    v1_avg = v1_total_score / num_cases
    v2_avg = v2_total_score / num_cases
    total_delta = v2_avg - v1_avg

    print("-" * 90)
    print(f"{'TRUNG BÌNH':<33} | {v1_avg:<8.2f} | {v2_avg:<8.2f} | {total_delta:<+8.2f} |")
    print(f"{'TỶ LỆ ĐẠT (PASS)':<33} | {v1_pass_count}/{num_cases:<6} | {v2_pass_count}/{num_cases:<6} |")
    print("="*90)
    
    print(f"\n💡 Tóm tắt: {improvements} cải thiện, {regressions} thụt lùi.")
    if total_delta > 5:
        print(f"✅ Kết luận: Version {v2_tag} có cải tiến đáng kể. Khuyến nghị cập nhật.")
    elif total_delta < -5:
        print(f"⚠️ Cảnh báo: Version {v2_tag} tệ hơn version {v1_tag}. Cần kiểm tra lại prompt.")
    else:
        print(f"ℹ️ Kết luận: Không có sự thay đổi lớn về chất lượng giữa hai phiên bản.")

    # In lý do của những ca bị giảm điểm (nếu có)
    if regressions > 0:
        print("\n🔍 CHI TIẾT CÁC CA BỊ GIẢM ĐIỂM:")
        for cid in all_ids:
            s1 = results_v1.get(cid, {}).get("eval", {}).get("score", 0)
            s2 = results_v2.get(cid, {}).get("eval", {}).get("score", 0)
            if s2 < s1:
                print(f"--- [CASE {cid}] ---")
                print(f"Lý do v2: {results_v2[cid]['eval'].get('reasoning')}")
                print(f"Ý chính thiếu: {results_v2[cid]['eval'].get('missing_points')}")

if __name__ == "__main__":
    compare_versions("v1", "v2")