import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import CORS_ORIGINS, LOG_LEVEL, DEBUG_MODE
from app.routes.audit import router as audit_router
from app.services.rag import initialize_rag

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MedAudit AI Platform...")
    initialize_rag()
    logger.info("RAG knowledge base ready.")
    yield
    logger.info("MedAudit AI Platform shutting down.")


app = FastAPI(
    title="MedAudit AI",
    description="AI-Powered Medical Bill Audit & Dispute Platform",
    version="1.0.0",
    debug=DEBUG_MODE,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_router)


@app.get("/")
async def root():
    return {
        "name": "MedAudit AI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }
