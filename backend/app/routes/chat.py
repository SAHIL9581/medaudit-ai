import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.sarvam_chatbot import answer_question
from app.services.translate import translate_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="Patient's question")
    dashboard_data: dict = Field(default_factory=dict, description="Audit result payload")
    language: str = Field(default="en", description="ISO 639-1 target language code")


class ChatResponse(BaseModel):
    answer: str


@router.post("/ask", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Answer a patient question about their audit results.

    The *dashboard_data* field should be the full JSON object returned by
    POST /api/audit/analyze.  The response is translated to *language* when
    a non-English target is provided.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    try:
        # AI responds directly in the requested language via system prompt
        answer = answer_question(request.question, request.dashboard_data, request.language)
    except Exception as e:
        logger.error("Chatbot service error: %s", e)
        raise HTTPException(status_code=503, detail="AI assistant is temporarily unavailable.")

    # Optional quality pass: if Sarvam API key is available and language is hi/ta,
    # run the English-generated answer through Sarvam Translate for higher accuracy.
    # (Spanish is handled natively by the AI above.)
    if request.language in ("hi", "ta"):
        try:
            sarvam_result = translate_text(answer, request.language)
            if sarvam_result != answer:  # translation actually happened
                answer = sarvam_result
        except Exception as e:
            logger.warning("Sarvam translate skipped, using AI language output: %s", e)

    return ChatResponse(answer=answer)
