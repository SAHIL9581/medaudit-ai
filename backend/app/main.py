import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import CORS_ORIGINS, CORS_ORIGIN_REGEX, LOG_LEVEL, DEBUG_MODE
from app.routes.audit import router as audit_router
from app.routes.chat import router as chat_router
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


# Serve static data files for deployment (only if directories exist)
if os.path.isdir("app/data"):
    app.mount("/data", StaticFiles(directory="app/data"), name="data")
if os.path.isdir("app/vectorstore"):
    app.mount("/vectorstore", StaticFiles(directory="app/vectorstore"), name="vectorstore")
if os.path.isdir("sample_bills"):
    app.mount("/samples", StaticFiles(directory="sample_bills"), name="samples")


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(audit_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    return {
        "name": "MedAudit AI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "data_endpoint": "/data/cpt_benchmarks.json",
        "vectorstore": "/vectorstore/vector_store.json",
        "samples": "/samples/",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Render deployment"""
    return {"status": "healthy", "service": "MedAudit AI"}
