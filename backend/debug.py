from app.services.parser import extract_text_from_pdf
import json

benchmarks = json.load(open('app/data/cpt_benchmarks.json'))

# Show raw text for problem bills
for bill_path, label in [
    ("sample_bills/bill_1_upcoding_anomaly.pdf",    "BILL 1"),
    ("sample_bills/bill_2_duplicate_unbundling.pdf", "BILL 2"),
    ("sample_bills/bill_5_multiline_format.pdf",     "BILL 5"),
    ("sample_bills/bill_6_mixed_format.pdf",         "BILL 6"),
]:
    print(f"\n{'='*55}")
    print(f"RAW TEXT — {label}")
    print('='*55)
    text = extract_text_from_pdf(bill_path)
    print(text[:2000])
    print("...")
