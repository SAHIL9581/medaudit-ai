import json
import logging
import re
from pathlib import Path
from typing import List, Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import OPENAI_API_KEY, OPENAI_MODEL, PRICING_THRESHOLD_PCT
from app.models.schemas import (
    ExtractedBill, AuditIssue, PricingResult, AuditReport, AppealLetter
)
from app.services.rag import query_knowledge_base

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

DATA_DIR = Path(__file__).parent.parent / "data"

def _load_benchmarks() -> dict:
    p = DATA_DIR / "cpt_benchmarks.json"
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {}

def _load_ncci() -> dict:
    p = DATA_DIR / "ncci_edits.json"
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {}

def _load_lcd() -> dict:
    p = DATA_DIR / "lcd_mappings.json"
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {}

def check_ncci_violations(bill: ExtractedBill) -> List[AuditIssue]:
    """Pure rule-based NCCI unbundling detection — no GPT needed."""
    ncci = _load_ncci()
    issues = []
    code_set = {item.cpt_code for item in bill.line_items}
    checked = set()

    for item in bill.line_items:
        code = item.cpt_code
        if code in ncci and code not in checked:
            conflicts = code_set & set(ncci[code])
            for conflict in conflicts:
                pair = tuple(sorted([code, conflict]))
                if pair not in checked:
                    checked.add(pair)
                    issues.append(AuditIssue(
                        issue_type="Unbundling (NCCI Violation)",
                        cpt_code=f"{code} + {conflict}",
                        description=f"CPT {code} and {conflict} cannot be billed together per CMS NCCI edit rules. One code is already included in the other.",
                        rule_triggered=f"CMS NCCI Correct Coding Initiative — edit pair {code}/{conflict}",
                        risk_level="high",
                        confidence=0.97,
                        estimated_overcharge=item.billed_amount * 0.85,
                        suggested_action=f"Request removal of CPT {conflict} from bill. CPT {code} already includes this service.",
                        cpt_reference=f"CMS NCCI Policy Manual: CPT {code} and {conflict} are mutually exclusive — the comprehensive code covers all components."
                    ))
    return issues

def check_lcd_violations(bill: ExtractedBill) -> List[AuditIssue]:
    """Check if procedure ICD-10 diagnosis supports medical necessity."""
    lcd = _load_lcd()
    issues = []
    for item in bill.line_items:
        code = item.cpt_code
        icd = item.icd10_code or ""
        if code in lcd and icd:
            rule = lcd[code]
            allowed = rule["allowed_icd_prefixes"]
            if not any(icd.startswith(prefix) for prefix in allowed):
                issues.append(AuditIssue(
                    issue_type="Medical Necessity Concern",
                    cpt_code=code,
                    description=f"CPT {code} ({rule['description']}) may not be medically necessary for diagnosis {icd}. The listed diagnosis may not support this procedure per CMS coverage guidelines.",
                    rule_triggered=f"CMS Local Coverage Determination (LCD) — {rule['description']}",
                    risk_level=rule["denial_risk"],
                    confidence=0.82,
                    estimated_overcharge=0.0,
                    suggested_action="Request documentation showing medical necessity. Ask provider to cite the specific clinical indication that justifies this procedure for your diagnosis.",
                    cpt_reference=f"CMS LCD requires one of these diagnosis categories for {code}: {', '.join(allowed[:5])}"
                ))
    return issues

def check_duplicate_charges(bill: ExtractedBill) -> List[AuditIssue]:
    """Detect duplicate CPT codes on same date of service."""
    issues = []
    seen = {}
    for item in bill.line_items:
        key = (item.cpt_code, item.date_of_service or "")
        if key in seen:
            issues.append(AuditIssue(
                issue_type="Duplicate Billing",
                cpt_code=item.cpt_code,
                description=f"CPT {item.cpt_code} appears more than once on {item.date_of_service or 'same date'}. Each service should only be billed once per day unless a valid modifier (-50, -76, -77) is present.",
                rule_triggered="CMS Duplicate Claim Policy — same service same date same provider",
                risk_level="high",
                confidence=0.95,
                estimated_overcharge=item.billed_amount,
                suggested_action=f"Request immediate removal of duplicate CPT {item.cpt_code} charge of ${item.billed_amount:.2f}. If bilateral or repeat procedure, verify modifier is present.",
                cpt_reference="CMS Claims Processing Manual Ch.1 §70.7: Duplicate claims are a top billing error — same HCPCS/CPT, same DOS, same beneficiary."
            ))
        else:
            seen[key] = item
    return issues

def analyze_pricing(bill: ExtractedBill) -> List[PricingResult]:
    benchmarks = _load_benchmarks()
    results = []
    threshold = PRICING_THRESHOLD_PCT / 100.0

    for item in bill.line_items:
        code = item.cpt_code
        billed = item.billed_amount

        if code in benchmarks:
            bench = benchmarks[code]
            median = bench["median"]
            deviation = ((billed - median) / median) if median > 0 else 0.0
            overcharge = max(0.0, billed - bench["range_high"])
            flagged = deviation > threshold

            results.append(PricingResult(
                cpt_code=code,
                description=bench["description"],
                billed_amount=billed,
                benchmark_median=median,
                benchmark_low=bench["range_low"],
                benchmark_high=bench["range_high"],
                deviation_percent=round(deviation * 100, 1),
                is_flagged=flagged,
                estimated_overcharge=round(overcharge, 2),
                category=bench.get("category", "Unknown")
            ))
        else:
            results.append(PricingResult(
                cpt_code=code,
                description=item.description or "Unknown procedure",
                billed_amount=billed,
                benchmark_median=0.0,
                benchmark_low=0.0,
                benchmark_high=0.0,
                deviation_percent=0.0,
                is_flagged=False,
                estimated_overcharge=0.0,
                category="Unknown"
            ))
    return results

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def run_gpt_audit(bill: ExtractedBill, rag_context: List[str],
                  ncci_issues: List[AuditIssue],
                  duplicate_issues: List[AuditIssue],
                  lcd_issues: List[AuditIssue]) -> dict:

    pre_detected = []
    for issue in ncci_issues + duplicate_issues + lcd_issues:
        pre_detected.append(f"- [{issue.issue_type}] CPT {issue.cpt_code}: {issue.description}")

    pre_detected_text = "\n".join(pre_detected) if pre_detected else "None detected by rule engine."

    line_items_text = "\n".join([
        f"  CPT {item.cpt_code}: {item.description or 'N/A'} | ICD-10: {item.icd10_code or 'N/A'} | "
        f"${item.billed_amount:.2f} | Date: {item.date_of_service or 'N/A'} | Units: {item.units}"
        for item in bill.line_items
    ])

    prompt = f"""You are a senior medical billing fraud analyst and certified professional coder (CPC).
Analyze this medical bill for billing errors, fraud indicators, and overcharges.

RULE ENGINE PRE-DETECTED ISSUES (already confirmed — do NOT re-add these):
{pre_detected_text}

KNOWLEDGE BASE CONTEXT:
{chr(10).join(rag_context)}

BILL DETAILS:
- Patient: {bill.patient_name or 'Unknown'}
- Provider: {bill.provider_name or 'Unknown'}
- Setting: {'INPATIENT' if bill.is_inpatient else 'OUTPATIENT'}
- Date of Service: {bill.date_of_service or 'Unknown'}
- Total Billed: ${bill.total_amount:.2f}
- Insurance: {bill.insurance_name or 'Unknown'}

LINE ITEMS:
{line_items_text}

ANALYZE FOR THESE ADDITIONAL ISSUES (beyond what rule engine found):
1. UPCODING — Is the CPT level justified by the clinical scenario? Check E&M levels vs complexity.
2. INPATIENT_MISMATCH — Are inpatient codes (99221-99233) used for likely outpatient/observation care?
3. MEDICAL_NECESSITY — Do procedures match the diagnoses? Any unnecessary services?
4. MODIFIER_ABUSE — Are modifiers likely being misused?
5. PRICING_ANOMALY — Any charges that seem extremely high vs typical rates?
6. CODING_ERROR — Wrong code for the described service?

For each issue found, respond with this EXACT JSON format:
{{
  "additional_issues": [
    {{
      "issue_type": "string (e.g. Upcoding, Inpatient Mismatch, Medical Necessity)",
      "cpt_code": "string",
      "description": "clear explanation of the problem in plain English",
      "rule_triggered": "specific CMS/AMA rule or guideline violated",
      "risk_level": "high|medium|low",
      "confidence": 0.0-1.0,
      "estimated_overcharge": 0.0,
      "suggested_action": "specific actionable step for patient",
      "cpt_reference": "relevant billing rule or code definition"
    }}
  ],
  "overall_risk_score": 0.0-1.0,
  "overall_confidence": 0.0-1.0,
  "appeal_success_probability": 0.0-1.0,
  "summary": "2-3 sentence plain English summary of findings"
}}

Return ONLY valid JSON. No extra text."""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=3000,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def validate_and_detect_issues(bill: ExtractedBill, bill_text: str = "") -> AuditReport:
    logger.info(f"Starting full audit: {len(bill.line_items)} line items")

    # Layer 1 — Rule-based checks (deterministic, no GPT)
    ncci_issues      = check_ncci_violations(bill)
    duplicate_issues = check_duplicate_charges(bill)
    lcd_issues       = check_lcd_violations(bill)
    logger.info(f"Rule engine: {len(ncci_issues)} NCCI, {len(duplicate_issues)} duplicate, {len(lcd_issues)} LCD issues")

    # Layer 2 — Pricing analysis
    pricing_results = analyze_pricing(bill)
    flagged_pricing = [p for p in pricing_results if p.is_flagged]
    logger.info(f"Pricing: {len(flagged_pricing)}/{len(pricing_results)} codes flagged")

    # Layer 3 — RAG context retrieval
    query = f"{bill.provider_name or ''} {' '.join(i.cpt_code for i in bill.line_items[:8])} billing audit"
    rag_context = query_knowledge_base(query, n_results=4)

    # Layer 4 — GPT semantic analysis
    try:
        gpt_result = run_gpt_audit(bill, rag_context, ncci_issues, duplicate_issues, lcd_issues)
        gpt_issues_raw = gpt_result.get("additional_issues", [])
    except Exception as e:
        logger.error(f"GPT audit failed: {e}")
        gpt_issues_raw = []
        gpt_result = {"overall_risk_score": 0.5, "overall_confidence": 0.5,
                      "appeal_success_probability": 0.5, "summary": "Automated analysis completed."}

    # Parse GPT issues
    gpt_issues = []
    for raw in gpt_issues_raw:
        try:
            gpt_issues.append(AuditIssue(
                issue_type=raw.get("issue_type", "Unknown"),
                cpt_code=raw.get("cpt_code", ""),
                description=raw.get("description", ""),
                rule_triggered=raw.get("rule_triggered", ""),
                risk_level=raw.get("risk_level", "medium"),
                confidence=float(raw.get("confidence", 0.7)),
                estimated_overcharge=float(raw.get("estimated_overcharge", 0.0)),
                suggested_action=raw.get("suggested_action", ""),
                cpt_reference=raw.get("cpt_reference", "")
            ))
        except Exception as e:
            logger.warning(f"Could not parse GPT issue: {e}")

    # Combine all issues — rule engine first (highest confidence)
    all_issues = ncci_issues + duplicate_issues + lcd_issues + gpt_issues

    # Calculate totals
    total_billed     = sum(i.billed_amount for i in bill.line_items)
    total_overcharge = sum(p.estimated_overcharge for p in pricing_results)
    issue_overcharge = sum(i.estimated_overcharge for i in all_issues)
    estimated_savings = max(total_overcharge, issue_overcharge)
    estimated_fair   = max(0.0, total_billed - estimated_savings)

    # Generate appeal letter
    appeal_letter = generate_appeal_letter(bill, all_issues, pricing_results)

    return AuditReport(
        extracted_bill=bill,
        issues=all_issues,
        pricing_results=pricing_results,
        appeal_letter=appeal_letter,
        total_billed=total_billed,
        estimated_fair_total=estimated_fair,
        estimated_savings=estimated_savings,
        issue_count=len(all_issues),
        risk_score=float(gpt_result.get("overall_risk_score", 0.5)),
        overall_confidence=float(gpt_result.get("overall_confidence", 0.5)),
        appeal_success_probability=float(gpt_result.get("appeal_success_probability", 0.5)),
        audit_summary=gpt_result.get("summary", "Audit completed.")
    )

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
def generate_appeal_letter(bill: ExtractedBill, issues: List[AuditIssue],
                           pricing_results: List[PricingResult]) -> AppealLetter:
    if not issues and not any(p.is_flagged for p in pricing_results):
        return AppealLetter(
            letter_text="No significant billing issues were detected. No appeal letter is necessary at this time.",
            issues_summary=[],
            total_estimated_overcharge=0.0,
            cpt_references=[],
        )

    total_overcharge = sum(i.estimated_overcharge for i in issues)
    high_issues = [i for i in issues if i.risk_level == "high"]
    flagged_pricing = [p for p in pricing_results if p.is_flagged]

    issues_summary_text = "\n".join([
        f"- {i.issue_type} (CPT {i.cpt_code}): {i.description} | Overcharge: ${i.estimated_overcharge:.2f}"
        for i in issues[:8]
    ])
    pricing_summary_text = "\n".join([
        f"- CPT {p.cpt_code} ({p.description}): Billed ${p.billed_amount:.2f} vs benchmark ${p.benchmark_median:.2f} ({p.deviation_percent:+.1f}%)"
        for p in flagged_pricing[:5]
    ])

    prompt = f"""Write a formal, professional medical billing dispute letter for this patient.

PATIENT: {bill.patient_name or 'The Patient'}
PROVIDER: {bill.provider_name or 'The Provider'}
DATE OF SERVICE: {bill.date_of_service or 'as listed on the bill'}
ACCOUNT NUMBER: {bill.account_number or 'as listed on the bill'}
TOTAL ESTIMATED OVERCHARGE: ${total_overcharge:.2f}

BILLING ISSUES FOUND:
{issues_summary_text}

PRICING ANOMALIES:
{pricing_summary_text if pricing_summary_text else 'None'}

Write a formal dispute letter that:
1. Opens with patient information and account details
2. States the purpose clearly — disputing specific charges
3. Lists each issue with the specific CPT code, amount billed, and the rule violated
4. Cites relevant CMS guidelines, AMA CPT rules, or NCCI edits
5. Demands specific corrective action — itemized corrections, refunds, or documentation
6. Sets a 30-day response deadline
7. Mentions escalation to state insurance commissioner and OIG if unresolved
8. Closes professionally

Write the complete letter in plain text, ready to send."""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
    )

    letter_text = response.choices[0].message.content.strip()
    issues_summary = [f"{i.issue_type} — CPT {i.cpt_code}: ${i.estimated_overcharge:.2f} overcharge" for i in issues[:8]]
    cpt_refs = list({i.cpt_code for i in issues if i.cpt_code})

    return AppealLetter(
        letter_text=letter_text,
        issues_summary=issues_summary,
        total_estimated_overcharge=round(total_overcharge, 2),
        cpt_references=cpt_refs,
    )
