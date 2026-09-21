"""
FAQ Similarity Matcher using Dual TF-IDF and Cosine Similarity.

Accurately matches user questions using a dual-representation scoring pipeline:
1. Question-to-Question vector similarity (preserves exact/near-exact phrasing)
2. Question-to-Combined (Keywords + Category) vector similarity (captures rephrased concepts)
Scores are combined using maximum signal blending, evaluated against a calibrated threshold.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.app.config import settings
from backend.app.models.schemas import FAQItem
from backend.app.nlp.preprocessor import TextPreprocessor
from backend.app.nlp.conversational import ConversationalHandler
from backend.app.utils.logger import logger

class FAQMatcher:
    """
    NLP Matching Engine for FAQ retrieval based on TF-IDF Cosine Similarity.
    """

    def __init__(
        self,
        dataset_path: Optional[Path] = None,
        threshold: Optional[float] = None,
        fallback_message: Optional[str] = None
    ):
        self.dataset_path = dataset_path or settings.DATASET_PATH
        self.threshold = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD
        self.fallback_message = fallback_message or settings.FALLBACK_RESPONSE
        
        self.preprocessor = TextPreprocessor(preserve_question_words=True)
        self.faqs: List[FAQItem] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.question_matrix = None
        self.combined_matrix = None

        self._load_and_index_dataset()

    def _load_and_index_dataset(self) -> None:
        """Loads FAQs from JSON file and builds the TF-IDF index."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"FAQ dataset file not found at: {self.dataset_path}")

        logger.info(f"Loading FAQ dataset from {self.dataset_path}")
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self.faqs = [FAQItem(**item) for item in raw_data]
        if not self.faqs:
            raise ValueError("FAQ dataset is empty!")

        question_corpus = []
        combined_corpus = []

        for faq in self.faqs:
            # 1. Direct Question preprocessed text
            q_proc = self.preprocessor.preprocess(faq.question, include_derivations=True)
            question_corpus.append(q_proc)

            # 2. Combined Question + Keywords + Category preprocessed text
            kw_str = " ".join(faq.keywords)
            c_proc = self.preprocessor.preprocess(
                f"{faq.question} {kw_str} {faq.category}",
                include_derivations=True
            )
            combined_corpus.append(c_proc)

        # Fit single unified vectorizer over all corpus documents
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1
        )
        self.vectorizer.fit(question_corpus + combined_corpus)

        self.question_matrix = self.vectorizer.transform(question_corpus)
        self.combined_matrix = self.vectorizer.transform(combined_corpus)

        logger.info(
            f"Indexed {len(self.faqs)} FAQs with {self.question_matrix.shape[1]} vocabulary features."
        )

    def get_categories(self) -> List[str]:
        """Returns sorted list of unique FAQ categories."""
        return sorted(list(set(faq.category for faq in self.faqs)))

    def get_faqs_by_category(self, category: str) -> List[FAQItem]:
        """Returns all FAQs belonging to a category."""
        return [faq for faq in self.faqs if faq.category.lower() == category.lower()]

    def match(
        self,
        query: str,
        custom_threshold: Optional[float] = None
    ) -> Dict:
        """
        Matches a user query against the FAQ dataset using dual-representation similarity.

        Returns a dictionary containing:
        - answer (str): Best FAQ answer or fallback message
        - matched_question (str or None): Question text of the matched FAQ
        - category (str or None): Category of the matched FAQ
        - confidence (float): Cosine similarity score [0.0 - 1.0]
        - is_fallback (bool): True if confidence fell below threshold
        - suggestions (list): Suggested related FAQ questions
        """
        active_threshold = custom_threshold if custom_threshold is not None else self.threshold

        # Step 0: Check conversational and chitchat intents (greetings, pleasantries, identity)
        cleaned_text = self.preprocessor.clean_text(query)
        chitchat = ConversationalHandler.handle_conversational_query(cleaned_text)
        if chitchat:
            logger.info(f"Query '{query}' resolved as conversational intent: {chitchat['matched_question']}")
            # Provide popular starter questions
            suggestions = [self.faqs[i].question for i in [0, 6, 3] if i < len(self.faqs)]
            return {
                **chitchat,
                "suggestions": suggestions
            }

        # Step 1: Preprocess user query for FAQ matching
        processed_query = self.preprocessor.preprocess(query, include_derivations=True)
        if not processed_query.strip():
            return {
                "answer": self.fallback_message,
                "matched_question": None,
                "category": None,
                "confidence": 0.0,
                "is_fallback": True,
                "suggestions": [f.question for f in self.faqs[:3]]
            }

        # Step 2: Vectorize user query
        query_vector = self.vectorizer.transform([processed_query])

        # Step 3: Compute Cosine Similarity against question and combined matrices
        sim_q = cosine_similarity(query_vector, self.question_matrix)[0]
        sim_c = cosine_similarity(query_vector, self.combined_matrix)[0]

        # Step 4: Blend scores: prioritize direct question match when strong,
        # otherwise leverage keyword expansion
        similarities = np.maximum(sim_q, sim_c * 0.95)

        # Step 5: Find best match
        sorted_indices = np.argsort(similarities)[::-1]
        best_idx = int(sorted_indices[0])
        best_score = float(similarities[best_idx])

        # Compile secondary suggestions for user convenience
        suggestions: List[str] = []
        for idx in sorted_indices:
            if idx != best_idx and similarities[idx] > 0.10:
                suggestions.append(self.faqs[idx].question)
                if len(suggestions) >= 3:
                    break

        if not suggestions:
            suggestions = [self.faqs[i].question for i in [0, 3, 6] if i < len(self.faqs)]

        # Step 6: Evaluate against confidence threshold
        if best_score >= active_threshold:
            matched_faq = self.faqs[best_idx]
            logger.info(
                f"Query '{query}' matched FAQ #{matched_faq.id} "
                f"('{matched_faq.question}') with confidence {best_score:.4f}"
            )
            return {
                "answer": matched_faq.answer,
                "matched_question": matched_faq.question,
                "category": matched_faq.category,
                "confidence": round(best_score, 4),
                "is_fallback": False,
                "suggestions": suggestions
            }
        else:
            logger.info(
                f"Query '{query}' fell below threshold (score={best_score:.4f} < {active_threshold}). "
                "Triggering fallback."
            )
            return {
                "answer": self.fallback_message,
                "matched_question": None,
                "category": None,
                "confidence": round(best_score, 4),
                "is_fallback": True,
                "suggestions": suggestions
            }
