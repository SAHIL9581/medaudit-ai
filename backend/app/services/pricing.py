import json
import logging
from pathlib import Path
from typing import List
from app.models.schemas import CPTEntry, PricingResult

logger = logging.getLogger(__name__)

_BENCHMARKS_PATH = Path(__file__).parent.parent / "data" / "cpt_benchmarks.json"
_benchmarks: dict = {}

# Flag if billed is more than this % above benchmark median
_FLAG_THRESHOLD_PCT = 30.0


def _load_benchmarks() -> dict:
    global _benchmarks
    if not _benchmarks:
        try:
            with open(_BENCHMARKS_PATH) as f:
                _benchmarks = json.load(f)
            logger.info(f"Loaded {len(_benchmarks)} CPT benchmarks from {_BENCHMARKS_PATH}")
        except Exception as e:
            logger.error(f"Failed to load CPT benchmarks: {e}")
            _benchmarks = {}
    return _benchmarks


def compare_pricing(cpt_entries: List[CPTEntry]) -> List[PricingResult]:
    benchmarks = _load_benchmarks()
    results = []

    for entry in cpt_entries:
        code   = entry.code
        billed = entry.billed_amount

        if code in benchmarks:
            bench      = benchmarks[code]
            median     = bench["median"]
            range_low  = bench.get("range_low",  median * 0.70)
            range_high = bench.get("range_high", median * 1.50)
            description = bench.get("description", "")
            category    = bench.get("category", "Unknown")

            # Deviation from median (positive = overbilled)
            deviation = ((billed - median) / median * 100) if median > 0 else 0.0

            # Overcharge = amount above the HIGH end of the fair range
            # (not just above median — gives patient the benefit of the doubt)
            overcharge = max(0.0, billed - range_high)

            # Flag if more than 30% above median
            is_flagged = deviation > _FLAG_THRESHOLD_PCT

            # Confidence scoring
            if billed <= range_high:
                confidence = 0.85
            else:
                excess_ratio = (billed - range_high) / max(range_high, 1.0)
                confidence = min(0.99, 0.85 + excess_ratio * 0.1)

            results.append(PricingResult(
                cpt_code=code,
                description=description,
                billed_amount=round(billed, 2),
                benchmark_median=round(median, 2),
                benchmark_low=round(range_low, 2),
                benchmark_high=round(range_high, 2),
                deviation_percent=round(deviation, 2),
                estimated_fair_price=round(median, 2),
                estimated_overcharge=round(overcharge, 2),
                is_flagged=is_flagged,
                confidence_score=round(confidence, 3),
                category=category,
            ))

        else:
            # Unknown CPT — flag for manual review but no overcharge estimate
            results.append(PricingResult(
                cpt_code=code,
                description="Unknown CPT code — manual review required",
                billed_amount=round(billed, 2),
                benchmark_median=0.0,
                benchmark_low=0.0,
                benchmark_high=0.0,
                deviation_percent=0.0,
                estimated_fair_price=0.0,
                estimated_overcharge=0.0,
                is_flagged=True,
                confidence_score=0.40,
                category="Unknown",
            ))

    flagged = [r for r in results if r.is_flagged]
    logger.info(
        f"Pricing analysis: {len(flagged)}/{len(results)} codes flagged, "
        f"total overcharge: ${sum(r.estimated_overcharge for r in results):.2f}"
    )
    return results
