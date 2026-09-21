"""
NLP Matching Benchmark Suite.

Evaluates matching accuracy across direct, rephrased, perturbed,
and out-of-domain queries to empirically validate the threshold and NLP pipeline.
"""

import pytest
from backend.app.nlp.matcher import FAQMatcher

BENCHMARK_DATASET = [
    # (Query, Expected FAQ ID or None for Fallback)
    ("What payment methods do you accept?", 1),
    ("Which methods can I use to pay?", 1),
    ("How can I pay for my items?", 1),
    ("What payment options are available?", 1),
    ("How do I update my credit card on file?", 2),
    ("Where can I get my invoice?", 3),
    ("How can I reset or change my account password?", 4),
    ("How do I change my password?", 4),
    ("I forgot my password, how can I recover it?", 4),
    ("How do I turn on 2FA?", 5),
    ("How do I delete my account?", 6),
    ("Where is my package?", 7),
    ("Can I track my shipment?", 7),
    ("Can I cancel my order?", 8),
    ("How long does shipping take?", 9),
    ("Do you ship internationally to Canada or UK?", 10),
    ("What is your refund policy?", 11),
    ("How long until I receive my refund in my bank?", 12),
    ("How can I talk to a real person in support?", 16),
    ("What are your business hours?", 17),
    
    # Out of domain queries (Must Trigger Fallback -> None)
    ("What is the weather in Tokyo today?", None),
    ("Can you write a poem about autumn trees?", None),
    ("Who won the soccer world cup in 2022?", None),
    ("Explain the theory of relativity to me.", None),
]

@pytest.fixture(scope="module")
def matcher():
    return FAQMatcher()

def test_nlp_benchmark_accuracy(matcher):
    correct_matches = 0
    total = len(BENCHMARK_DATASET)
    results = []

    for query, expected_id in BENCHMARK_DATASET:
        match_result = matcher.match(query)
        if expected_id is None:
            passed = match_result["is_fallback"] is True
            matched_id = None if match_result["is_fallback"] else "Incorrect Match"
        else:
            matched_id = None
            if not match_result["is_fallback"]:
                # find matched FAQ ID
                for faq in matcher.faqs:
                    if faq.question == match_result["matched_question"]:
                        matched_id = faq.id
                        break
            passed = (matched_id == expected_id)

        if passed:
            correct_matches += 1

        results.append({
            "query": query,
            "expected_id": expected_id,
            "matched_id": matched_id,
            "confidence": match_result["confidence"],
            "passed": passed
        })

    accuracy = (correct_matches / total) * 100
    print(f"\n--- NLP BENCHMARK RESULTS: {correct_matches}/{total} ({accuracy:.1f}%) ---")
    for r in results:
        status_str = "PASS" if r["passed"] else "FAIL"
        print(f"[{status_str}] '{r['query']}' -> Matched: {r['matched_id']}, Expected: {r['expected_id']}, Score: {r['confidence']}")

    assert accuracy >= 85.0, f"Benchmark accuracy {accuracy:.1f}% is below 85% requirement!"
