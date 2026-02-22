from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class RiskLevel(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


class CPTEntry(BaseModel):
    code: str
    description: Optional[str] = None
    billed_amount: float
    service_date: Optional[str] = None
    units: Optional[int] = 1


class LineItem(BaseModel):
    cpt_code: str
    description: Optional[str] = None
    billed_amount: float
    date_of_service: Optional[str] = None
    icd10_code: Optional[str] = None
    units: int = 1


class ExtractedBill(BaseModel):
    provider_name: Optional[str] = None
    patient_name: Optional[str] = None
    service_dates: List[str] = []
    cpt_codes: List[CPTEntry] = []
    icd_codes: List[str] = []
    total_billed: float = 0.0
    is_inpatient: Optional[bool] = None
    insurance_paid: Optional[float] = None
    patient_responsibility: Optional[float] = None
    raw_text_snippet: Optional[str] = None
    date_of_service: Optional[str] = None
    account_number: Optional[str] = None
    insurance_name: Optional[str] = None
    total_amount: float = 0.0

    @property
    def line_items(self) -> List[LineItem]:
        return [
            LineItem(
                cpt_code=e.code,
                description=e.description,
                billed_amount=e.billed_amount,
                date_of_service=e.service_date,
                icd10_code=self.icd_codes[i] if i < len(self.icd_codes) else None,
                units=e.units or 1,
            )
            for i, e in enumerate(self.cpt_codes)
        ]


# ── Single unified issue class used by EVERYTHING ─────────────────────────
class BillingIssue(BaseModel):
    issue_type: str
    cpt_code: Optional[str] = None
    description: str
    rule_triggered: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    risk_level: str = "medium"
    estimated_overcharge: float = 0.0
    suggested_action: str = ""
    cpt_reference: Optional[str] = None

# Both names point to the exact same class — zero type mismatch
AuditIssue = BillingIssue


class PricingResult(BaseModel):
    cpt_code: str
    description: Optional[str] = None
    billed_amount: float
    benchmark_median: float
    benchmark_low: float = 0.0
    benchmark_high: float = 0.0
    deviation_percent: float
    estimated_fair_price: float = 0.0
    estimated_overcharge: float
    is_flagged: bool
    confidence_score: float = 0.0
    category: Optional[str] = None


class AppealLetter(BaseModel):
    patient_name: Optional[str] = None
    provider_name: Optional[str] = None
    letter_text: str
    issues_summary: List[str]
    total_estimated_overcharge: float
    cpt_references: List[str]


# ── Single unified result class used by EVERYTHING ────────────────────────
class AuditResult(BaseModel):
    extracted_bill: ExtractedBill
    issues: List[BillingIssue]
    pricing_results: List[PricingResult]
    appeal_letter: AppealLetter
    total_billed: float
    estimated_fair_total: float
    estimated_savings: float
    overall_confidence: float
    risk_score: float
    appeal_success_probability: float
    issue_count: int
    audit_summary: Optional[str] = None
    rag_context_used: List[str] = []

# Both names point to the exact same class — zero type mismatch
AuditReport = AuditResult
