import pytest
from backend.ai.intelligence import (
    generate_cognitive_depths,
    answer_article_question,
    analyze_wire_perspectives,
    calculate_personal_impact,
)


def test_cognitive_depths_generation():
    title = "Quantum Computing Breakthrough Slashes Cryptographic Latency"
    summary = "Researchers at MIT achieved a fault-tolerant logical qubit operation with 99.9% fidelity."
    content = "The breakthrough solves a 20-year quantum coherence challenge. Financial institutions and cybersecurity agencies are reviewing protocols."
    claims = [
        {"claim": "MIT achieved 99.9% fidelity on fault-tolerant qubits", "status": "Verified Reporting", "confidence_score": 96}
    ]

    depths = generate_cognitive_depths(
        title=title,
        summary=summary,
        content=content,
        key_claims=claims,
        category="Technology",
        source="Nature News",
        credibility_score=94
    )

    assert "radar" in depths
    assert "brief" in depths
    assert "deep" in depths
    assert "eli5" in depths

    # Level 1 Radar checks
    assert len(depths["radar"]["takeaways"]) >= 1
    assert depths["radar"]["reading_time"] == "15 sec"

    # Level 2 Brief checks
    assert "what_happened" in depths["brief"]
    assert "stakeholders" in depths["brief"]

    # Level 4 ELI5 checks
    assert "simple_analogy" in depths["eli5"]
    assert len(depths["eli5"]["jargon_buster"]) > 0


def test_socratic_ask_article():
    article = {
        "title": "Central Bank Holds Benchmark Interest Rate Steady at 5.25%",
        "summary": "Monetary policy committee cites softening headline inflation and stable labor conditions.",
        "content": "Officials emphasized that rate cuts would require further empirical evidence of wage cooling. Mortgage lenders held borrowing costs unchanged.",
        "key_claims": [
            {"claim": "Central Bank benchmark rate remains unchanged at 5.25%", "status": "Official Statement", "confidence_score": 98}
        ],
        "category_name": "Markets",
        "source_name": "Reuters",
        "credibility_score": 96,
        "bias_spectrum": "Neutral Analytic"
    }

    # Test counter-argument question
    ans_counter = answer_article_question(article, "What are the counter-arguments?")
    assert "critics" in ans_counter["answer"].lower() or "skeptics" in ans_counter["answer"].lower()
    assert ans_counter["confidence_score"] == 96

    # Test personal impact question
    ans_impact = answer_article_question(article, "How does this affect my personal wallet and mortgage?")
    assert "wallet" in ans_impact["evidence_tag"].lower() or "impact" in ans_impact["evidence_tag"].lower()

    # Test plain english / ELI5 question
    ans_eli5 = answer_article_question(article, "Explain this like I am 5")
    assert "plain english" in ans_eli5["answer"].lower() or "analogy" in ans_eli5["answer"].lower()


def test_perspective_prism():
    article = {
        "title": "Global Climate Summit Reaches Framework on Transition Finance",
        "category_name": "World Affairs",
        "source_name": "Associated Press",
        "credibility_score": 92
    }
    prism = analyze_wire_perspectives(article)
    assert "consensus_points" in prism
    assert "perspectives" in prism
    assert len(prism["perspectives"]) >= 3
    assert "omission_radar" in prism


def test_personal_impact_simulator():
    article = {
        "title": "Generative AI Code Assistants Double Developer Throughput in Tech Audit",
        "category_name": "Technology"
    }
    impact_dev = calculate_personal_impact(article, persona="developer")
    assert impact_dev["impact_level"] == "High"
    assert "software" in impact_dev["takeaway"].lower() or "developer" in impact_dev["action_item"].lower()

    impact_investor = calculate_personal_impact(article, persona="investor")
    assert "relevance_score" in impact_investor
