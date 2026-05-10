import numpy as np
from services.rag_service import RAGService, generate_training_data

if __name__ == "__main__":
    # Initialize RAGService to use its retrieval capabilities
    rag_service = RAGService()

    # Define a set of sample queries to generate training data
    sample_queries = [
        "Khoa học máy tính học gì?",
        "Ngành kỹ thuật điện tử có gì đặc biệt?",
        "Học phí VinUni là bao nhiêu?",
        "Yêu cầu đầu vào ngành quản trị kinh doanh?",
        "Tôi có thể học gì với điểm IELTS 7.0 và kinh nghiệm lập trình Python?",
        "Chương trình học của ngành Kỹ thuật Cơ khí?",
        "VinUni có những câu lạc bộ nào?",
        "Làm thế nào để nộp hồ sơ vào VinUni?",
    ]

    # Retrieve detailed documents for each query
    retrieved_results_for_training = {}
    for query in sample_queries:
        # Use retrieve_with_details to get text, distance, and metadata
        detailed_docs = rag_service.retrieve_with_details(query, top_k=5) 
        retrieved_results_for_training[query] = detailed_docs

    # Generate training data (features X and labels y)
    X, y = generate_training_data(sample_queries, retrieved_results_for_training)

    # Save the generated data using numpy for easy loading later
    np.save("training_X.npy", X)
    np.save("training_y.npy", y)

    print(f"Generated {len(X)} training samples.")
    print(f"Shape of X: {X.shape}")
    print(f"Shape of y: {y.shape}")
    print("Training data saved to training_X.npy and training_y.npy")