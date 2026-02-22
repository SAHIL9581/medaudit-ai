import json
import logging
from datetime import date
from typing import List
from io import BytesIO
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAI, APITimeoutError, APIConnectionError, RateLimitError
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from app.config import OPENAI_API_KEY, OPENAI_MODEL, MAX_TOKENS
from app.models.schemas import ExtractedBill, BillingIssue, PricingResult, AppealLetter

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY, timeout=60.0)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((APITimeoutError, APIConnectionError, RateLimitError)),
)
def _generate_letter_text(
    bill: ExtractedBill,
    issues: List[BillingIssue],
    pricing_results: List[PricingResult],
    total_overcharge: float,
) -> str:
    issues_summary = "\n".join(
        f"- [{i.issue_type}] CPT {i.cpt_code or 'N/A'}: {i.description} (Confidence: {i.confidence:.0%})"
        for i in issues
    )
    pricing_summary = "\n".join(
        f"- CPT {p.cpt_code}: Billed ${p.billed_amount:.2f}, Benchmark ${p.benchmark_median:.2f}, "
        f"Deviation {p.deviation_percent:+.1f}%"
        for p in pricing_results if p.is_flagged
    )

    prompt = f"""Generate a formal, professional medical billing dispute letter based on these findings.

PATIENT: {bill.patient_name or 'Patient'}
PROVIDER: {bill.provider_name or 'Provider'}
DATE: {date.today().strftime('%B %d, %Y')}
TOTAL ESTIMATED OVERCHARGE: ${total_overcharge:.2f}

DETECTED ISSUES:
{issues_summary or 'General billing anomalies detected'}

FLAGGED PRICING:
{pricing_summary or 'Pricing above benchmark detected'}

Requirements:
- Professional legal tone
- Reference specific CPT codes
- Cite CMS/AMA guidelines
- Request itemized bill review
- Demand correction/refund
- Include appeal rights statement
- 400-600 words
- Plain text, no markdown"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a patient advocate attorney specializing in medical billing disputes. Write formal, legally precise dispute letters.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1200,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def generate_appeal_letter(
    bill: ExtractedBill,
    issues: List[BillingIssue],
    pricing_results: List[PricingResult],
    total_overcharge: float,
) -> AppealLetter:
    try:
        letter_text = _generate_letter_text(bill, issues, pricing_results, total_overcharge)
    except Exception as e:
        logger.error(f"Appeal letter generation failed: {e}")
        letter_text = _fallback_letter(bill, issues, total_overcharge)

    issues_summary = [
        f"{i.issue_type}: {i.description}" for i in issues
    ]
    cpt_references = list(set(
        i.cpt_code for i in issues if i.cpt_code
    ))

    return AppealLetter(
        patient_name=bill.patient_name,
        provider_name=bill.provider_name,
        letter_text=letter_text,
        issues_summary=issues_summary,
        total_estimated_overcharge=round(total_overcharge, 2),
        cpt_references=cpt_references,
    )


def _fallback_letter(bill: ExtractedBill, issues: List[BillingIssue], total_overcharge: float) -> str:
    today = date.today().strftime("%B %d, %Y")
    issue_list = "\n".join(f"  - {i.issue_type}: {i.description}" for i in issues)
    return f"""
{today}

Billing Department
{bill.provider_name or 'Healthcare Provider'}

RE: Formal Billing Dispute — {bill.patient_name or 'Patient'}

To Whom It May Concern,

I am writing to formally dispute charges on my recent medical bill. 
After a thorough review, the following issues were identified totaling approximately ${total_overcharge:.2f} in potential overcharges:

{issue_list}

I respectfully request:
1. A complete itemized bill
2. Medical record documentation supporting each billed service
3. Review and correction of the identified billing errors
4. Written response within 30 days

I reserve the right to escalate this dispute to the state insurance commissioner 
and report to the CMS Office of Inspector General if unresolved.

Sincerely,
{bill.patient_name or 'Patient'}
""".strip()


def generate_pdf_letter(appeal: AppealLetter) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=1 * inch,
        leftMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#1e3a5f"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748b"),
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        spaceAfter=12,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#374151"),
        leading=14,
        spaceAfter=4,
    )

    story = []
    story.append(Paragraph("Medical Billing Dispute Letter", title_style))
    story.append(Paragraph("Generated by MedAudit AI Platform", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1e3a5f")))
    story.append(Spacer(1, 0.2 * inch))

    # Metadata block
    story.append(Paragraph(f"<b>Patient:</b> {appeal.patient_name or 'N/A'}", label_style))
    story.append(Paragraph(f"<b>Provider:</b> {appeal.provider_name or 'N/A'}", label_style))
    story.append(Paragraph(f"<b>Estimated Overcharge:</b> ${appeal.total_estimated_overcharge:.2f}", label_style))
    story.append(Paragraph(f"<b>CPT Codes Referenced:</b> {', '.join(appeal.cpt_references) or 'N/A'}", label_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
    story.append(Spacer(1, 0.2 * inch))

    # Letter body
    for paragraph in appeal.letter_text.split("\n"):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), body_style))

    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        "<i>This letter was generated by MedAudit AI. Please review before sending.</i>",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=9, textColor=colors.gray, alignment=TA_CENTER),
    ))

    doc.build(story)
    return buffer.getvalue()
