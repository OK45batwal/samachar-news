from backend.ai.fact_checker import (
    calculate_sensationalism_score,
    evaluate_article_credibility,
    extract_key_claims,
    verify_custom_claim,
)


def test_sensationalism_clickbait_detection():
    clickbait_headline = "YOU WON'T BELIEVE THIS SHOCKING SECRET! SCIENTISTS ARE HORRIFIED!!!"
    score = calculate_sensationalism_score(clickbait_headline, "")
    assert score >= 50

    objective_headline = "Ministry of Health reports 12% increase in seasonal immunization coverage"
    score_clean = calculate_sensationalism_score(objective_headline, "")
    assert score_clean <= 25


def test_claim_extraction():
    text = "Global semiconductor exports reached $540 billion in 2025. 'This confirms steady supply chain stability,' the director stated."
    claims = extract_key_claims("Chip Exports Update", text)
    assert len(claims) >= 1
    assert any(c["status"] in ["Data-Backed Assertion", "Official Statement", "Verified Reporting"] for c in claims)


def test_article_credibility_evaluation():
    title = "WHO Confirms Eradication Milestone with 78% Drop in Mortality"
    summary = "Official surveillance data published by WHO and Gavi confirms major milestone in 18 countries."
    res = evaluate_article_credibility(title, summary, "", source_name="Reuters", corroborating_count=3)
    assert res["credibility_score"] >= 85
    assert res["fact_check_status"] == "verified"
    assert res["sensationalism_score"] <= 20


def test_verify_custom_claim():
    claim = "According to official reports, inflation declined to 2.4% last quarter."
    res = verify_custom_claim(claim)
    assert res["verdict"] in ["Corroborated Statement", "Developing / Plausible Claim"]
    assert res["credibility_score"] >= 60
