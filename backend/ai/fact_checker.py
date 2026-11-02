"""
MEKA Truth Intelligence & Fact-Checking Engine 3.0
Multi-Source Cross-Corroboration, Sensationalism Indexing, Claim Decomposition & Bias Analysis.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

# Comprehensive Global Source Reliability Index (0-100)
SOURCE_RELIABILITY_MAP: Dict[str, int] = {
    "reuters": 98,
    "associated press": 98,
    "ap news": 98,
    "bbc": 96,
    "bbc news": 96,
    "bbc sport": 94,
    "bloomberg": 96,
    "nature": 98,
    "science": 98,
    "the hindu": 93,
    "indian express": 91,
    "financial times": 95,
    "the wall street journal": 94,
    "wsj": 94,
    "the guardian": 92,
    "techcrunch": 90,
    "the verge": 89,
    "wired": 90,
    "ars technica": 91,
    "ndtv": 88,
    "times of india": 85,
    "hindustan times": 85,
    "espn": 91,
    "cricinfo": 93,
    "al jazeera": 90,
    "cnbc": 91,
    "who": 99,
    "nasa": 99,
    "nih": 99,
}

# Lexical Clickbait & Sensationalism Flags
SENSATIONAL_PATTERNS = [
    r'\b(?:you won\'?t believe|shocking|jaw-?dropping|mind-?blowing|unbelievable|astonishing)\b',
    r'\b(?:destroys|slams|eviscerates|blasts|rips into|obliterates|shatters|explodes|nukes)\b',
    r'\b(?:secret trick|hidden truth|what they aren\'?t telling you|conspiracy|hoax)\b',
    r'\b(?:miracle cure|instant fix|guaranteed to|one weird trick)\b',
    r'\b(?:horrifying|terrifying|apocalypse|catastrophe strikes|end of days|panic)\b',
    r'\b(?:goes viral|breaks the internet|meltdown|freaks out|loses mind)\b',
    r'\b(?:they don\'?t want you to know|censored video|leaked footage)\b',
    r'\b(?:exposed|bombshell|unmasked|humiliated|brutal takedown)\b',
]

# Disinformation, Pseudoscience & Fake News Markers (Severe Credibility Penalty)
DISINFORMATION_PATTERNS = [
    r'\b(?:cure (?:for )?(?:cancer|diabetes|aids|hiv|alzheimer\'?s|covid)(?: [a-z]+)* (?:overnight|in \d+ days|instantly))\b',
    r'\b(?:secret (?:miracle )?cure|instant (?:miracle )?remedy)\b',
    r'\b(?:vaccines? (?:contain microchips?|cause autism|depopulation|poison|are toxic))\b',
    r'\b(?:chemtrails|flat earth|5g causes|reptilian|illuminati|deep state false flag)\b',
    r'\b(?:crisis actors?|faked moon landing|hologram plane|haarp weather control)\b',
    r'\b(?:doctors? (?:hate|fear|banned) (?:this|it)|banned by (?:doctors|big pharma)|secret natural cure)\b',
    r'\b(?:elon musk (?:giving away|doubles your) crypto|send (?:btc|eth) to receive)\b',
    r'\b(?:banks? closing down nationwide tomorrow|all ATMs shutdown panic)\b',
    r'\b(?:wake up sheeple|share before (?:it\'?s )?(?:deleted|banned|censored))\b',
    r'\b(?:anonymous 4chan post claims|viral whatsapp forward warns|unnamed blogger reveals)\b',
]

# Verifiable Journalistic Evidence Indicators
FACTUAL_INDICATORS = [
    r'\b(?:confirmed|according to|officials? reported|data shows|study published|reuters reported|statement released)\b',
    r'\b(?:spokesperson said|ministry announced|department stated|press release|peer-reviewed|published in)\b',
    r'\b(?:investigation revealed|statistics indicate|official record|audit|ratified|documented|reports?)\b',
    r'\b(?:\d+(\.\d+)?%|\$\d+|\d+\s*(?:million|billion|trillion|percent|crore|lakh))\b',
    r'\b(?:parliament passed|court ruled|un security council|world health organization|clinical trials?)\b',
    r'\b(?:satellite imagery|seismological data|sec filing|regulatory approval|patent filed)\b',
]

# Subject Matter Keyword Extraction for Cross-Corroboration
TOPIC_ENTITIES = [
    r'\b(?:india|us|usa|china|russia|uk|europe|japan|un|who|nato|brics|g20)\b',
    r'\b(?:ai|artificial intelligence|semiconductor|quantum|space|nasa|isro|malaria|cancer|vaccine|climate|ev)\b',
    r'\b(?:gdp|inflation|federal reserve|rbi|markets|stocks|treasury|crude oil|energy)\b',
    r'\b(?:election|parliament|congress|supreme court|legislation|treaty|accord)\b',
]


# Distinctive named publishers/agencies used for lexical attribution checks.
# Generic words ("nature", "science") are deliberately excluded to avoid false matches.
NAMED_EVIDENCE_SOURCES = [
    "reuters", "associated press", "ap news", "bbc", "bloomberg",
    "the hindu", "indian express", "financial times", "wall street journal",
    "wsj", "the guardian", "techcrunch", "the verge", "ars technica",
    "ndtv", "times of india", "hindustan times", "espn", "cricinfo",
    "al jazeera", "cnbc", "nasa", "nih", "world health organization",
]


def _find_named_sources(query: str) -> List[str]:
    found = []
    for name in NAMED_EVIDENCE_SOURCES:
        if re.search(r'\b' + re.escape(name) + r'\b', query, re.IGNORECASE):
            found.append(name)
    if re.search(r'\bWHO\b', query):
        found.append("who")
    return found


def calculate_sensationalism_score(title: str, text: str) -> int:
    """
    Compute fine-grained Sensationalism & Clickbait Index (0 to 100%).
    Penalizes hyperbolic rhetoric, clickbait phrasing, excessive punctuation, and ALL-CAPS styling.
    """
    if not title:
        return 10

    combined = f"{title} {text or ''}"
    lower = combined.lower()

    score = 4  # Baseline journalistic variance

    # 1. Lexical pattern matching
    for pat in SENSATIONAL_PATTERNS:
        matches = len(re.findall(pat, lower))
        score += matches * 14

    # 2. Sensational punctuation penalties (!!, ???, ?!)
    punct_count = title.count('!') + (title.count('?') if title.count('?') > 1 else 0)
    score += punct_count * 10

    # 3. Aggressive uppercase words in title (ignoring acronyms under 4 chars like WHO, NASA, RBI)
    caps_words = [w for w in title.split() if w.isupper() and len(w) >= 4 and w not in {'SAMACHAR', 'COVID', 'BRICS', 'NATO', 'NASA', 'ISRO'}]
    score += len(caps_words) * 12

    # 4. First-person clickbait phrasing ("Why I...", "This is why you...")
    if re.search(r'\b(?:why (?:i|you) should|here is why you)\b', lower):
        score += 15

    return min(100, max(0, score))


def extract_key_claims(title: str, text: str, corroborating_count: int = 1) -> List[Dict[str, Any]]:
    """
    Decompose news articles into atomic, structured claims.
    Categorizes claims into Official Statements, Quantitative Assertions, or Reported Claims.
    """
    claims = []
    combined = f"{title}. {text or ''}"
    
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', combined) if len(s.strip()) > 20]
    
    seen = set()
    for sentence in sentences:
        if len(claims) >= 4:
            break
        
        has_stats = bool(re.search(r'\b(?:\d+(?:\.\d+)?%?|\$\d+|\bmillion\b|\bbillion\b|\btrillion\b|\bcrore\b|\byears?\b)', sentence, re.IGNORECASE))
        has_quote = bool(re.search(r'["\u201C\u201D]([^"\u201C\u201D]+)["\u201C\u201D]', sentence))
        has_fact_kw = any(re.search(p, sentence, re.IGNORECASE) for p in FACTUAL_INDICATORS)
        
        clean_s = sentence.replace('"', '').strip()
        if (has_stats or has_quote or has_fact_kw) and clean_s not in seen:
            seen.add(clean_s)
            
            if has_quote:
                status = "Official Statement"
                ev = "Direct on-record quote in the source text"
                conf = 90
            elif has_stats:
                status = "Data-Backed Assertion"
                ev = "Quantitative figure reported in the source text"
                conf = 85
            else:
                status = "Reported Claim"
                if corroborating_count >= 2:
                    ev = f"Reported across {corroborating_count} named sources"
                    conf = 80
                else:
                    ev = "Reported in the source text only; not independently corroborated"
                    conf = 55
                
            claims.append({
                "claim": clean_s if len(clean_s) <= 180 else clean_s[:177] + "...",
                "status": status,
                "evidence": ev,
                "confidence_score": conf
            })
            
    if not claims and title:
        claims.append({
            "claim": title.strip(),
            "status": "Reported Claim",
            "evidence": "Headline claim; no independent corroboration retrieved",
            "confidence_score": 50
        })
        
    return claims


def evaluate_article_credibility(
    title: str,
    summary: str,
    content: str,
    source_name: Optional[str] = None,
    corroborating_count: int = 1
) -> Dict[str, Any]:
    """
    MEKA 3.5 Multi-Factor Credibility & Disinformation Scoring:
    - Source Reliability (40%)
    - Inverse Sensationalism / Clickbait Penalty (25%)
    - Cross-Source Wire Corroboration (15%)
    - Empirical Factual Evidence Density (10%)
    - Disinformation & Pseudoscience Detection (-50% penalty if detected)
    """
    text = f"{summary or ''} {content or ''}"
    sensationalism = calculate_sensationalism_score(title, text)
    
    src_key = (source_name or "").lower().strip()
    source_score = SOURCE_RELIABILITY_MAP.get(src_key, 88)
    
    corroboration_bonus = min(15, max(0, (corroborating_count - 1) * 5))
    
    factual_bonus = 0
    fact_matches = sum(1 for p in FACTUAL_INDICATORS if re.search(p, text.lower()))
    factual_bonus = min(12, fact_matches * 3)

    # Check for active disinformation / fake news markers
    disinfo_matches = [p for p in DISINFORMATION_PATTERNS if re.search(p, f"{title} {text}".lower())]
    disinfo_penalty = len(disinfo_matches) * 45
        
    raw_cred = (0.50 * source_score) + (0.30 * (100 - sensationalism)) + corroboration_bonus + factual_bonus - disinfo_penalty
    credibility = int(min(99, max(10, round(raw_cred))))
    
    if disinfo_penalty > 0 or credibility < 40 or sensationalism > 70:
        status = "disputed"
        bias = "🔴 High Risk / Disinformation Warning"
    elif credibility >= 85 and corroborating_count >= 2 and sensationalism <= 25:
        status = "verified"
        bias = "Neutral Analytic (Wire Grade)" if source_score >= 94 else "Center-Editorial Reporting"
    elif credibility >= 75 and corroborating_count >= 2:
        status = "corroborated"
        bias = "Center-Editorial Reporting"
    elif credibility >= 55:
        status = "developing"
        bias = "Developing / Uncorroborated"
    elif sensationalism > 50:
        status = "disputed"
        bias = "Sensationalized / High Hype"
    else:
        status = "unverified"
        bias = "General News Wire"
        
    claims = extract_key_claims(title, text, corroborating_count)
    
    return {
        "credibility_score": credibility,
        "sensationalism_score": sensationalism,
        "fact_check_status": status,
        "bias_spectrum": bias,
        "key_claims": claims,
        "corroboration_count": max(0, corroborating_count),
        "disinformation_flags": len(disinfo_matches)
    }


def verify_custom_claim(query_text: str) -> Dict[str, Any]:
    """Interactive tool to verify any user-submitted claim or news headline with fake news detection."""
    if not query_text or len(query_text.strip()) < 5:
        return {
            "verdict": "Invalid Query",
            "credibility_score": 0,
            "sensationalism_score": 0,
            "analysis": "Please provide a complete news headline or factual claim to analyze.",
            "claims_breakdown": [],
            "corroborated_sources": []
        }
        
    lower_query = query_text.lower()
    sensationalism = calculate_sensationalism_score(query_text, "")
    claims = extract_key_claims(query_text, "")
    has_quantitative = bool(re.search(
        r'\b(?:\d+(?:\.\d+)?%|\$\d+(?:\.\d+)?|\d+\s*(?:million|billion|trillion|percent|crore|lakh))',
        lower_query,
    ))
    named_sources = _find_named_sources(query_text)
    
    # Check for disinformation / conspiracy / fake news markers
    disinfo_found = [p for p in DISINFORMATION_PATTERNS if re.search(p, lower_query)]

    if disinfo_found:
        verdict = "🔴 False Claim / Pseudoscience Alert"
        credibility = max(8, 25 - len(disinfo_found) * 10)
        sensationalism = max(75, sensationalism)
        analysis = "⚠️ High Disinformation Alert: This statement matches known pseudoscience, financial scam, or conspiratorial propaganda patterns that lack institutional or peer-reviewed evidence."
        sources = ["Heuristic disinformation pattern match"]
    elif sensationalism >= 65:
        verdict = "🔴 High Sensationalism / Unverified"
        credibility = max(20, 100 - sensationalism)
        analysis = "This claim exhibits sensationalized phrasing, emotive hyperbole, or clickbait rhetoric lacking accredited primary source attribution."
        sources = []
    elif named_sources:
        source_score = max(SOURCE_RELIABILITY_MAP.get(name, 88) for name in named_sources)
        verdict = "Attributed Claim — Not Independently Verified"
        credibility = min(92, max(80, source_score - 5))
        analysis = (
            f"The claim cites {', '.join(named_sources)}. This is a lexical attribution check only; "
            "no live evidence was retrieved and no independent corroboration was performed."
        )
        sources = []
    elif has_quantitative:
        verdict = "Developing / Plausible Claim"
        credibility = 60
        analysis = (
            "The statement includes quantitative details but does not name a verifiable source. "
            "No evidence was retrieved; treat this claim as unverified."
        )
        sources = []
    else:
        verdict = "🔴 Unverified — Insufficient Evidence"
        credibility = min(45, max(10, 45 - sensationalism // 3))
        analysis = (
            "No named, verifiable source or retrievable evidence was provided. "
            "This tool performs lexical screening only; treat the claim as unverified."
        )
        sources = []
        
    return {
        "verdict": verdict,
        "credibility_score": credibility,
        "sensationalism_score": sensationalism,
        "analysis": analysis,
        "claims_breakdown": claims,
        "corroborated_sources": sources
    }
