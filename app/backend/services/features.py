# services/features.py

import numpy as np

def extract_features(query: str, doc: str, distance: float, metadata: dict):
    metadata = metadata or {}
    query_words = set(query.lower().split())
    doc_words = set(doc.lower().split())

    keyword_overlap = len(query_words & doc_words)

    # Correctly identify source type across Admissions, FAQ, and CV collections
    # Supports both 'source' and 'type' keys used in rag_service ingestion/retrieval
    src = str(metadata.get("source", "")).lower()
    tp  = str(metadata.get("type", "")).lower()

    is_cv  = 1 if (src == "cv" or tp == "cv") else 0
    is_adm = 1 if (tp == "admission" or src == "admissions") else 0
    is_faq = 1 if (tp == "faq" or src == "faq") else 0

    return np.array([
        1.0 - distance if distance is not None else 0.0,   # semantic score
        keyword_overlap,                                   # keyword match
        len(doc_words) / 100,                              # normalized length
        is_cv, is_adm, is_faq                              # source flags
    ])