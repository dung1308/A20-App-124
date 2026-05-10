"""
services/reranker.py
--------------------
Simple Learning-to-Rank implementation using Logistic Regression.
"""

import os
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

MODEL_DIR = "model_saved"
MODEL_PATH = os.path.join(MODEL_DIR, "reranker.pkl")

class LearningToRank:
    def __init__(self):
        self.model = self.load()

    def train(self, X, y):
        """Trains the model and saves it to disk."""
        self.model.fit(X, y)
        self.save()

    def save(self):
        """Serializes the model to a file."""
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(self.model, MODEL_PATH)

    def load(self):
        """Loads the model from disk or returns a new instance."""
        if os.path.exists(MODEL_PATH):
            try:
                return joblib.load(MODEL_PATH)
            except Exception:
                pass
        return LogisticRegression()

    def score(self, features: np.ndarray) -> float:
        try:
            return self.model.predict_proba([features])[0][1]
        except Exception:
            # Re-raise to trigger fallback in RAGService if model not fitted
            raise