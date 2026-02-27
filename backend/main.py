"""
EdAccelerator API

Main application entry point.
Configures FastAPI app, middleware, and mounts routers.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load local .env file if it exists
load_dotenv()

from api.routes import system_router, session_router, chat_router
from shared.passage import PASSAGE
from evaluator.question_generator import initialize_questions

# ============================================================
# Configuration
# ============================================================

ENV = os.getenv("ENV", "development")
# Default to localhost for dev, but we will process this further below
FRONTEND_URL_RAW = os.getenv("FRONTEND_URL", "http://localhost:3000")
VERSION = "1.0.0"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s │ %(levelname)s │ %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("main")

# ============================================================
# Application
# ============================================================

app = FastAPI(
    title="EdAccelerator API",
    description="AI-powered English comprehension learning assistant",
    version=VERSION,
    # Only show docs in development mode for security
    docs_url="/docs" if ENV == "development" else None,
    redoc_url="/redoc" if ENV == "development" else None,
)

# ============================================================
# Middleware (CORS)
# ============================================================

# Start with local defaults
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Process the FRONTEND_URL variable
if FRONTEND_URL_RAW:
    # Split by comma to support multiple Vercel URLs if needed
    urls = [url.strip() for url in FRONTEND_URL_RAW.split(",")]
    for url in urls:
        # Add the URL as is
        if url not in allowed_origins:
            allowed_origins.append(url)
        
        # Security/Browser Tip: Ensure versions with/without trailing slashes are trusted
        if url.endswith("/"):
            clean_url = url.rstrip("/")
            if clean_url not in allowed_origins:
                allowed_origins.append(clean_url)
        else:
            slashed_url = f"{url}/"
            if slashed_url not in allowed_origins:
                allowed_origins.append(slashed_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Routers
# ============================================================

app.include_router(system_router)
app.include_router(session_router)
app.include_router(chat_router)

# Add a basic health check for Railway deployment verification
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": VERSION, "environment": ENV}

# ============================================================
# Startup
# ============================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info(f"🚀 EdAccelerator API v{VERSION}")
    logger.info(f"   Environment: {ENV}")
    logger.info(f"   Allowed Origins: {allowed_origins}")
    logger.info("=" * 50)

    # Validate required environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.error("OPENAI_API_KEY environment variable is not set!")
        raise RuntimeError("OPENAI_API_KEY is required but not configured")
    if openai_key.startswith("sk-") is False and openai_key != "test":
        logger.warning("OPENAI_API_KEY may be invalid (expected sk-... format)")
    logger.info("✅ OPENAI_API_KEY configured")

    # Generate question pools at startup
    # In development, always regenerate. In production, use cache if available.
    force_regen = (ENV == "development")
    logger.info(f"📝 Initializing question pools (regenerate={force_regen})...")
    initialize_questions(PASSAGE["title"], PASSAGE["content"], force_regenerate=force_regen)
    logger.info("✅ Question pools ready")

# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    # Railway automatically provides the PORT environment variable
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Required for Railway/Docker to bind correctly
        port=port,
        reload=(ENV == "development")
    )