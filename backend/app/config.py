import os
from pathlib import Path
from dataclasses import dataclass, field

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Robust path resolution across local and Vercel serverless environments
def _resolve_dataset_path() -> Path:
    candidates = [
        BACKEND_DIR / "app" / "data" / "faqs.json",
        BASE_DIR / "backend" / "app" / "data" / "faqs.json",
        Path.cwd() / "backend" / "app" / "data" / "faqs.json"
    ]
    for c in candidates:
        if c.exists():
            return c
    return BACKEND_DIR / "app" / "data" / "faqs.json"

@dataclass
class Settings:
    PROJECT_NAME: str = "FAQ Chatbot NLP"
    PROJECT_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1")
    
    # NLP & Matching Configuration
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.30"))
    MAX_QUERY_LENGTH: int = int(os.getenv("MAX_QUERY_LENGTH", "500"))
    RATE_LIMIT_DEFAULT: str = os.getenv("RATE_LIMIT", "60/minute")
    
    # Paths
    DATASET_PATH: Path = _resolve_dataset_path()
    FRONTEND_DIR: Path = BASE_DIR / "frontend"
    
    # Fallback message
    FALLBACK_RESPONSE: str = (
        "I'm sorry, I couldn't find a relevant answer to that question in our knowledge base. "
        "Please try rephrasing your question or contact our support team at support@example.com."
    )
    
    # CORS
    ALLOWED_ORIGINS: list[str] = field(default_factory=lambda: ["*"])

settings = Settings()
