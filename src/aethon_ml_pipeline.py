import os
from typing import List
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_PATH, exist_ok=True)

def train_tfclf(prompts: List[str], labels: List[int], save_name="tfidf_lr.pkl"):
    X_train, X_test, y_train, y_test = train_test_split(prompts, labels, test_size=0.2, random_state=42)
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000)),
        ("lr", LogisticRegression(max_iter=1000))
    ])
    pipeline.fit(X_train, y_train)
    score = pipeline.score(X_test, y_test)
    path = os.path.join(MODEL_PATH, save_name)
    joblib.dump(pipeline, path)
    return {"score": score, "path": path}

def load_model(path):
    return joblib.load(path)

def predict(model, prompts: List[str]):
    return model.predict(prompts).tolist()
