"""
Chat routing module for user query handling and FAQ matching.
"""

import time
from fastapi import APIRouter, HTTPException, Request, Depends, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.app.config import settings
from backend.app.models.schemas import ChatQueryRequest, ChatResponse
from backend.app.nlp.matcher import FAQMatcher
from backend.app.utils.logger import logger

router = APIRouter(prefix="/api/v1", tags=["Chat"])
limiter = Limiter(key_func=get_remote_address)

# Global matcher instance cached in memory
_matcher: FAQMatcher | None = None

def get_matcher() -> FAQMatcher:
    global _matcher
    if _matcher is None:
        _matcher = FAQMatcher()
    return _matcher

@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit user question and receive best matching FAQ answer",
    description="Processes user input via NLP pipeline and returns the most relevant FAQ answer using TF-IDF cosine similarity."
)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def chat_endpoint(
    request: Request,
    payload: ChatQueryRequest,
    matcher: FAQMatcher = Depends(get_matcher)
) -> ChatResponse:
    start_time = time.perf_counter()
    question = payload.question.strip()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty or contain only whitespace."
        )

    try:
        match_result = matcher.match(question)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return ChatResponse(
            answer=match_result["answer"],
            matched_question=match_result.get("matched_question"),
            category=match_result.get("category"),
            confidence=match_result["confidence"],
            is_fallback=match_result["is_fallback"],
            suggestions=match_result.get("suggestions", []),
            response_time_ms=duration_ms
        )
    except Exception as exc:
        logger.error(f"Unexpected error processing query '{question}': {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request. Please try again later."
        )
