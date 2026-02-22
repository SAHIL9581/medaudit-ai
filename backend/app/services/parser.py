import re
import logging
from typing import Optional, List
from pathlib import Path
from app.models.schemas import ExtractedBill, CPTEntry

logger = logging.getLogger(__name__)

_CPT_MIN = 10000
_CPT_MAX = 99999
_MAX_LINE_ITEM_AMOUNT = 9999.0

_JUNK_KEYWORDS = [
    "billing statement", "patient information", "billing information",
    "itemized", "statement", "invoice", "account", "facility", "hospital",
    "medical center", "clinic", "provider", "address", "phone", "fax",
    "date", "service", "charge", "amount", "total", "insurance", "paid",
    "required", "optional", "eob", "summary", "visit", "admission",
    "balance due", "balance", "complexity", "icd",
]

_PROVIDER_JUNK = [
    "patient information", "billing information", "statement of account",
    "itemized", "patient billing", "balance due", "amount due",
    "patient name", "procedure",
]


# ══════════════════════════════════════════════════════════════════════════
# PDF EXTRACTION — 3 engines with fallback
# ══════════════════════════════════════════════════════════════════════════

def _extract_with_pdfplumber(file_path: str) -> str:
    try:
        import pdfplumber
        parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            if row:
                                parts.append("\t".join(
                                    str(cell).strip() if cell else ""
                                    for cell in row
                                ))
                t = page.extract_text()
                if t:
                    parts.append(t)
        return "\n".join(parts)
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")
        return ""


def _extract_with_pymupdf(file_path: str) -> str:
    try:
        import fitz
        doc   = fitz.open(file_path)
        parts = []
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if b.get("type") == 0:
                    for line in b.get("lines", []):
                        line_text = " ".join(
                            span["text"] for span in line.get("spans", [])
                        )
                        if line_text.strip():
                            parts.append(line_text.strip())
        doc.close()
        return "\n".join(parts)
    except Exception as e:
        logger.warning(f"PyMuPDF failed: {e}")
        return ""


def _extract_with_ocr(file_path: str) -> str:
    try:
        import pytesseract
        from pdf2image import convert_from_path
        pages = convert_from_path(file_path, dpi=300)
        parts = [pytesseract.image_to_string(page) for page in pages]
        logger.info(f"OCR extracted {len(pages)} pages")
        return "\n".join(parts)
    except Exception as e:
        logger.warning(f"OCR failed (install pytesseract + pdf2image): {e}")
        return ""


def extract_text_from_pdf(file_path: str) -> str:
    text = _extract_with_pdfplumber(file_path)
    if len(text.strip()) > 100:
        logger.info("PDF extracted via pdfplumber")
        return text
    text = _extract_with_pymupdf(file_path)
    if len(text.strip()) > 100:
        logger.info("PDF extracted via PyMuPDF")
        return text
    logger.info("Attempting OCR for scanned PDF")
    text = _extract_with_ocr(file_path)
    if len(text.strip()) > 50:
        logger.info("PDF extracted via OCR")
        return text
    raise ValueError(f"Could not extract text from PDF: {file_path}")


# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════

def _parse_amount(raw: str) -> float:
    cleaned = re.sub(r"[^\d.]", "", raw)
    try:
        val = float(cleaned)
        return val if 0.01 <= val <= 9_999_999 else 0.0
    except Exception:
        return 0.0


def _is_valid_cpt(code: str) -> bool:
    try:
        return _CPT_MIN <= int(code) <= _CPT_MAX
    except Exception:
        return False


def _clean_name(raw: Optional[str], max_len: int = 50) -> Optional[str]:
    if not raw:
        return None
    cleaned = raw.strip().strip(",").strip()
    if not cleaned or len(cleaned) < 3 or len(cleaned) > max_len:
        return None
    lower = cleaned.lower()
    if any(kw in lower for kw in _JUNK_KEYWORDS):
        return None
    if cleaned.isupper() and len(cleaned) > 20:
        return None
    if re.search(r"\d", cleaned):
        return None
    words = cleaned.split()
    if len(words) < 2:
        return None
    if not all(w[0].isupper() for w in words if len(w) > 1):
        return None
    return cleaned


def _clean_provider(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    cleaned = raw.strip().strip(",")
    if not cleaned or len(cleaned) < 3 or len(cleaned) > 80:
        return None
    return cleaned


# ══════════════════════════════════════════════════════════════════════════
# CPT EXTRACTION — 5 strategies, most specific wins
# ══════════════════════════════════════════════════════════════════════════

def _strategy_1(text: str) -> dict:
    """Structured line: date + CPT + desc + ICD-10 + units + $amount"""
    pattern = re.compile(
        r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\s+"
        r"(\d{5})\s+"
        r"(.+?)\s+"
        r"([A-Z]\d{2}\.?\d{0,4})\s+"
        r"(\d+)\s+"
        r"\$?([\d,]+\.?\d*)",
        re.IGNORECASE,
    )
    entries = {}
    for m in pattern.finditer(text):
        code   = m.group(2)
        amount = _parse_amount(m.group(6))
        if _is_valid_cpt(code) and amount > 0:
            entries[code] = CPTEntry(
                code=code,
                description=m.group(3).strip(),
                billed_amount=amount,
                service_date=m.group(1),
                units=int(m.group(5)),
            )
    return entries


def _strategy_2(text: str) -> dict:
    """CPT label: 'CPT 99285: desc  ICD-10: J06.9  Units: 1  Charge: $1850'"""
    # Specific Charge: $amount format (bill 6 format)
    pattern_charge = re.compile(
        r"CPT\s+(\d{5})[^\n]*?Charge:\s*\$\s*([\d,]+\.?\d+)",
        re.IGNORECASE,
    )
    # Generic CPT label with any $ amount
    pattern_generic = re.compile(
        r"(?:CPT|Procedure\s*Code?|Svc\s*Code)[:\s#]*(\d{5})"
        r"[^\n\$]{0,80}\$\s*([\d,]+\.?\d+)",
        re.IGNORECASE,
    )
    entries = {}
    for pat in [pattern_charge, pattern_generic]:
        for m in pat.finditer(text):
            code   = m.group(1)
            amount = _parse_amount(m.group(2))
            if _is_valid_cpt(code) and amount > 0 and code not in entries:
                entries[code] = CPTEntry(code=code, billed_amount=amount)
    return entries


def _strategy_3(text: str) -> dict:
    """Tab-separated table rows."""
    p1 = re.compile(r"(\d{5})\t[^\t\n]{0,60}\t\$?([\d,]+\.?\d{2})")
    p2 = re.compile(r"\$?([\d,]+\.?\d{2})\t[^\t\n]{0,60}\t(\d{5})")
    entries = {}
    for m in p1.finditer(text):
        code, amount = m.group(1), _parse_amount(m.group(2))
        if _is_valid_cpt(code) and amount > 0 and code not in entries:
            entries[code] = CPTEntry(code=code, billed_amount=amount)
    for m in p2.finditer(text):
        code, amount = m.group(2), _parse_amount(m.group(1))
        if _is_valid_cpt(code) and amount > 0 and code not in entries:
            entries[code] = CPTEntry(code=code, billed_amount=amount)
    return entries


def _strategy_4(text: str) -> dict:
    """Procedure Code: XXXXX on one line, Amount Charged: $X on next line."""
    lines   = text.split("\n")
    entries = {}
    for i, line in enumerate(lines):
        # Match "Procedure Code: 29881" style
        m = re.search(r"(?:Procedure\s*Code|Proc\.?\s*Code)[:\s#]+(\d{5})", line, re.IGNORECASE)
        if not m:
            # Also try bare 5-digit code on its own line
            m = re.search(r"^\s*(\d{5})\s*$", line)
        if m and _is_valid_cpt(m.group(1)):
            code        = m.group(1)
            # Look for "Amount Charged: $X" in next 2 lines
            search_text = " ".join(lines[i:i+3])
            amounts     = re.findall(
                r"(?:Amount\s*Charged|Charge|Amount)[:\s]*\$\s*([\d,]+\.?\d{2})",
                search_text, re.IGNORECASE
            )
            if not amounts:
                amounts = re.findall(r"\$\s*([\d,]+\.?\d{2})", search_text)
            if amounts:
                amount = _parse_amount(amounts[0])  # first amount = this line's charge
                if amount > 0 and code not in entries:
                    entries[code] = CPTEntry(code=code, billed_amount=amount)
    return entries


def _strategy_5(text: str) -> dict:
    """Broadest fallback: any 5-digit code near any dollar amount on same line."""
    pattern = re.compile(
        r"\b(\d{5})\b[^\n\$]{0,100}\$\s*([\d,]+\.?\d+)",
    )
    entries = {}
    for m in pattern.finditer(text):
        code   = m.group(1)
        amount = _parse_amount(m.group(2))
        if _is_valid_cpt(code) and amount > 0 and code not in entries:
            entries[code] = CPTEntry(code=code, billed_amount=amount)
    return entries


def _extract_cpt_codes(text: str) -> dict:
    """Run all 5 strategies — most specific strategy wins on conflict."""
    s1 = _strategy_1(text)
    s2 = _strategy_2(text)
    s3 = _strategy_3(text)
    s4 = _strategy_4(text)
    s5 = _strategy_5(text)

    merged = {}
    for d in [s5, s4, s3, s2, s1]:
        merged.update(d)

    # ── Block fake CPTs from total/subtotal lines ─────────────────────────
    total_line_pattern = re.compile(
        r"(?:Total|Insurance|Amount Due|Patient Due|Balance|Subtotal|Billed Amount)"
        r"[^\n]*?(\d{5,6})",
        re.IGNORECASE,
    )
    blocked = set(m.group(1) for m in total_line_pattern.finditer(text))

    to_remove = [
        code for code, entry in merged.items()
        if code in blocked or entry.billed_amount > _MAX_LINE_ITEM_AMOUNT
    ]
    for code in to_remove:
        logger.warning(f"Dropping CPT {code} — matched total line or amount too large")
        del merged[code]

    logger.info(
        f"CPT strategies: s1={len(s1)} s2={len(s2)} s3={len(s3)} "
        f"s4={len(s4)} s5={len(s5)} → final={len(merged)}"
    )
    return merged


# ══════════════════════════════════════════════════════════════════════════
# MAIN PARSE FUNCTION
# ══════════════════════════════════════════════════════════════════════════

def parse_bill_text(text: str) -> ExtractedBill:

    # ── CPT codes ─────────────────────────────────────────────────────────
    cpt_entries = _extract_cpt_codes(text)

    # ── Dates ─────────────────────────────────────────────────────────────
    date_pattern = re.compile(
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b"
    )
    dates = list(set(date_pattern.findall(text)))[:10]

    # ── ICD-10 codes ──────────────────────────────────────────────────────
    icd_line_pattern = re.compile(
        r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\s+\d{5}.+?([A-Z]\d{2}\.?\d{0,4})",
        re.IGNORECASE,
    )
    icd_pattern = re.compile(r"\b([A-Z]\d{2}\.?\d{0,4})\b")
    icd_from_lines = [m.group(1) for m in icd_line_pattern.finditer(text)]
    icd_codes = icd_from_lines if icd_from_lines else [
        c for c in list(set(icd_pattern.findall(text)))[:20]
        if len(c) >= 3
    ]

    # ── Totals ────────────────────────────────────────────────────────────
    total_pattern = re.compile(
        r"(?:Total\s*(?:Charges?|Amount|Due|Billed)|"
        r"Total\s*Billed\s*Amount|Amount\s*(?:Billed|Due))"
        r"[:\s]*\$?([\d,]+\.?\d*)",
        re.IGNORECASE,
    )
    total_match  = total_pattern.search(text)
    total_billed = (
        _parse_amount(total_match.group(1))
        if total_match
        else sum(e.billed_amount for e in cpt_entries.values())
    )

    # ── Insurance + patient responsibility ───────────────────────────────
    ins_pattern = re.compile(
        r"(?:Insurance\s*(?:Paid|Payment|Amount)|Plan\s*Paid|Insurance\s*Payment)"
        r"[:\s]*-?\$?([\d,]+\.?\d*)",
        re.IGNORECASE,
    )
    resp_pattern = re.compile(
        r"(?:Patient\s*(?:Responsibility|Owes?|Due|Amount)\b"
        r"|Amount\s*(?:You\s*Owe|Due\s*from\s*Patient)"
        r"|Patient\s*Balance\s*Due)"
        r"[:\s]*\$?([\d,]+\.?\d*)",
        re.IGNORECASE,
    )
    ins_match  = ins_pattern.search(text)
    resp_match = resp_pattern.search(text)
    insurance_paid         = _parse_amount(ins_match.group(1))  if ins_match  else None
    patient_responsibility = _parse_amount(resp_match.group(1)) if resp_match else None

    # ── Provider name ─────────────────────────────────────────────────────
    provider_name = None
    for pat in [
        # Org name containing a medical keyword
        re.compile(
            r"^((?:[A-Z][A-Za-z]+\s+){1,6}"
            r"(?:Hospital|Medical|Clinic|Center|Health|Surgery|Orthopedic|Cardiology|Medicine|System)"
            r"[A-Za-z\s&'.,-]{0,40})\n",
            re.MULTILINE
        ),
        # Explicit label
        re.compile(
            r"(?:Hospital|Medical Center|Clinic|Provider|Facility|From|Billed\s*By)"
            r"[:\s]+([A-Z][A-Za-z\s&'-]{3,60})",
            re.IGNORECASE
        ),
        # First multi-word line (min 10 chars, not a junk header)
        re.compile(r"^([A-Z][A-Za-z\s&'.,-]{10,70})\n", re.MULTILINE),
    ]:
        m = pat.search(text)
        if m:
            candidate = _clean_provider(m.group(1))
            if not candidate:
                continue
            lower = candidate.lower()
            if len(candidate.split()) < 2:
                continue
            if any(kw in lower for kw in _PROVIDER_JUNK):
                continue
            provider_name = candidate
            break

    # ── Patient name ──────────────────────────────────────────────────────
    # Key fix: stop matching at whitespace clusters or billing keywords
    # "Patient Name: James R. Hartwell Account #: ..." → stop before "Account"
    patient_name = None
    for pat in [
        re.compile(
            r"Patient\s*Name[:\s]+"
            r"([A-Z][A-Za-z]+(?:\s+[A-Za-z.][A-Za-z'-]+){1,3})"
            r"(?=\s{2,}|\s*Account|\s*Member|\s*Date|\s*DOB|\n|$)",
            re.IGNORECASE | re.MULTILINE,
        ),
        re.compile(
            r"(?:Patient|Guarantor)[:\s]+"
            r"([A-Z][A-Za-z]+(?:\s+[A-Za-z][A-Za-z'-]+){1,3})"
            r"(?=\s{2,}|\s*Account|\s*$|\n)",
            re.IGNORECASE | re.MULTILINE,
        ),
        re.compile(
            r"(?<!\w)Name[:\s]+"
            r"([A-Z][A-Za-z]+(?:\s+[A-Za-z][A-Za-z'-]+){1,2})"
            r"(?=\s{2,}|\s*Account|\s*$|\n)",
            re.IGNORECASE | re.MULTILINE,
        ),
    ]:
        m = pat.search(text)
        if m:
            candidate = _clean_name(m.group(1))
            if candidate:
                patient_name = candidate
                break

    # ── Inpatient detection ───────────────────────────────────────────────
    is_inpatient = None
    if re.search(r"\binpatient\b|\badmission\b|\bhospitalization\b", text, re.IGNORECASE):
        is_inpatient = True
    if re.search(r"\boutpatient\b|\bambulatory\b|\bobservation\b|\bemergency\b", text, re.IGNORECASE):
        is_inpatient = False if is_inpatient is None else is_inpatient

    logger.info(
        f"Parsed bill — provider: {provider_name}, patient: {patient_name}, "
        f"CPT codes: {len(cpt_entries)}, total: ${total_billed:.2f}, "
        f"inpatient: {is_inpatient}"
    )

    return ExtractedBill(
        provider_name=provider_name,
        patient_name=patient_name,
        service_dates=dates,
        cpt_codes=list(cpt_entries.values()),
        icd_codes=icd_codes,
        total_billed=total_billed,
        is_inpatient=is_inpatient,
        insurance_paid=insurance_paid,
        patient_responsibility=patient_responsibility,
        raw_text_snippet=text[:1500],
    )
