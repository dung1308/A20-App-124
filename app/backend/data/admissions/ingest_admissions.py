import json
import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# Tải biến môi trường (OPENAI_API_KEY)
load_dotenv()

def ingest_admissions_data():
    """
    Đọc dữ liệu tuyển sinh từ JSON và nạp vào ChromaDB với đầy đủ metadata.
    """
    # Cấu hình đường dẫn
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "admissions", "ung-tuyen-vao-vinuni (1).json")
    persist_directory = os.path.join(base_dir, "chroma_db")

    # 1. Khởi tạo ChromaDB Persistent Client
    client = chromadb.PersistentClient(path=persist_directory)

    # 2. Cấu hình OpenAI Embedding Function (sử dụng text-embedding-3-small như thiết kế)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Lỗi: Không tìm thấy OPENAI_API_KEY trong file .env")
        return

    embedding_fn = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name="text-embedding-3-small"
    )

    # 3. Khởi tạo hoặc lấy collection 'admissions'
    collection = client.get_or_create_collection(
        name="admissions",
        embedding_function=embedding_fn
    )

    # 4. Đọc dữ liệu từ file JSON
    if not os.path.exists(data_path):
        print(f"❌ Lỗi: Không tìm thấy tệp dữ liệu tại {data_path}")
        return

    with open(data_path, 'r', encoding='utf-8') as f:
        items = json.load(f)

    ids = []
    documents = []
    metadatas = []

    for item in items:
        ids.append(item["id"])
        documents.append(item["text"])
        
        # Chuẩn bị metadata (ChromaDB không nhận list/dict lồng nhau)
        metadata = {
            "section": item.get("section", ""),
            "source": item.get("source", ""),
            "url": item.get("url", ""),
            "type": item.get("type", ""),
            "videos": json.dumps(item.get("videos", [])), # Chuyển list thành string
            "links": json.dumps(item.get("links", []))    # Chuyển list thành string
        }
        metadatas.append(metadata)

    # 5. Thực hiện nạp dữ liệu (upsert)
    print(f"🚀 Đang nạp {len(documents)} bản ghi vào collection 'admissions'...")
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    print("✅ Hoàn tất nạp dữ liệu vào ChromaDB.")

if __name__ == "__main__":
    ingest_admissions_data()