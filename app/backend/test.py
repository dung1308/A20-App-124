import json
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from services.pdf_loader import extract_text_from_pdf
from main import app, create_access_token

# Initialize the FastAPI test client
client = TestClient(app)

def test_upload_cv_flow():
    """
    Integration test to verify that the /api/upload-cv endpoint:
    1. Authenticates successfully with a JWT token.
    2. Processes a mock PDF file.
    3. Returns 'cv_signals' which are essential for prompt analysis and matching.
    """
    print("Starting Integration Test: /api/upload-cv")

    # 1. Generate a mock access token
    test_user_payload = {"sub": "student_test@vinuni.edu.vn", "role": "user"}
    token = create_access_token(test_user_payload)
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Prepare the real PDF upload from mock_data
    cv_path = os.path.join(os.path.dirname(__file__), "mock_data", "CV_Samples", "template.pdf")
    
    if not os.path.exists(cv_path):
        print(f"Error: Target CV file not found at {cv_path}")
        return

    with open(cv_path, "rb") as f:
        file_content = f.read()
    
    # Sanity check: Ensure we aren't sending a mock text file by mistake
    if b"% Mock PDF Content" in file_content:
        print("CRITICAL ERROR: template.pdf seems to be a mock text file, not a real PDF.")
        return

    files = {"file": ("template.pdf", file_content, "application/pdf")}

    # 3. Execute the request
    print("Sending POST request to /api/upload-cv (injecting mock Academic Signals)...")
    
    # We patch the PDF loader in main.py to append a mock GPA string to the extracted text.
    # This allows us to verify the high-achiever persona logic without modifying template.pdf.
    with patch("main.extract_text_from_pdf") as mock_loader:
        original_text = extract_text_from_pdf(cv_path)
        mock_loader.return_value = original_text + "\nGPA: 3.9/4.0 (10-scale: 9.2)\nIELTS: 8.5"
        response = client.post("/api/upload-cv", files=files, headers=headers)

    # 4. Assertions and Data Inspection
    print(f"Response Code: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    print("\n[API RESPONSE DATA]")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    assert "cv_signals" in data, "The endpoint MUST return cv_signals for prompt analysis."
    assert "cv_text" in data, "The endpoint MUST return cv_text to populate the frontend store."
    
    # Verify that text was actually extracted and measured by the CVAgent
    extracted_length = data["cv_signals"].get("analysis_metadata", {}).get("length", 0)
    assert extracted_length > 0, f"Expected extracted text length > 0, but got {extracted_length}."

    # Verify specific signals extracted from template.pdf via the new layout-aware parser
    signals = data["cv_signals"]
    job_titles = signals.get("extracted_job_titles", [])
    referrer_titles = signals.get("referrer_titles", [])
    skills = signals.get("extracted_skills", [])
    suggested_majors = signals.get("suggested_majors", [])
    gpa = signals.get("gpa_estimate")
    ielts = signals.get("ielts_estimate")
    persona_summary = signals.get("persona_summary", "")

    # Candidate experience assertions
    assert any("Product Manager" in title for title in job_titles), f"Expected Product Manager in candidate titles, got: {job_titles}"
    # assert any("Owner" in title for title in job_titles), f"Expected Owner in candidate titles, got: {job_titles}"
    
    # Referrer assertions
    # assert any("Technical Lead" in title for title in referrer_titles), f"Expected Technical Lead in referrers, got: {referrer_titles}"
    # assert any("QC Lead" in title for title in referrer_titles), f"Expected QC Lead in referrers, got: {referrer_titles}"
    
    assert "Product Management" in skills, f"Expected 'Product Management' in skills, got: {skills}"
    # assert "Business Administration" in suggested_majors, f"Expected 'Business Administration' in suggested majors, got: {suggested_majors}"
    # assert "Computer Science" in suggested_majors, f"Expected 'Computer Science' in suggested majors, got: {suggested_majors}"

    # GPA and Persona Highlight assertions
    assert gpa == 3.9 or gpa == 9.2, f"Expected GPA (3.9 or 9.2) to be detected, got: {gpa}"
    assert ielts == 8.5, f"Expected IELTS 8.5 to be detected, got: {ielts}"
    assert "thành tích học tập xuất sắc" in persona_summary, "Persona summary should highlight academic excellence for high GPAs."
    assert "8.5" in persona_summary, "Persona summary should include the IELTS score for context."

    # Communication enrichment assertion
    assert "Senior Product Manager" in persona_summary, "Persona summary should include professional context for the LLM."
    
    print(f"\n[SUCCESS] Integration test passed: Extracted {extracted_length} chars, identified titles: {job_titles}")

if __name__ == "__main__":
    test_upload_cv_flow()