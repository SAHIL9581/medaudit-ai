# MedAudit AI 🏥

> AI-powered medical bill auditor that catches overcharges before you pay them.

Medical billing errors affect an estimated **80% of bills**. MedAudit AI parses your bill, extracts every CPT code, benchmarks each charge against CMS Medicare rates, and runs a full AI audit — then drafts a ready-to-send dispute letter automatically.

---

## Features

- **PDF Parsing** — 3-engine extraction pipeline (pdfplumber, PyMuPDF, fallback OCR)
- **CPT Extraction** — 5-strategy pattern matching with per-code confidence scoring
- **Benchmark Comparison** — Per-procedure pricing vs. the CMS Medicare database
- **AI Audit** — Detects upcoding, duplicate charges, NCCI unbundling violations, and pricing anomalies
- **Risk Scoring** — Per-charge risk level with confidence percentages
- **Dispute Letter** — Auto-generated, citation-backed appeal letter ready to send
- **Multilingual Chatbot** — Sarvam AI-powered support with regional language options
- **Fast** — Full audit in under 10 seconds

---

## How It Works

```
Upload Bill → Parse PDF → Extract CPT Codes → Benchmark vs. CMS → AI Audit → Dispute Letter
```

1. **Upload** your medical bill (PDF)
2. **MedAudit** extracts all CPT procedure codes using a multi-strategy parser
3. Each code is **benchmarked** against CMS Medicare reimbursement rates
4. An **AI model** reviews the full bill for upcoding, duplicates, and unbundling violations
5. You receive a **risk-scored report** and a ready-to-send dispute letter

---

## Tech Stack

**Backend**
- FastAPI · Python 3.11
- pdfplumber · PyMuPDF · OCR fallback

**AI**
- OpenAI GPT-4.1-mini
- RAG pipeline
- Sarvam AI (multilingual)

**Frontend**
- React 18 · Tailwind CSS · Framer Motion · Vite

**Data**
- CMS Medicare Benchmark Database (JSON)
- NCCI Edits · LCD Mappings

---

## Project Structure

```
medaudit-ai/
├── backend/
│   ├── main.py               # FastAPI app & routes
│   ├── parser/               # PDF + CPT extraction engines
│   ├── benchmark/            # CMS rate lookup
│   ├── audit/                # AI audit logic & risk scoring
│   └── letter/               # Dispute letter generation
├── frontend/
│   ├── src/
│   │   ├── components/       # UI components
│   │   └── pages/            # App views
│   └── vite.config.ts
├── data/
│   ├── cms_rates.json        # CMS Medicare benchmark data
│   ├── ncci_edits.json       # NCCI bundling rules
│   └── lcd_mappings.json     # Local coverage determinations
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key
- Sarvam AI API key

### Installation

```bash
# Clone the repo
git clone https://github.com/your-org/medaudit-ai
cd medaudit-ai

# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173).

---

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4.1-mini |
| `SARVAM_API_KEY` | Sarvam AI key for multilingual chat |
| `CMS_DATA_PATH` | Path to CMS benchmark JSON |

---

## Disclaimer

MedAudit AI is an informational tool and does not constitute legal or medical advice. Always consult a qualified billing advocate or attorney before submitting a formal dispute.