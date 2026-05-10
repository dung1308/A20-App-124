# 🎯 Admission Chatbot Data Design (Final)

## 1. 📦 Thư mục tổng thể

```
data/
├── universities/
│   ├── fpt/
│   │   ├── university.json
│   │   ├── programs.json
│   │   ├── scholarships.json
│   │   └── documents/
│   │       ├── raw/
│   │       │   ├── admission.pdf
│   │       │   ├── scholarship.pdf
│   │       └── processed/
│   │           ├── document_chunks.json
│
├── users/
│   └── user_profiles.json
│
├── vector_store/
│   ├── program_index/
│   ├── document_index/
│   └── university_index/
```

---

# 2. 🟦 SCHEMA

## 2.1 university.json

Thông tin tổng quan về trường

```json
{
  "id": "string",
  "name": "string",
  "location": { "city": "string" },
  "type": "public | private",
  "ranking": { "national": "number" },
  "facilities": ["string"],
  "tuition_range": { "min": "number", "max": "number" },
  "university_insights": ["string"]
}
```

---

## 2.2 programs.json

Danh sách ngành học

```json
[
  {
    "program_id": "string",
    "university_id": "string",
    "name": "string",
    "degree": "Bachelor",
    "duration": "string",

    "career": {
      "job_roles": ["string"],
      "average_salary": { "min": "number", "max": "number" }
    },

    "training_quality": ["string"],

    "program_score_factors": {
      "difficulty": "low | medium | high",
      "practical_level": "low | medium | high",
      "job_opportunity": "low | medium | high"
    }
  }
]
```

---

## 2.3 scholarships.json

Tóm tắt học bổng

```json
[
  {
    "id": "string",
    "university_id": "string",
    "name": "string",
    "value": "string",
    "summary": "string",
    "conditions": ["string"],
    "applicable_programs": ["string"]
  }
]
```

---

## 2.4 document.json

Thông tin file tài liệu

```json
[
  {
    "id": "string",
    "university_id": "string",
    "program_id": "string | null",
    "document_type": "admission | scholarship",
    "title": "string",
    "file_url": "string"
  }
]
```

---

## 2.5 document_chunk.json (RAG)

Dữ liệu dùng cho AI

```json
[
  {
    "id": "string",
    "document_id": "string",
    "program_id": "string | null",

    "document_type": "admission | scholarship",

    "content": "text đã extract",

    "section": "hoc_phi | dieu_kien | hoc_bong",

    "structure_type": "text | table",

    "table_data": [
      { "field": "string", "value": "string" }
    ]
  }
]
```

---

## 2.6 user_profile.json

```json
[
  {
    "user_id": "string",

    "academic_info": {
      "gpa": "number"
    },

    "preferences": {
      "interests": ["string"]
    },

    "goals": ["string"],

    "constraints": {
      "budget": "number"
    }
  }
]
```

---

# 3. 📄 TÀI LIỆU CẦN THU THẬP

# 📄 3. TÀI LIỆU CẦN THU THẬP (TABLE)

| Nhóm dữ liệu                 | Nội dung cần thu thập                                                                                   | Nguồn                        |
| ---------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------- |
| 🎓 Chương trình đào tạo      | - Mô tả ngành<br>- Nội dung học (curriculum)<br>- Thời gian học<br>- Career outcome (job roles, salary) | Website ngành của trường     |
| 🏫 Thông tin trường          | - Giới thiệu trường<br>- Cơ sở vật chất<br>- Ranking / uy tín<br>- Học phí tổng quan                    | Website chính thức, brochure |
| 📄 Tài liệu tuyển sinh (RAG) | - PDF tuyển sinh<br>- Điều kiện xét tuyển (GPA, IELTS)<br>- Phương thức tuyển sinh<br>- Deadline        | PDF, website tuyển sinh      |
| 🎁 Tài liệu học bổng (RAG)   | - PDF học bổng<br>- Điều kiện nhận (GPA, IELTS)<br>- Giá trị học bổng (% học phí)<br>- Số lượng suất    | Website, PDF học bổng        |

**Lưu ý** Lưu tài liệu về dưới dạng docs hoặc bất kỳ dạng nào sẵn sàng cho chunking và đưa vào folder `data/docs`

---

# 4. 🎯 TỔNG KẾT

* University → thông tin trường
* Program → ngành học
* Scholarship → tóm tắt học bổng
* Document → file gốc
* Document Chunk → AI sử dụng
* User → cá nhân hóa

