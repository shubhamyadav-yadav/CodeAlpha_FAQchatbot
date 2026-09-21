"""
Unit tests for NLP TextPreprocessor.
"""

import pytest
from backend.app.nlp.preprocessor import TextPreprocessor

@pytest.fixture
def preprocessor():
    return TextPreprocessor()

def test_clean_text_lowercasing_and_punctuation(preprocessor):
    raw = "What ARE the payment methods??? (Visa, MasterCard!)"
    cleaned = preprocessor.clean_text(raw)
    assert cleaned == "what are the payment methods visa mastercard"

def test_contraction_expansion(preprocessor):
    raw = "I can't access my account and won't be able to log in."
    expanded = preprocessor.expand_contractions(raw)
    assert "cannot" in expanded
    assert "will not" in expanded

def test_lemmatization_nouns_and_verbs(preprocessor):
    # Plural nouns to singular
    assert preprocessor.lemmatize_token("methods") == "method"
    assert preprocessor.lemmatize_token("invoices") == "invoice"
    assert preprocessor.lemmatize_token("passwords") == "password"
    
    # Verbs to root
    assert preprocessor.lemmatize_token("paying") == "pay"
    assert preprocessor.lemmatize_token("cancelled") == "cancel"
    assert preprocessor.lemmatize_token("tracking") == "track"

def test_derivational_forms(preprocessor):
    derivations = preprocessor.get_derivational_forms("payment")
    assert "pay" in derivations

def test_stopwords_preserves_question_words(preprocessor):
    # Essential QA intent words must not be removed
    text = "how can I pay and what is the fee"
    processed = preprocessor.preprocess(text, include_derivations=False)
    assert "how" in processed
    assert "what" in processed
    assert "pay" in processed
    # Low information filler words should be removed
    assert " the " not in f" {processed} "
    assert " and " not in f" {processed} "

def test_preprocess_empty_and_whitespace(preprocessor):
    assert preprocessor.preprocess("") == ""
    assert preprocessor.preprocess("   ") == ""
    assert preprocessor.preprocess("!@#$%^&*()") == ""
