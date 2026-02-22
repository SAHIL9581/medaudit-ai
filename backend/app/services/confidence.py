from typing import List
from app.models.schemas import BillingIssue, PricingResult, RiskLevel


def calculate_risk_score(
    issues: List[BillingIssue],
    pricing_results: List[PricingResult],
) -> float:
    """
    Weighted risk score 0.0 - 1.0.
    Components:
    - Issue severity (40%)
    - Pricing deviation (35%)
    - Issue count (25%)
    """
    if not issues and not pricing_results:
        return 0.0

    # Issue severity score
    severity_map = {RiskLevel.LOW: 0.2, RiskLevel.MEDIUM: 0.5, RiskLevel.HIGH: 1.0}
    severity_score = 0.0
    if issues:
        weighted = sum(
            severity_map.get(i.risk_level, 0.5) * i.confidence for i in issues
        )
        severity_score = min(1.0, weighted / len(issues))

    # Pricing deviation score
    pricing_score = 0.0
    if pricing_results:
        flagged = [p for p in pricing_results if p.is_flagged]
        if flagged:
            avg_dev = sum(min(abs(p.deviation_percent), 200) / 200 for p in flagged) / len(flagged)
            pricing_score = min(1.0, avg_dev * (len(flagged) / len(pricing_results)) * 2)

    # Issue count score
    count_score = min(1.0, len(issues) / 10.0)

    risk = (severity_score * 0.40) + (pricing_score * 0.35) + (count_score * 0.25)
    return round(min(1.0, risk), 3)


def calculate_overall_confidence(
    issues: List[BillingIssue],
    pricing_results: List[PricingResult],
) -> float:
    """Average confidence across all detected signals."""
    scores = [i.confidence for i in issues] + [p.confidence_score for p in pricing_results]
    if not scores:
        return 0.5
    return round(sum(scores) / len(scores), 3)


def calculate_appeal_success_probability(
    issues: List[BillingIssue],
    pricing_results: List[PricingResult],
    risk_score: float,
) -> float:
    """
    Heuristic appeal success probability 0.0 - 1.0.
    Higher when:
    - Clear upcoding/duplicate issues (high confidence)
    - Large pricing deviation
    - Multiple independent issues
    """
    base = 0.35

    # Bonus for high-confidence clear-cut issues
    upcoding_issues = [
        i for i in issues
        if any(kw in i.issue_type.lower() for kw in ["upcode", "duplicate", "unbundle"])
        and i.confidence > 0.75
    ]
    base += min(0.25, len(upcoding_issues) * 0.08)

    # Bonus for large overcharges
    total_overcharge = sum(p.estimated_overcharge for p in pricing_results)
    if total_overcharge > 500:
        base += 0.10
    if total_overcharge > 2000:
        base += 0.10

    # Bonus for risk score (well-documented case)
    base += risk_score * 0.20

    return round(min(0.95, base), 3)
