# services/train.py (Optional: can be used for training the reranker model)

import numpy as np
import joblib

from services.features import extract_features
from sklearn.linear_model import LogisticRegression


def train_reranker(training_data, model_path="models/reranker.pkl"):
    X = []
    y = []

    for item in training_data:
        query = item["query"]
        doc = item["doc"]
        distance = item.get("distance", 0.5)
        metadata = item.get("metadata", {})
        label = item["label"]

        features = extract_features(query, doc, distance, metadata)

        X.append(features)
        y.append(label)

    model = LogisticRegression()
    model.fit(np.array(X), np.array(y))

    joblib.dump(model, model_path)
    print(f"Model saved to {model_path}")