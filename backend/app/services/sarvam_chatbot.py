import logging
import re
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError
from app.config import SARVAM_API_KEY, OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKENS

logger = logging.getLogger(__name__)

_SARVAM_BASE_URL = "https://api.sarvam.ai/v1"
_SARVAM_MODEL = "sarvam-m"

# Use Sarvam if key is present, otherwise fall back to configured OpenAI client
def _get_client() -> tuple[OpenAI, str]:
    if SARVAM_API_KEY:
        return OpenAI(api_key=SARVAM_API_KEY, base_url=_SARVAM_BASE_URL, timeout=60.0), _SARVAM_MODEL
    logger.warning("SARVAM_API_KEY not set — falling back to OpenAI for chatbot.")
    return OpenAI(api_key=OPENAI_API_KEY, timeout=60.0), OPENAI_MODEL


# Maps ISO 639-1 code → full language instruction injected into the system prompt
_LANGUAGE_INSTRUCTIONS: dict[str, str] = {
    "hi": "IMPORTANT: You MUST respond entirely in Hindi (हिंदी). Use simple, everyday Hindi words that rural and elderly people can easily understand. Do NOT use English words unless they are medical codes or numbers.",
    "ta": "IMPORTANT: You MUST respond entirely in Tamil (தமிழ்). Use simple, everyday Tamil words that rural and elderly people can easily understand. Do NOT use English words unless they are medical codes or numbers.",
    "es": "IMPORTANT: You MUST respond entirely in Spanish (Español). Use simple, everyday Spanish words that rural and elderly people can easily understand. Do NOT use English words unless they are medical codes or numbers.",
}


def _build_system_prompt(language: str) -> str:
    base = """You are a friendly medical bill helper. You explain hospital bills in very simple words that anyone can understand, including elderly people and children.

Rules:
- Use simple, everyday language. No medical or legal jargon.
- If you must use a technical term, explain it in plain words right after.
- Keep your answer short and easy to read.
- Always structure your answer like this:
  1. A one-sentence plain summary of the answer
  2. A numbered list (2-4 points) explaining the key details simply
  3. One clear action the person should take next
- Reference specific codes or amounts from the audit data when helpful.
- Never diagnose or give legal advice.
- Answer only based on the audit data provided."""
    lang_instruction = _LANGUAGE_INSTRUCTIONS.get(language, "")
    if lang_instruction:
        return f"{base}\n\n{lang_instruction}"
    return base


def _build_context(dashboard_data: dict) -> str:
    """Serialize the relevant parts of the audit result as readable context."""
    parts: list[str] = []

    total_billed = dashboard_data.get("total_billed", 0)
    savings = dashboard_data.get("estimated_savings", 0)
    issue_count = dashboard_data.get("issue_count", 0)
    parts.append(
        f"AUDIT SUMMARY: Total Billed=${total_billed:.2f}, "
        f"Estimated Overcharge=${savings:.2f}, Issues Found={issue_count}"
    )

    issues = dashboard_data.get("issues", [])
    if issues:
        issue_lines = [
            f"  - [{i.get('issue_type', 'UNKNOWN')}] CPT {i.get('cpt_code', 'N/A')}: "
            f"{i.get('description', '')} "
            f"(Confidence: {i.get('confidence', 0):.0%}, Risk: {i.get('risk_level', 'N/A')}, "
            f"Suggested action: {i.get('suggested_action', '')})"
            for i in issues
        ]
        parts.append("BILLING ISSUES DETECTED:\n" + "\n".join(issue_lines))

    pricing = dashboard_data.get("pricing_results", [])
    flagged = [p for p in pricing if p.get("is_flagged")]
    if flagged:
        pricing_lines = [
            f"  - CPT {p.get('cpt_code', 'N/A')}: Billed=${p.get('billed_amount', 0):.2f}, "
            f"Benchmark=${p.get('benchmark_median', 0):.2f}, "
            f"Deviation={p.get('deviation_percent', 0):+.1f}%"
            for p in flagged
        ]
        parts.append("FLAGGED PRICING ANOMALIES:\n" + "\n".join(pricing_lines))

    bill = dashboard_data.get("extracted_bill", {})
    if bill:
        parts.append(
            f"PATIENT INFO: Patient={bill.get('patient_name', 'Unknown')}, "
            f"Provider={bill.get('provider_name', 'Unknown')}, "
            f"Setting={'Inpatient' if bill.get('is_inpatient') else 'Outpatient'}"
        )

    appeal = dashboard_data.get("appeal_letter", {})
    if appeal and appeal.get("summary"):
        parts.append(f"APPEAL SUMMARY: {appeal.get('summary', '')[:400]}")

    return "\n\n".join(parts)


def _strip_thinking_tokens(text: str) -> str:
    """Remove <think>...</think> reasoning tokens produced by some models."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((APITimeoutError, APIConnectionError, RateLimitError)),
)
def _call_chat_api(client: OpenAI, model: str, messages: list[dict]) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=MAX_TOKENS,
        temperature=0.4,
    )
    return response.choices[0].message.content or ""


def answer_question(question: str, dashboard_data: dict, language: str = "en") -> str:
    """
    Answer a patient question about their audit results using Sarvam AI (or OpenAI fallback).
    The AI responds directly in *language* via system prompt instruction.

    Args:
        question:        The patient's question.
        dashboard_data:  The full audit result dict from /api/audit/analyze.
        language:        ISO 639-1 code, e.g. "en", "hi", "ta", "es".

    Returns:
        A plain-text answer string in the requested language.
    """
    client, model = _get_client()
    context = _build_context(dashboard_data)
    system_prompt = _build_system_prompt(language)

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"Here is the audit report context:\n\n{context}\n\n"
                f"Patient question: {question}"
            ),
        },
    ]

    logger.info("Chatbot request via model=%s question=%r", model, question[:80])
    try:
        raw = _call_chat_api(client, model, messages)
        answer = _strip_thinking_tokens(raw)
        logger.info("Chatbot answered successfully.")
        return answer
    except Exception as e:
        logger.error("Chatbot call failed: %s", e)
        raise
