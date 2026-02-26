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

load_dotenv()

from api.routes import system_router, session_router, chat_router

# ============================================================
# Configuration
# ============================================================

ENV = os.getenv("ENV", "development")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
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
    docs_url="/docs" if ENV == "development" else None,
    redoc_url="/redoc" if ENV == "development" else None,
)

# ============================================================
# Middleware
# ============================================================

# CORS
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
if FRONTEND_URL and FRONTEND_URL not in allowed_origins:
    allowed_origins.append(FRONTEND_URL)

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

# ============================================================
# Startup
# ============================================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info(f"🚀 EdAccelerator API v{VERSION}")
    logger.info(f"   Environment: {ENV}")
    logger.info(f"   Frontend URL: {FRONTEND_URL}")
    logger.info("=" * 50)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=ENV == "development"
    )
