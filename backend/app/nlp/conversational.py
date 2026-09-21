"""
Conversational and Chitchat Intent Handler.

Handles common conversational inputs such as greetings, well-being inquiries,
bot identity, gratitude, and goodbyes before querying the knowledge base.
"""

import re
from typing import Dict, Optional

CONVERSATIONAL_INTENTS = [
    # Combined Greeting + Well-being (e.g. "hi how are you")
    {
        "name": "Greeting & Well-being",
        "patterns": [
            r"^(hi|hello|hey|greetings)\s+(how\s+are\s+you|how\s+are\s+you\s+doing|how\s+is\s+it\s+going|hows\s+it\s+going|how\s+do\s+you\s+do)",
            r"^(how\s+are\s+you|how\s+are\s+you\s+doing|how\s+is\s+it\s+going|hows\s+it\s+going|how\s+are\s+things)\s*,?\s*(hi|hello|hey)?$"
        ],
        "answer": "Hello! I'm doing great, thank you for asking! I'm your FAQ Assistant - how can I help you with your account, orders, or payments today?"
    },
    # Simple Well-being (e.g. "how are you")
    {
        "name": "Well-being",
        "patterns": [
            r"^how\s+are\s+you(\s+today|\s+doing)?$",
            r"^how\s+is\s+it\s+going$",
            r"^hows\s+it\s+going$",
            r"^how\s+are\s+things$",
            r"^what\s+is\s+up$",
            r"^whats\s+up$"
        ],
        "answer": "I'm doing well, thank you! I'm here and ready to assist you. Ask me anything about our billing, shipments, or account policies."
    },
    # Greetings (e.g. "hi", "hello", "hey")
    {
        "name": "Greeting",
        "patterns": [
            r"^(hi|hello|hey|heya|howdy|greetings|good\s+morning|good\s+afternoon|good\s+evening|hi\s+there|hello\s+there)$"
        ],
        "answer": "Hello! Welcome to our FAQ Assistant. How can I help you today? You can ask about payment methods, tracking orders, password resets, and more."
    },
    # Bot Identity & Capabilities (e.g. "who are you", "what can you do")
    {
        "name": "Bot Identity & Capabilities",
        "patterns": [
            r"^who\s+are\s+you$",
            r"^what\s+is\s+your\s+name$",
            r"^what\s+are\s+you$",
            r"^what\s+can\s+you\s+do$",
            r"^what\s+do\s+you\s+do$",
            r"^tell\s+me\s+about\s+yourself$",
            r"^can\s+you\s+help\s+me$",
            r"^help(\s+me)?$"
        ],
        "answer": "I am an intelligent FAQ Assistant powered by Natural Language Processing. I can help answer questions about payment methods, order shipments, return policies, account security, and how to reach human support."
    },
    # Gratitude (e.g. "thank you", "thanks")
    {
        "name": "Gratitude",
        "patterns": [
            r"^(thank\s+you|thanks|thanks\s+a\s+lot|thank\s+you\s+very\s+much|thank\s+you\s+so\s+much|much\s+appreciated|appreciate\s+it)$",
            r"^(great\s+thanks|thanks\s+for\s+the\s+help)$"
        ],
        "answer": "You're very welcome! If you have any more questions, feel free to ask anytime."
    },
    # Farewell (e.g. "bye", "goodbye")
    {
        "name": "Farewell",
        "patterns": [
            r"^(bye|goodbye|bye\s+bye|see\s+you|see\s+ya|have\s+a\s+good\s+day|talk\s+to\s+you\s+later|take\s+care)$"
        ],
        "answer": "Goodbye! Have a great day ahead, and don't hesitate to return if you need any further assistance."
    },
    # Acknowledgment (e.g. "ok", "great")
    {
        "name": "Acknowledgment",
        "patterns": [
            r"^(ok|okay|cool|great|awesome|perfect|got\s+it|understood|nice|alright)$"
        ],
        "answer": "Glad to hear! Let me know if there's anything else I can help you with."
    }
]

class ConversationalHandler:
    """Detects and responds to conversational chitchat and pleasantries."""

    @staticmethod
    def handle_conversational_query(cleaned_text: str) -> Optional[Dict]:
        """
        Checks if the cleaned query matches any conversational intent.
        Returns a response dict if matched, otherwise None.
        """
        # Normalize whitespace
        text = re.sub(r"\s+", " ", cleaned_text.strip().lower())
        if not text:
            return None

        for intent in CONVERSATIONAL_INTENTS:
            for pattern in intent["patterns"]:
                if re.search(pattern, text):
                    return {
                        "answer": intent["answer"],
                        "matched_question": intent["name"],
                        "category": "Conversational",
                        "confidence": 1.0,
                        "is_fallback": False,
                    }
        return None
