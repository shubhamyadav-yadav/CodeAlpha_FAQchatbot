"""
Unit tests for Conversational and Chitchat Intent Handler.
"""

import pytest
from backend.app.nlp.matcher import FAQMatcher
from backend.app.nlp.conversational import ConversationalHandler

@pytest.fixture(scope="module")
def matcher():
    return FAQMatcher()

def test_greeting_how_are_you_exact(matcher):
    # Exactly what user showed in image: "hi how are you"
    res = matcher.match("hi how are you")
    assert res["is_fallback"] is False
    assert res["category"] == "Conversational"
    assert "doing great" in res["answer"].lower() or "doing well" in res["answer"].lower()
    assert res["confidence"] == 1.0

def test_greetings_variations(matcher):
    for greeting in ["hi", "hello", "hey", "good morning", "good evening", "hi there"]:
        res = matcher.match(greeting)
        assert res["is_fallback"] is False, f"Failed for '{greeting}'"
        assert res["category"] == "Conversational"

def test_well_being_variations(matcher):
    for query in ["how are you", "how are you doing", "how's it going", "how is it going"]:
        res = matcher.match(query)
        assert res["is_fallback"] is False, f"Failed for '{query}'"
        assert res["category"] == "Conversational"

def test_identity_and_capabilities(matcher):
    for query in ["who are you", "what is your name", "what can you do", "help"]:
        res = matcher.match(query)
        assert res["is_fallback"] is False, f"Failed for '{query}'"
        assert res["category"] == "Conversational"
        assert "FAQ Assistant" in res["answer"]

def test_gratitude_and_farewell(matcher):
    res_thanks = matcher.match("thank you")
    assert res_thanks["is_fallback"] is False
    assert "welcome" in res_thanks["answer"].lower()

    res_bye = matcher.match("goodbye")
    assert res_bye["is_fallback"] is False
    assert "goodbye" in res_bye["answer"].lower() or "day" in res_bye["answer"].lower()
