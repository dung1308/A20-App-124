# services/ltr.py

import numpy as np
import joblib
import os

from sklearn.linear_model import LogisticRegression
from services.features import extract_features


class LearningToRank:
    def __init__(self, model_path: str = "models/reranker.pkl"):
        self.model_path = model_path

        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
        else:
            # fallback: simple linear model with default weights
            self.model = LogisticRegression()
            self._init_default_weights()

    def _init_default_weights(self):
        # Fake training so model works before real training
        # Features: [semantic, keyword_overlap, doc_len, is_cv, is_adm, is_faq]
        X = np.array([
            [0.9, 3, 1.0, 1, 0, 0],
            [0.8, 2, 0.7, 0, 1, 0],
            [0.1, 0, 0.1, 0, 0, 0]
        ])
        y = np.array([1, 1, 0])
        self.model.fit(X, y)

    def score(self, query: str, doc: str, distance: float, metadata: dict) -> float:
        features = extract_features(query, doc, distance, metadata)
        return self.model.predict_proba([features])[0][1]

    def rerank(self, query: str, docs: list, distances: list, metadatas: list, top_k: int = 3):
        scored = []

        for doc, dist, meta in zip(docs, distances, metadatas):
            score = self.score(query, doc, dist, meta)
            scored.append((score, doc))

        scored.sort(reverse=True)
        return [doc for score, doc in scored[:top_k]]

    def save(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)