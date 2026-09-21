"""
Unit tests for FAQMatcher similarity engine.
"""

import pytest
from backend.app.nlp.matcher import FAQMatcher

@pytest.fixture(scope="module")
def matcher():
    return FAQMatcher()

def test_exact_question_match(matcher):
    query = "What payment methods do you accept?"
    result = matcher.match(query)
    assert result["is_fallback"] is False
    assert result["matched_question"] == "What payment methods do you accept?"
    assert result["category"] == "Payment & Billing"
    assert result["confidence"] > 0.85
    assert len(result["answer"]) > 20

def test_rephrased_payment_question(matcher):
    query = "Which methods can I use to pay?"
    result = matcher.match(query)
    assert result["is_fallback"] is False
    assert result["matched_question"] == "What payment methods do you accept?"
    assert result["confidence"] >= matcher.threshold

def test_rephrased_password_question(matcher):
    query = "How do I change my password?"
    result = matcher.match(query)
    assert result["is_fallback"] is False
    assert result["matched_question"] == "How can I reset or change my account password?"
    assert result["category"] == "Account & Security"

def test_out_of_domain_query_triggers_fallback(matcher):
    query = "What is the capital of France and what is the weather today?"
    result = matcher.match(query)
    assert result["is_fallback"] is True
    assert result["matched_question"] is None
    assert result["confidence"] < matcher.threshold
    assert "knowledge base" in result["answer"]
    assert len(result["suggestions"]) > 0

def test_punctuation_and_caps_insensitivity(matcher):
    query = "WHAT PAYMENT METHODS DO YOU ACCEPT???!!!!"
    result = matcher.match(query)
    assert result["is_fallback"] is False
    assert result["matched_question"] == "What payment methods do you accept?"
    assert result["confidence"] > 0.85

def test_empty_and_whitespace_query(matcher):
    result = matcher.match("   ")
    assert result["is_fallback"] is True
    assert result["confidence"] == 0.0

def test_suggestions_present(matcher):
    result = matcher.match("order")
    assert len(result["suggestions"]) > 0
