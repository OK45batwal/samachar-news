import re
from collections import Counter
from typing import List

POSITIVE_WORDS = {
    'breakthrough', 'growth', 'gain', 'gains', 'profit', 'rise', 'surge', 'soar', 'record',
    'success', 'successful', 'innovation', 'boost', 'upgrade', 'advance', 'progress', 'promising',
    'strong', 'positive', 'recovery', 'heal', 'peace', 'agreement', 'milestone', 'victory', 'champion',
    'award', 'expand', 'expansion', 'unveil', 'launch', 'thrive', 'flourish', 'optimism', 'optimistic'
}

NEGATIVE_WORDS = {
    'crash', 'drop', 'decline', 'loss', 'losses', 'fall', 'plunge', 'crisis', 'threat', 'risk',
    'warn', 'warning', 'concern', 'fear', 'fail', 'failure', 'collapse', 'conflict', 'war', 'attack',
    'strike', 'damage', 'destroy', 'disaster', 'outbreak', 'virus', 'death', 'dead', 'kill', 'fatal',
    'arrest', 'indict', 'lawsuit', 'sanction', 'ban', 'protest', 'riot', 'down', 'deficit', 'inflation'
}

STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'by', 'with',
    'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'shall',
    'can', 'not', 'no', 'nor', 'its', 'it', 'this', 'that', 'these', 'those', 'all',
    'each', 'every', 'both', 'few', 'more', 'most', 'some', 'any', 'new', 'after',
    'over', 'under', 'up', 'down', 'out', 'off', 'about', 'into', 'through', 'during',
    'before', 'between', 'than', 'also', 'just', 'very', 'too', 'yet', 'so', 'if',
    'because', 'while', 'when', 'where', 'how', 'what', 'which', 'who', 'whom', 'why',
}


def analyze_sentiment(text: str) -> int:
    """Analyze sentiment of text and return a score between -100 and +100."""
    if not text:
        return 0
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    if not words:
        return 0

    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    total_matched = pos_count + neg_count

    if total_matched == 0:
        return 15

    score = int(((pos_count - neg_count) / total_matched) * 100)
    return max(-100, min(100, score))


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """Extract top keywords excluding stop words."""
    if not text:
        return []
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    return [w for w, _ in Counter(filtered).most_common(top_n)]


def generate_key_takeaways(title: str, summary: str, content: str) -> List[str]:
    """Generate 2-3 key takeaway bullet points for an article."""
    points = []
    if title:
        points.append(title.strip())

    body = summary or content or ""
    if body:
        sentences = [s.strip() for s in re.split(r'[.!?]+', body) if len(s.strip()) > 15]
        for s in sentences:
            if s not in points and len(points) < 3:
                points.append(s)

    if not points:
        points = ["Key details and breaking analysis published."]
    return points
