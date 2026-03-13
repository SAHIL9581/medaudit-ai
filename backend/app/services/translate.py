import logging
import httpx
from app.config import SARVAM_API_KEY

logger = logging.getLogger(__name__)

_TRANSLATE_URL = "https://api.sarvam.ai/translate"

# Sarvam-supported language codes (BCP-47 + region)
SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "en-IN",
    "hi": "hi-IN",
    "ta": "ta-IN",
    "es": "es",        # Sarvam may not support Spanish; handled gracefully below
}

_UNSUPPORTED_FALLBACK = {"es"}  # languages Sarvam does not cover; return original text


def translate_text(text: str, target_language: str) -> str:
    """
    Translate *text* to *target_language* using the Sarvam Translate API.

    Args:
        text:            The source text (assumed English).
        target_language: ISO 639-1 code, e.g. "hi", "ta", "es".

    Returns:
        Translated text string.  Returns *text* unchanged if:
        - target_language is "en" (no-op)
        - SARVAM_API_KEY is not configured
        - The language is unsupported by Sarvam
        - The API call fails
    """
    if target_language == "en":
        return text

    if not SARVAM_API_KEY:
        logger.warning("SARVAM_API_KEY not set — translation unavailable, returning original text.")
        return text

    target_code = SUPPORTED_LANGUAGES.get(target_language)
    if not target_code or target_language in _UNSUPPORTED_FALLBACK:
        logger.warning(
            "Language '%s' is not supported by Sarvam Translate. Returning original text.",
            target_language,
        )
        return text

    payload = {
        "input": text,
        "source_language_code": "en-IN",
        "target_language_code": target_code,
        "speaker_gender": "Male",
        "mode": "formal",
        "model": "mayura:v1",
        "enable_preprocessing": False,
    }
    headers = {
        "Content-Type": "application/json",
        "API-Subscription-Key": SARVAM_API_KEY,
    }

    try:
        response = httpx.post(_TRANSLATE_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        translated = data.get("translated_text") or data.get("output") or text
        logger.info("Translated %d chars to '%s'.", len(text), target_language)
        return translated
    except httpx.HTTPStatusError as e:
        logger.error("Sarvam Translate HTTP error: %s — %s", e, e.response.text[:200])
        return text
    except Exception as e:
        logger.error("Sarvam Translate failed: %s", e)
        return text
