import json
import logging
import numpy as np
from pathlib import Path
from typing import List
from openai import OpenAI
from app.config import OPENAI_API_KEY, CHROMA_PERSIST_DIR

logger = logging.getLogger(__name__)
_client = OpenAI(api_key=OPENAI_API_KEY)
_EMBED_MODEL = "text-embedding-3-small"
_store = None

ADVANCED_KNOWLEDGE = [
    {"id": "em_coding_2026",
     "text": "2026 AMA E&M Office Visit Guidelines: Established patients — 99211 minimal, 99212=10-19min or straightforward MDM, 99213=20-29min or low MDM, 99214=30-39min or moderate MDM, 99215=40-54min or high MDM. New patients — 99202=15-29min, 99203=30-44min, 99204=45-59min, 99205=60-74min. Code selection based on TOTAL time or Medical Decision Making (MDM). Documentation must support the level billed. Upcoding to higher level without documentation = Medicare fraud."},
    {"id": "upcoding_patterns",
     "text": "Common upcoding fraud patterns: (1) 99215 billed for routine follow-ups — requires 40-54 min or high MDM with multiple diagnoses/medications. (2) 99285 ED Level 5 for minor complaints like sore throat or sprain — requires high complexity MDM with threat to life or severe morbidity. (3) 99233 subsequent hospital care for brief daily notes — requires high complexity. (4) 99223 initial inpatient for low-complexity admission. OIG identifies upcoding as top Medicare fraud. Penalty: exclusion + $10,000 per claim + 3x overpayment."},
    {"id": "duplicate_billing_rules",
     "text": "Duplicate billing rules: Same CPT code + same date + same provider + same patient = duplicate claim. Medicare pays once only. Allowed exceptions requiring modifiers: bilateral procedures use modifier -50, staged use -58, repeat same day use -76, repeat different physician use -77. Without modifier, second identical charge is fraud. Common in lab tests, imaging, E&M visits."},
    {"id": "ncci_unbundling",
     "text": "NCCI unbundling rules: CMS edit pairs that cannot be billed together. 45380 (colonoscopy with biopsy) includes 45378 (diagnostic) — billing both = $1,500-3,200 overcharge. 43239 (EGD with biopsy) includes 43235. 85025 (CBC with diff) includes 85027. 93000 (complete ECG) includes 93005 and 93010 separately. Unbundling = False Claims Act fraud."},
    {"id": "inpatient_outpatient_rules",
     "text": "CMS Two-Midnight Rule: Inpatient admission requires physician expectation of care spanning at least TWO midnights documented in medical record. Stays under two midnights = outpatient or observation, NOT inpatient. Using inpatient codes 99221-99223 or 99231-99233 for short stays = incorrect billing. Reclassification can reduce charges 20-40%."},
    {"id": "modifier_abuse",
     "text": "Modifier abuse: Modifier -25 (separate E&M same day as procedure) requires documentation of separate evaluation. OIG top audit target. Modifier -59 (distinct procedural service) used to bypass NCCI edits — requires truly distinct service or anatomy. Modifier -51 reduces additional procedure payments. Appending modifiers without documentation = False Claims Act violation up to $23,000 per claim."},
    {"id": "medical_necessity",
     "text": "Medical necessity: Every billed service must be medically necessary per CMS LCD and NCD policies. ICD-10 diagnosis must support procedure. MRI brain (70553) requires neurological indication — not Z00.00 (routine checkup). PET scan (78816) requires oncological or dementia workup. Echo (93306) requires cardiac indication. Services without supporting diagnosis = denied claim and overpayment demand."},
    {"id": "cms_fee_schedule_benchmarks",
     "text": "2026 CMS Medicare key rates: 99213=$111, 99214=$167, 99215=$232, 99285=$319, 71046=$56, 93000=$29, 85025=$11, 80053=$15, 36415=$4, 70553=$612, 93306=$685, 27447=$1802, 45378=$325, 45380=$430, 96372=$25, 99221=$118, 99223=$263, 99291=$420, 47562=$1155, 93452=$1845. Private payers 115-200% of Medicare. Bills exceeding 200% of Medicare = suspicious."},
    {"id": "global_surgical_package",
     "text": "CMS Global Surgical Package: Major surgeries have 90-day global period. Minor surgeries 0 or 10 days. Package includes pre-op day before, intraoperative, all post-op care. Billing E&M within global period without modifier -24 (unrelated) or -58 (staged) = unbundling. Billing post-op office visits within 90 days of major surgery without modifier is incorrect."},
    {"id": "lab_panel_rules",
     "text": "Lab panel bundling: CMP (80053) includes glucose, BUN, creatinine, calcium, sodium, potassium, CO2, chloride, albumin, total protein, ALT, AST, bilirubin, alkaline phosphatase — cannot bill components separately. CBC with diff (85025) includes CBC without diff (85027) and differential (85004). Cannot bill panel and individual components together — NCCI violation."},
    {"id": "no_surprises_act",
     "text": "No Surprises Act 2022: Patients at in-network facilities cannot receive surprise bills from out-of-network emergency physicians, radiologists, anesthesiologists, pathologists, neonatologists. Maximum liability = in-network cost-sharing. Air ambulance balance billing prohibited. Violations: report to CMS 1-800-985-3059."},
    {"id": "appeal_process_detailed",
     "text": "Medical billing appeal process: Step 1 — Request itemized bill and medical records. Step 2 — Compare to EOB from insurer. Step 3 — Internal appeal to provider billing dept. Step 4 — Insurance formal appeal within 180 days of EOB (ACA required). Step 5 — External Independent Medical Review. Step 6 — State Insurance Commissioner. Step 7 — OIG fraud hotline 1-800-HHS-TIPS. Success rates: duplicate billing 85%, upcoding 60%, pricing 45%."},
    {"id": "observation_status",
     "text": "Observation vs inpatient: Observation patients are outpatients even if overnight. Hospital must notify within 36 hours (NOTICE Act). Observation uses codes 99218-99220 (initial) and 99224-99226 (subsequent). Inpatient codes 99221-99233 for observation patients = incorrect billing. Under Medicare observation patients pay 20% coinsurance per service vs inpatient deductible."},
    {"id": "facility_vs_physician_fees",
     "text": "Hospital facility fees vs physician fees: Two separate bills — (1) facility fee for hospital use equipment staff, (2) professional fee for physician services. Both billed separately. ED facility fee (99281-99285) separate from physician E&M. Together can total $2,000-$8,000 for ED visits. Patients receive two separate bills. Verify both against EOB."},
    {"id": "upcoding_ed_levels",
     "text": "ED level requirements: 99281=minor self-limited 5-10min. 99282=low complexity minor acute. 99283=moderate complexity acute with workup. 99284=high complexity acute with systemic symptoms. 99285=HIGH complexity ONLY requires high MDM with threat to life OR 70+ minutes total time. Billing 99285 for every patient regardless of complexity = fraud."},
    {"id": "preventive_vs_diagnostic",
     "text": "Preventive vs diagnostic billing: Preventive (99381-99397) = routine wellness, covered 100% ACA. Diagnostic (99202-99215) = illness treatment, subject to deductible/copay. Billing diagnostic E&M when patient came for preventive visit = overcharging. Modifier -25 required if separate significant problem addressed during preventive visit. Very common billing error."},
    {"id": "telehealth_billing",
     "text": "Telehealth billing rules: Audio-video visits use same CPT as in-person (99202-99215) with modifier -95 or -GT. Audio-only uses 99441-99443. Must document patient consent. Place of service code 02 or 10 required. Billing in-person rates for telephone calls without video = overcharging. Telehealth cannot be billed for services requiring physical examination."},
    {"id": "coding_specificity",
     "text": "ICD-10 coding specificity: Codes must be as specific as possible. Unspecified codes not acceptable when specific information in chart. Using higher-severity diagnosis without documentation to justify higher-level procedure = upcoding. Incorrect ICD-10 can indicate fraud. Example: using sepsis code when chart shows simple UTI."},
    {"id": "dme_billing_rules",
     "text": "DME billing rules: Requires Certificate of Medical Necessity from physician. Medicare requires face-to-face exam before DME order. Fraud: billing for DME not delivered, billing upgrades without consent. Wheelchair, CPAP, brace fraud are top OIG targets. Patients verify all billed equipment received. Report to 1-800-HHS-TIPS."},
    {"id": "oig_fraud_indicators",
     "text": "OIG top fraud indicators 2026: (1) E&M upcoding — billing 99215 or 99285 for majority of patients. (2) Services not documented in record. (3) Duplicate claims same date. (4) Unbundling lab panels. (5) Inpatient codes for outpatient care. (6) Modifier -59 overuse. (7) Medically unnecessary services. (8) Phantom billing — charges for services never rendered. Report: 1-800-HHS-TIPS or oig.hhs.gov."},
]

def _store_path():
    p = Path(CHROMA_PERSIST_DIR) / "vector_store.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def _embed_texts(texts: List[str]) -> List[List[float]]:
    response = _client.embeddings.create(model=_EMBED_MODEL, input=texts)
    return [item.embedding for item in response.data]

def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / (denom + 1e-9))

def _keyword_fallback(query: str, n: int) -> List[str]:
    qwords = set(query.lower().split())
    scored = sorted(ADVANCED_KNOWLEDGE,
                    key=lambda d: len(qwords & set(d["text"].lower().split())),
                    reverse=True)
    return [d["text"] for d in scored[:n]]

def _load_or_build() -> dict:
    global _store
    if _store is not None:
        return _store
    sp = _store_path()
    if sp.exists():
        try:
            with open(sp) as f:
                data = json.load(f)
            if len(data.get("documents", [])) >= len(ADVANCED_KNOWLEDGE):
                _store = data
                logger.info(f"Loaded vector store: {len(_store['documents'])} documents")
                return _store
        except Exception as e:
            logger.warning(f"Corrupt vector store, rebuilding: {e}")
    docs = [item["text"] for item in ADVANCED_KNOWLEDGE]
    ids  = [item["id"]   for item in ADVANCED_KNOWLEDGE]
    try:
        embeddings = _embed_texts(docs)
        logger.info(f"Built embeddings for {len(docs)} documents via OpenAI {_EMBED_MODEL}")
    except Exception as e:
        logger.error(f"Embedding failed: {e}. Using zero vectors — keyword fallback active.")
        embeddings = [[0.0] * 1536 for _ in docs]
    _store = {"documents": docs, "ids": ids, "embeddings": embeddings}
    try:
        with open(sp, "w") as f:
            json.dump(_store, f)
        logger.info(f"Vector store saved: {sp}")
    except Exception as e:
        logger.warning(f"Could not persist vector store: {e}")
    return _store

def query_knowledge_base(query: str, n_results: int = 4) -> List[str]:
    try:
        store = _load_or_build()
        if not store or not store.get("documents"):
            return _keyword_fallback(query, n_results)
        embeddings = np.array(store["embeddings"])
        if not np.any(embeddings):
            return _keyword_fallback(query, n_results)
        try:
            query_emb = np.array(_embed_texts([query])[0])
        except Exception:
            return _keyword_fallback(query, n_results)
        sims = [_cosine_sim(query_emb, embeddings[i]) for i in range(len(embeddings))]
        top_k = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:n_results]
        return [store["documents"][i] for i in top_k]
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        return _keyword_fallback(query, n_results)

def initialize_rag():
    try:
        _load_or_build()
        logger.info("Advanced RAG knowledge base ready (20 documents, OpenAI embeddings)")
    except Exception as e:
        logger.error(f"RAG initialization failed: {e}")
