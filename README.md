# MedAudit AI 🏥

**AI-powered medical bill auditor** that detects upcoding, duplicate charges, NCCI unbundling violations, and pricing anomalies — then drafts a ready-to-send dispute letter automatically.

---

## What It Does

Medical billing errors affect an estimated 80% of bills. MedAudit AI parses your bill, extracts every CPT code, benchmarks each charge against CMS Medicare rates, and runs AI analysis to surface overcharges before you pay them.

| Capability | Details |
|---|---|
| 📄 PDF Parsing | 3-engine extraction pipeline (pdfplumber, PyMuPDF, fallback OCR) |
| 🔍 CPT Extraction | 5-strategy pattern matching with confidence scoring |
| 💰 Benchmark Comparison | Per-procedure pricing vs. CMS Medicare database |
| 🤖 AI Audit | Upcoding, duplicates, unbundling, and anomaly detection |
| 📊 Risk Scoring | Per-charge risk level with confidence percentages |
| 📝 Dispute Letter | Auto-generated, citation-backed appeal letter |
| ⚡ Speed | Full audit in under 10 seconds |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI · Python 3.11 · pdfplumber · PyMuPDF |
| AI | OpenAI GPT-4.1-mini · RAG pipeline |
| Frontend | React 18 · Tailwind CSS · Framer Motion |
| Data | CMS Medicare Benchmark Database (JSON) |

---

## Project Structure

```
medical_bill_audit/
├── backend/
│   ├── app/
│   │   ├── data/          # CMS benchmark JSON files
│   │   ├── models/        # Pydantic schemas
│   │   ├── routes/        # FastAPI route handlers
│   │   └── services/      # PDF parser, auditor, AI logic
│   ├── sample_bills/      # Test PDFs (gitignored)
│   ├── debug.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── index.html
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### 1. Clone & configure

```bash
git clone https://github.com/your-username/medical_bill_audit.git
cd medical_bill_audit
```

Create `backend/.env`:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Run the backend

```bash
cd backend

python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
uvicorn app.main:app --reload```

Backend → `http://localhost:8000`  
API docs → `http://localhost:8000/docs`

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend → `http://localhost:5173`

---

## How It Works

```
Upload PDF  →  Parse (3 engines)  →  Extract CPT codes  →  CMS benchmark lookup
                                                                    ↓
              Dispute Letter  ←  AI analysis  ←  Risk scoring  ←  Anomaly detection
```

1. **Parse** — pdfplumber, PyMuPDF, and an OCR fallback ensure extraction even from scanned bills
2. **Extract** — 5 regex and heuristic strategies identify CPT codes, quantities, and billed amounts
3. **Benchmark** — each line item is compared against the CMS Medicare fee schedule for your region
4. **Analyze** — GPT-4.1-mini audits for upcoding patterns, duplicate billing, NCCI bundling violations, and statistical outliers
5. **Report** — results are returned as structured JSON with a ready-to-send dispute letter

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/audit` | Upload a bill PDF and receive full audit results |
| `GET` | `/benchmarks/{cpt_code}` | Look up CMS pricing for a specific CPT code |
| `GET` | `/health` | Health check |

Full interactive docs available at `/docs` when the backend is running.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | Your OpenAI API key |

---

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Commit your changes (`git commit -m 'Add my change'`)
4. Push and open a pull request

---

## Disclaimer

MedAudit AI is an assistive tool and does not constitute legal or medical advice. Always verify findings with a qualified medical billing advocate before submitting a formal dispute.

---

## License

MIT © 2025