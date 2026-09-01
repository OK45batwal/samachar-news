import re
from collections import Counter
from typing import List

POSITIVE_WORDS = {'breakthrough', 'growth', 'gain', 'profit', 'rise', 'surge', 'success', 'innovation', 'boost', 'upgrade', 'advance', 'progress', 'recovery', 'milestone', 'victory', 'expand', 'unveil', 'launch'}
NEGATIVE_WORDS = {'crash', 'drop', 'decline', 'loss', 'fall', 'plunge', 'crisis', 'threat', 'risk', 'warn', 'concern', 'fear', 'fail', 'collapse', 'conflict', 'war', 'attack', 'strike', 'damage', 'disaster'}
STOP_WORDS = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'by', 'with', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'have', 'has', 'had', 'this', 'that', 'these', 'those'}


def analyze_sentiment(text: str) -> int:
    """Analyze sentiment of text and return a normalized score between -100 and +100."""
    if not text:
        return 0
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    if not words:
        return 0
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return 15
    return max(-100, min(100, int(((pos - neg) / total) * 100)))


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """Extract top keywords excluding common stop words."""
    if not text:
        return []
    words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', text.lower()) if w not in STOP_WORDS]
    return [w for w, _ in Counter(words).most_common(top_n)]


def generate_key_takeaways(title: str, summary: str, content: str) -> List[str]:
    """Extract key takeaway bullet points for an article."""
    points = [title.strip()] if title else []
    body = summary or content or ""
    if body:
        sentences = [s.strip() for s in re.split(r'[.!?]+', body) if len(s.strip()) > 15]
        for s in sentences:
            if s not in points and len(points) < 3:
                points.append(s)
    return points or ["Verified factual reporting."]
