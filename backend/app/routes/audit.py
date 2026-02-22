import os
import uuid
import logging
import asyncio
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import Response
import aiofiles
from app.config import UPLOAD_DIR, DEBUG_MODE
from app.models.schemas import AuditResult
from app.services.parser import extract_text_from_pdf, parse_bill_text
from app.services.validator import validate_and_detect_issues
from app.services.pricing import compare_pricing
from app.services.confidence import (
    calculate_risk_score,
    calculate_overall_confidence,
    calculate_appeal_success_probability,
)
from app.services.appeal_generator import generate_appeal_letter, generate_pdf_letter
from app.services.rag import query_knowledge_base


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/audit", tags=["audit"])


async def _save_upload(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename or "bill.pdf")[1] or ".pdf"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        await f.write(content)
    return filepath


@router.post("/analyze", response_model=AuditResult)
async def analyze_bill(
    bill_pdf: UploadFile = File(..., description="Hospital bill PDF"),
    summary_pdf: Optional[UploadFile] = File(None, description="After Visit Summary PDF"),
    eob_pdf: Optional[UploadFile] = File(None, description="Insurance EOB PDF"),
):
    if not bill_pdf.filename or not bill_pdf.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # ── Stage 1: Save uploads ───────────────────────────────────────────────
    try:
        bill_path    = await _save_upload(bill_pdf)
        summary_path = await _save_upload(summary_pdf) if summary_pdf else None
        eob_path     = await _save_upload(eob_pdf)     if eob_pdf     else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")

    # ── Stage 2: Extract text ───────────────────────────────────────────────
    try:
        bill_text = await asyncio.to_thread(extract_text_from_pdf, bill_path)
        if summary_path:
            summary_text = await asyncio.to_thread(extract_text_from_pdf, summary_path)
            bill_text += "\n\n--- AFTER VISIT SUMMARY ---\n" + summary_text
        if eob_path:
            eob_text = await asyncio.to_thread(extract_text_from_pdf, eob_path)
            bill_text += "\n\n--- INSURANCE EOB ---\n" + eob_text
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF parsing failed: {e}")

    # ── Stage 3: Parse structured data ─────────────────────────────────────
    try:
        extracted_bill = await asyncio.to_thread(parse_bill_text, bill_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bill parsing failed: {e}")

    if DEBUG_MODE:
        logger.debug(f"Extracted bill: {extracted_bill.model_dump()}")

    # ── Stage 4: Validate & detect issues ──────────────────────────────────
    try:
        audit_report  = await asyncio.to_thread(
            validate_and_detect_issues, extracted_bill, bill_text
        )
        issues       = audit_report.issues
        refined_bill = audit_report.extracted_bill
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        issues, refined_bill = [], extracted_bill

    # ── Stage 5: Pricing comparison ─────────────────────────────────────────
    try:
        pricing_results = await asyncio.to_thread(
            compare_pricing, refined_bill.cpt_codes
        )
    except Exception as e:
        logger.error(f"Pricing comparison failed: {e}")
        pricing_results = []

    # ── Stage 6: Confidence & risk scoring ──────────────────────────────────
    risk_score         = calculate_risk_score(issues, pricing_results)
    overall_confidence = calculate_overall_confidence(issues, pricing_results)
    appeal_success_prob = calculate_appeal_success_probability(
        issues, pricing_results, risk_score
    )

    # ── Stage 7: Financial summary ───────────────────────────────────────────
    total_billed = refined_bill.total_billed or sum(
        e.billed_amount for e in refined_bill.cpt_codes
    )
    total_overcharge    = sum(p.estimated_overcharge for p in pricing_results)
    estimated_fair_total = max(0.0, total_billed - total_overcharge)

    # ── Stage 8: RAG context for transparency ────────────────────────────────
    rag_context = query_knowledge_base(
        f"billing appeal {' '.join(i.issue_type for i in issues[:3])}", n_results=2
    )

    # ── Stage 9: Generate appeal letter ──────────────────────────────────────
    try:
        appeal_letter = await asyncio.to_thread(
            generate_appeal_letter,
            refined_bill, issues, pricing_results, total_overcharge,
        )
    except Exception as e:
        logger.error(f"Appeal letter generation failed: {e}")
        from app.models.schemas import AppealLetter
        appeal_letter = AppealLetter(
            patient_name=refined_bill.patient_name,
            provider_name=refined_bill.provider_name,
            letter_text="Appeal letter generation failed. Please try again.",
            issues_summary=[],
            total_estimated_overcharge=total_overcharge,
            cpt_references=[],
        )

    # ── Cleanup temp files ────────────────────────────────────────────────────
    for path in [bill_path, summary_path, eob_path]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    return AuditResult(
        extracted_bill=refined_bill,
        issues=issues,
        pricing_results=pricing_results,
        appeal_letter=appeal_letter,
        total_billed=round(total_billed, 2),
        estimated_fair_total=round(estimated_fair_total, 2),
        estimated_savings=round(total_overcharge, 2),
        overall_confidence=overall_confidence,
        risk_score=risk_score,
        appeal_success_probability=appeal_success_prob,
        issue_count=len(issues),
        rag_context_used=rag_context,
    )


@router.post("/download-letter")
async def download_appeal_letter(appeal_data: dict):
    """Generate and return a downloadable PDF appeal letter."""
    try:
        from app.models.schemas import AppealLetter
        appeal    = AppealLetter(**appeal_data)
        pdf_bytes = await asyncio.to_thread(generate_pdf_letter, appeal)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="appeal_letter.pdf"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@router.get("/health")
async def health_check():
    return {"status": "healthy", "model": "gpt-4.1-mini", "rag": "active"}
