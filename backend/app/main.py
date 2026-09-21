"""
Main FastAPI Application Entry Point.

Configures:
- CORS middleware
- Security headers middleware
- Rate limiting and custom exception handlers
- API routers for Chat and FAQ management
- Static file serving for modern white-themed frontend
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from backend.app.config import settings
from backend.app.routers import chat, faqs
from backend.app.routers.chat import limiter, get_matcher
from backend.app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warms the NLP engine and models at startup."""
    logger.info(f"Initializing {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}...")
    # Pre-index and warm up NLP vectorizer
    matcher = get_matcher()
    logger.info(f"NLP Engine initialized with {len(matcher.faqs)} FAQs.")
    yield
    logger.info("Application shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Production-ready FAQ Chatbot powered by NLP preprocessing and TF-IDF Cosine Similarity.",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Attach rate limiter state
app.state.limiter = limiter

# Rate limit exceeded handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(f"Rate limit exceeded from client: {request.client.host if request.client else 'unknown'}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Too many requests. Please slow down and try again shortly."
        }
    )

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self'; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    return response

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(chat.router)
app.include_router(faqs.router)

# Mount Frontend static files if frontend directory exists
frontend_dir = settings.FRONTEND_DIR
if frontend_dir.exists():
    app.mount("/css", StaticFiles(directory=frontend_dir / "css"), name="css")
    app.mount("/js", StaticFiles(directory=frontend_dir / "js"), name="js")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(frontend_dir / "index.html")
