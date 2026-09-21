"""
FAQ knowledge base and system health router.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from backend.app.config import settings
from backend.app.models.schemas import FAQListResponse, HealthResponse
from backend.app.nlp.matcher import FAQMatcher
from backend.app.routers.chat import get_matcher

router = APIRouter(prefix="/api/v1", tags=["Knowledge Base & Health"])

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check and engine status",
    description="Returns the operating status of the NLP chatbot engine."
)
async def health_check(matcher: FAQMatcher = Depends(get_matcher)) -> HealthResponse:
    return HealthResponse(
        status="healthy",
        indexed_faqs=len(matcher.faqs),
        similarity_threshold=matcher.threshold,
        version=settings.PROJECT_VERSION
    )

@router.get(
    "/faqs",
    response_model=FAQListResponse,
    status_code=status.HTTP_200_OK,
    summary="List available FAQs",
    description="Returns the FAQ dataset, optionally filtered by category."
)
async def list_faqs(
    category: Optional[str] = Query(None, description="Filter FAQs by category"),
    matcher: FAQMatcher = Depends(get_matcher)
) -> FAQListResponse:
    if category:
        faqs = matcher.get_faqs_by_category(category)
    else:
        faqs = matcher.faqs

    return FAQListResponse(
        total=len(faqs),
        categories=matcher.get_categories(),
        faqs=faqs
    )

@router.get(
    "/categories",
    response_model=list[str],
    status_code=status.HTTP_200_OK,
    summary="List FAQ categories"
)
async def list_categories(matcher: FAQMatcher = Depends(get_matcher)) -> list[str]:
    return matcher.get_categories()
