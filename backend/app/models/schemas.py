from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class ChatQueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The user question to match against the FAQ knowledge base.",
        examples=["What payment methods do you accept?"]
    )

    @field_validator("question")
    @classmethod
    def validate_and_strip_question(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty or contain only whitespace.")
        if len(cleaned) > 500:
            raise ValueError("Question exceeds maximum length of 500 characters.")
        return cleaned

class FAQItem(BaseModel):
    id: int
    category: str
    question: str
    answer: str
    keywords: List[str] = Field(default_factory=list)

class ChatResponse(BaseModel):
    answer: str
    matched_question: Optional[str] = None
    category: Optional[str] = None
    confidence: float
    is_fallback: bool
    suggestions: List[str] = Field(default_factory=list)
    response_time_ms: float

class HealthResponse(BaseModel):
    status: str
    indexed_faqs: int
    similarity_threshold: float
    version: str

class FAQListResponse(BaseModel):
    total: int
    categories: List[str]
    faqs: List[FAQItem]
