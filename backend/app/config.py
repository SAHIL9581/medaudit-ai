import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


# ── OpenAI ────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str   = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
MAX_TOKENS: int     = int(os.getenv("MAX_TOKENS", "4096"))


# ── Sarvam AI ─────────────────────────────────────────────────────────────
SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")


# ── Server ────────────────────────────────────────────────────────────────
CORS_ORIGINS: list = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,https://medaudit-ai.vercel.app"
).split(",")

CORS_ORIGIN_REGEX: str = os.getenv(
    "CORS_ORIGIN_REGEX",
    r"https://medaudit-.*\.vercel\.app"
)

LOG_LEVEL: str   = os.getenv("LOG_LEVEL", "INFO")
DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"


# ── Storage ───────────────────────────────────────────────────────────────
CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./app/vectorstore")
UPLOAD_DIR: str         = os.getenv("UPLOAD_DIR", "tmp/uploads")


# ── Audit Settings ────────────────────────────────────────────────────────
PRICING_THRESHOLD_PCT: float = float(os.getenv("PRICING_THRESHOLD_PCT", "30"))
MAX_FILE_SIZE_MB: int        = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
MAX_PAGES_PER_PDF: int       = int(os.getenv("MAX_PAGES_PER_PDF", "50"))


# ── Directory Setup ───────────────────────────────────────────────────────
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)


# ── Settings object (for main.py compatibility) ───────────────────────────
class Settings:
    openai_api_key    = OPENAI_API_KEY
    openai_model      = OPENAI_MODEL
    cors_origins      = CORS_ORIGINS
    cors_origin_regex = CORS_ORIGIN_REGEX
    debug_mode        = DEBUG_MODE
    log_level         = LOG_LEVEL


@lru_cache
def get_settings() -> Settings:
    return Settings()
