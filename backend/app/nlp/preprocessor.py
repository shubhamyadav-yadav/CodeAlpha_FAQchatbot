"""
Text preprocessing module for FAQ Chatbot.

Provides text cleaning, normalization, contraction expansion, tokenization,
WordNet lemmatization, pertainym resolution for adverbs, and selective
stopword filtering tailored for Question Answering (QA) similarity matching.
"""

import re
from typing import List, Set
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords, wordnet as wn

import os

# Serverless / read-only filesystem support (e.g. Vercel, AWS Lambda)
tmp_nltk_dir = os.environ.get("NLTK_DATA", "/tmp/nltk_data")
if tmp_nltk_dir not in nltk.data.path:
    nltk.data.path.append(tmp_nltk_dir)

# Ensure required NLTK resources are available
for resource in ["punkt", "punkt_tab", "wordnet", "stopwords", "averaged_perceptron_tagger"]:
    try:
        nltk.data.find(f"tokenizers/{resource}" if "punkt" in resource else f"corpora/{resource}")
    except (LookupError, AttributeError):
        try:
            nltk.download(resource, quiet=True)
        except Exception:
            try:
                nltk.download(resource, download_dir=tmp_nltk_dir, quiet=True)
            except Exception:
                pass

# Common English contractions dictionary
CONTRACTIONS = {
    r"\bcan't\b": "cannot",
    r"\bwon't\b": "will not",
    r"\bn't\b": " not",
    r"\bi'm\b": "i am",
    r"\bwhat's\b": "what is",
    r"\bwhere's\b": "where is",
    r"\bhow's\b": "how is",
    r"\bthere's\b": "there is",
    r"\bthat's\b": "that is",
    r"\bit's\b": "it is",
    r"\blet's\b": "let us",
    r"\b're\b": " are",
    r"\b've\b": " have",
    r"\b'd\b": " would",
    r"\b'll\b": " will",
}

# Filler stop words to remove: low information tokens
# We keep question intent words (how, what, where, why, when, who, which)
# and negation (not, no) because they significantly impact sentence meaning.
DEFAULT_PRESERVED_WORDS = {
    "how", "what", "where", "why", "when", "who", "which",
    "can", "could", "may", "might", "will", "would",
    "not", "no", "never"
}

class TextPreprocessor:
    """
    Modular text preprocessor for question normalization and lemmatization.
    """

    def __init__(self, preserve_question_words: bool = True):
        self.lemmatizer = WordNetLemmatizer()
        try:
            base_stopwords = set(stopwords.words("english"))
        except Exception:
            base_stopwords = set()
            
        if preserve_question_words:
            self.stop_words: Set[str] = base_stopwords - DEFAULT_PRESERVED_WORDS
        else:
            self.stop_words = base_stopwords

    def expand_contractions(self, text: str) -> str:
        """Expands common English contractions."""
        text_lower = text.lower()
        for pattern, replacement in CONTRACTIONS.items():
            text_lower = re.sub(pattern, replacement, text_lower)
        return text_lower

    def clean_text(self, text: str) -> str:
        """
        Cleans text: expands contractions, removes special symbols and punctuation,
        and normalizes whitespace.
        """
        if not text:
            return ""
        # Expand contractions
        cleaned = self.expand_contractions(text)
        # Keep alphanumeric characters and whitespace
        cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
        # Normalize multiple spaces into single space
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def tokenize(self, text: str) -> List[str]:
        """Tokenizes text using NLTK or regex fallback."""
        if not text:
            return []
        try:
            return nltk.word_tokenize(text)
        except Exception:
            return text.split()

    def lemmatize_token(self, token: str) -> str:
        """
        Lemmatizes a single token across verb and noun forms.
        """
        # Verb form first (e.g. paying -> pay, cancelled -> cancel, shipping -> ship)
        lemma_v = self.lemmatizer.lemmatize(token, pos="v")
        # Noun form next (e.g. methods -> method, invoices -> invoice)
        lemma_n = self.lemmatizer.lemmatize(lemma_v, pos="n")
        return lemma_n

    def get_derivational_forms(self, lemma: str) -> List[str]:
        """Convenience method for retrieving WordNet derivational forms of a lemma."""
        return self.get_related_forms(lemma, lemma)

    def get_related_forms(self, token: str, lemma: str) -> List[str]:
        """
        Retrieves derivationally related forms and adverb pertainyms from WordNet.
        For example:
        - 'payment' -> 'pay'
        - 'shipping' -> 'ship'
        - 'cancellation' -> 'cancel'
        - 'internationally' -> 'international'
        - 'permanently' -> 'permanent'
        """
        related_tokens: List[str] = []
        if len(token) <= 3:
            return related_tokens

        try:
            # 1. Check pertainyms for adverbs (e.g. internationally -> international)
            if token.endswith("ly"):
                adv_lemmas = wn.lemmas(token, pos=wn.ADV)
                for al in adv_lemmas:
                    for pert in al.pertainyms():
                        p_name = pert.name().lower()
                        if p_name != token and p_name.isalpha():
                            related_tokens.append(p_name)

            # 2. Check derivational forms for the lemma
            for l in wn.lemmas(lemma):
                for related in l.derivationally_related_forms():
                    rel_name = related.name().lower()
                    if rel_name != lemma and len(rel_name) > 2 and rel_name.isalpha():
                        related_tokens.append(rel_name)
                        if len(related_tokens) >= 2:
                            break
                if len(related_tokens) >= 2:
                    break
        except Exception:
            pass

        return related_tokens

    def preprocess(self, text: str, include_derivations: bool = True) -> str:
        """
        Full preprocessing pipeline:
        1. Clean and normalize text
        2. Tokenize
        3. Filter out non-essential stop words
        4. Lemmatize tokens
        5. Optionally enrich with morphological derivations & pertainyms
        6. Return clean processed string
        """
        cleaned = self.clean_text(text)
        if not cleaned:
            return ""

        tokens = self.tokenize(cleaned)
        processed_tokens: List[str] = []

        for token in tokens:
            if token in self.stop_words:
                continue

            lemma = self.lemmatize_token(token)
            processed_tokens.append(lemma)

            if include_derivations:
                related = self.get_related_forms(token, lemma)
                for r in related:
                    if r not in processed_tokens:
                        processed_tokens.append(r)

        return " ".join(processed_tokens)
