from typing import Dict, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob


def analyze_sentiment(texts: List[str]) -> Dict:
    scores = [TextBlob(t).sentiment.polarity for t in texts]
    avg = np.mean(scores) if scores else 0
    return {
        "average_score": round(avg * 100, 1),
        "positive": round(sum(1 for s in scores if s > 0) / len(scores) * 100, 1) if scores else 0,
        "neutral": round(sum(1 for s in scores if s == 0) / len(scores) * 100, 1) if scores else 0,
        "negative": round(sum(1 for s in scores if s < 0) / len(scores) * 100, 1) if scores else 0,
        "count": len(scores),
    }

def find_trending_topics(texts: List[str], top_n: int = 10) -> List[str]:
    if not texts or len(texts) < 2:
        return []
    vec = TfidfVectorizer(max_features=100, stop_words="english", ngram_range=(1, 2))
    try:
        mat = vec.fit_transform(texts)
        scores = np.array(mat.sum(axis=0)).flatten()
        indices = scores.argsort()[-top_n:][::-1]
        return [vec.get_feature_names_out()[i] for i in indices]
    except Exception:
        return []

def compute_risk_index(texts: List[str]) -> Dict:
    negative_keywords = ["conflict", "war", "crisis", "attack", "threat", "sanction", "collapse"]
    scores = []
    for t in texts:
        blob = TextBlob(t.lower())
        count = sum(1 for word in blob.words if word in negative_keywords)
        scores.append(min(count / max(len(blob.words), 1) * 100, 100))
    avg_risk = np.mean(scores) if scores else 0
    if avg_risk > 60:
        level = "critical"
    elif avg_risk > 35:
        level = "high"
    elif avg_risk > 15:
        level = "moderate"
    else:
        level = "low"
    return {"risk_index": round(float(avg_risk), 1), "level": level}

def recommend_articles(user_history: List[str], available: List[str], top_n: int = 5) -> List[int]:
    if not user_history or not available:
        return list(range(min(top_n, len(available))))
    vec = TfidfVectorizer(stop_words="english", max_features=500)
    try:
        all_texts = user_history + available
        mat = vec.fit_transform(all_texts)
        user_vec = mat[:len(user_history)].mean(axis=0)
        sims = cosine_similarity(user_vec, mat[len(user_history):]).flatten()
        return sims.argsort()[-top_n:][::-1].tolist()
    except Exception:
        return list(range(min(top_n, len(available))))
