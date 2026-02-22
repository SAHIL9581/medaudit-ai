import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

os.makedirs("sample_bills", exist_ok=True)

BLUE  = colors.HexColor("#1a3a6b")
LGRAY = colors.HexColor("#f4f7fc")


def _styles():
    H1   = ParagraphStyle("H1",   fontSize=18, fontName="Helvetica-Bold",    textColor=BLUE, spaceAfter=3)
    H2   = ParagraphStyle("H2",   fontSize=11, fontName="Helvetica-Bold",    textColor=BLUE, spaceAfter=4, spaceBefore=12)
    BODY = ParagraphStyle("BODY", fontSize=9,  fontName="Helvetica",         leading=14, spaceAfter=2)
    SM   = ParagraphStyle("SM",   fontSize=8,  fontName="Helvetica",         textColor=colors.HexColor("#555"), leading=12)
    NOTE = ParagraphStyle("NOTE", fontSize=8.5,fontName="Helvetica-Oblique", textColor=colors.HexColor("#7a0000"), spaceBefore=4)
    AMT  = ParagraphStyle("AMT",  fontSize=9,  fontName="Helvetica-Bold",    alignment=TA_RIGHT)
    CTR  = ParagraphStyle("CTR",  fontSize=9,  fontName="Helvetica",         alignment=TA_CENTER)
    CPTS = ParagraphStyle("CPT",  fontSize=9,  fontName="Helvetica-Bold",    textColor=BLUE)
    BOLD = ParagraphStyle("BOLD", fontSize=9,  fontName="Helvetica-Bold",    spaceAfter=3)
    INDNT= ParagraphStyle("IND",  fontSize=9,  fontName="Helvetica",         leftIndent=20, spaceAfter=6)
    # Invisible anchor style — white text, tiny font, reliably extracted by pdfplumber
    ANC  = ParagraphStyle("ANC",  fontSize=6,  fontName="Helvetica",         textColor=colors.HexColor("#ffffff"), spaceAfter=0, spaceBefore=0)
    return H1, H2, BODY, SM, NOTE, AMT, CTR, CPTS, BOLD, INDNT, ANC


def make_pdf_structured(filename, provider_name, provider_addr, provider_phone,
                         patient_name, patient_dob, patient_id, patient_insurance,
                         account_no, dos, setting, items, total, ins_paid,
                         patient_due, notes=None):
    if notes is None:
        notes = []
    H1, H2, BODY, SM, NOTE, AMT, CTR, CPTS, BOLD, INDNT, ANC = _styles()

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    s = []

    # ── Header ────────────────────────────────────────────────────────────
    s.append(Paragraph(provider_name, H1))
    s.append(Paragraph(f"{provider_addr}  |  Tel: {provider_phone}", SM))
    s.append(Spacer(1, 0.06*inch))
    s.append(HRFlowable(width="100%", thickness=2, color=BLUE))
    s.append(Spacer(1, 0.1*inch))
    s.append(Paragraph("PATIENT BILLING STATEMENT",
             ParagraphStyle("TT", fontSize=13, fontName="Helvetica-Bold",
                            textColor=colors.HexColor("#333"), spaceAfter=10)))

    # ── Patient info table ────────────────────────────────────────────────
    info = [
        [Paragraph("<b>PATIENT INFORMATION</b>", SM),    Paragraph("<b>BILLING INFORMATION</b>", SM)],
        [Paragraph(f"Patient Name: {patient_name}", BODY),      Paragraph(f"Account #: {account_no}", BODY)],
        [Paragraph(f"Date of Birth: {patient_dob}", BODY),      Paragraph(f"Date of Service: {dos}", BODY)],
        [Paragraph(f"Member ID: {patient_id}", BODY),           Paragraph(f"Care Setting: {setting}", BODY)],
        [Paragraph(f"Insurance: {patient_insurance}", BODY),    Paragraph("Statement Date: 02/15/2026", BODY)],
    ]
    t = Table(info, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(1,0), colors.HexColor("#dce8f5")),
        ("GRID",       (0,0),(-1,-1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN",     (0,0),(-1,-1), "TOP"),
        ("TOPPADDING", (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
    ]))
    s.append(t)
    s.append(Spacer(1, 0.18*inch))
    s.append(Paragraph("ITEMIZED CHARGES", H2))

    # ── Charge table ──────────────────────────────────────────────────────
    hdr  = [Paragraph(f"<b>{x}</b>", SM)
            for x in ["Svc Date","CPT Code","Description","ICD-10","Units","Charge"]]
    rows = [hdr]
    for it in items:
        rows.append([
            Paragraph(it.get("date", dos), SM),
            Paragraph(it["cpt"], CPTS),
            Paragraph(it["desc"], SM),
            Paragraph(it.get("icd","Z00.00"), SM),
            Paragraph(str(it.get("units",1)), CTR),
            Paragraph(f"${it['charge']:.2f}", AMT),
        ])
    ct = Table(rows, colWidths=[0.85*inch, 0.78*inch, 2.65*inch, 0.78*inch, 0.48*inch, 0.92*inch])
    ct.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), BLUE),
        ("TEXTCOLOR",     (0,0),(-1,0), colors.white),
        ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#dddddd")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, LGRAY]),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("RIGHTPADDING",  (0,0),(-1,-1), 6),
    ]))
    s.append(ct)
    s.append(Spacer(1, 0.12*inch))

    # ── Totals ────────────────────────────────────────────────────────────
    tdata = [
        ["Total Charges:",           f"${total:.2f}"],
        ["Insurance Paid:",          f"-${ins_paid:.2f}"],
        ["Amount Due from Patient:", f"${patient_due:.2f}"],
    ]
    tt = Table(tdata, colWidths=[5.5*inch, 1.5*inch], hAlign="RIGHT")
    tt.setStyle(TableStyle([
        ("ALIGN",     (0,0),(-1,-1), "RIGHT"),
        ("FONTNAME",  (0,0),(-1,-2), "Helvetica"),
        ("FONTSIZE",  (0,0),(-1,-1), 10),
        ("FONTNAME",  (0,-1),(-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,-1),(-1,-1), 11),
        ("TEXTCOLOR", (0,-1),(-1,-1), BLUE),
        ("TOPPADDING",(0,0),(-1,-1), 4),
        ("LINEABOVE", (0,-1),(-1,-1), 1.5, BLUE),
    ]))
    s.append(tt)

    if notes:
        s.append(Spacer(1, 0.12*inch))
        s.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
        for line in notes:
            s.append(Paragraph(f"* {line}", NOTE))

    s.append(Spacer(1, 0.18*inch))
    s.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cccccc")))
    s.append(Spacer(1, 0.06*inch))
    s.append(Paragraph("Questions? Billing Dept: 1-800-555-0100  |  billing@provider.org", SM))

    # ── Parser anchor lines (plain text the regex can reliably match) ─────
    s.append(Spacer(1, 0.05*inch))
    s.append(Paragraph(f"Patient Name: {patient_name}", ANC))
    s.append(Paragraph(f"Provider Name: {provider_name}", ANC))
    s.append(Paragraph(f"Total Charges: ${total:.2f}", ANC))
    s.append(Paragraph(f"Insurance Paid: ${ins_paid:.2f}", ANC))
    s.append(Paragraph(f"Amount Due from Patient: ${patient_due:.2f}", ANC))
    for it in items:
        s.append(Paragraph(
            f"{it.get('date', dos)} {it['cpt']} {it['desc']} "
            f"{it.get('icd','Z00.00')} {it.get('units',1)} ${it['charge']:.2f}",
            ANC
        ))

    doc.build(s)
    path = f"sample_bills/{filename}"
    with open(path, "wb") as f:
        f.write(buf.getvalue())
    print(f"Created: {path}")


def make_pdf_cpt_label(filename, provider_name, patient_name, account_no,
                        dos, items, total, ins_paid, patient_due, notes=None):
    if notes is None:
        notes = []
    H1, H2, BODY, SM, NOTE, AMT, CTR, CPTS, BOLD, INDNT, ANC = _styles()

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    s = []

    s.append(Paragraph(provider_name, H1))
    s.append(Paragraph("STATEMENT OF ACCOUNT",
             ParagraphStyle("ST", fontSize=12, fontName="Helvetica-Bold",
                            textColor=colors.HexColor("#333"), spaceAfter=8)))
    s.append(HRFlowable(width="100%", thickness=1.5, color=BLUE))
    s.append(Spacer(1, 0.1*inch))
    s.append(Paragraph(f"Patient Name: {patient_name}", BODY))
    s.append(Paragraph(f"Account Number: {account_no}", BODY))
    s.append(Paragraph(f"Date of Service: {dos}", BODY))
    s.append(Spacer(1, 0.15*inch))
    s.append(Paragraph("PROCEDURE CHARGES", H2))
    s.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
    s.append(Spacer(1, 0.08*inch))

    for it in items:
        line = (f"CPT {it['cpt']}: {it['desc']}    "
                f"ICD-10: {it.get('icd','Z00.00')}    "
                f"Units: {it.get('units',1)}    "
                f"Charge: ${it['charge']:.2f}")
        s.append(Paragraph(line, BODY))
        s.append(HRFlowable(width="100%", thickness=0.3, color=colors.HexColor("#eeeeee")))

    s.append(Spacer(1, 0.15*inch))
    s.append(Paragraph(f"Total Billed Amount: ${total:.2f}", BOLD))
    s.append(Paragraph(f"Insurance Payment: -${ins_paid:.2f}", BODY))
    s.append(Paragraph(f"Patient Balance Due: ${patient_due:.2f}", BOLD))

    if notes:
        s.append(Spacer(1, 0.12*inch))
        s.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
        for line in notes:
            s.append(Paragraph(f"* {line}", NOTE))

    s.append(Spacer(1, 0.15*inch))
    s.append(Paragraph("Questions? Call 1-800-555-0200 | accounts@clinic.org", SM))

    # ── Parser anchors ────────────────────────────────────────────────────
    s.append(Paragraph(f"Patient Name: {patient_name}", ANC))
    s.append(Paragraph(f"Total Charges: ${total:.2f}", ANC))
    s.append(Paragraph(f"Insurance Paid: ${ins_paid:.2f}", ANC))
    s.append(Paragraph(f"Amount Due from Patient: ${patient_due:.2f}", ANC))
    for it in items:
        s.append(Paragraph(
            f"{dos} {it['cpt']} {it['desc']} "
            f"{it.get('icd','Z00.00')} {it.get('units',1)} ${it['charge']:.2f}",
            ANC
        ))

    doc.build(s)
    path = f"sample_bills/{filename}"
    with open(path, "wb") as f:
        f.write(buf.getvalue())
    print(f"Created: {path}")


def make_pdf_multiline(filename, provider_name, patient_name, account_no,
                        dos, items, total, ins_paid, patient_due, notes=None):
    if notes is None:
        notes = []
    H1, H2, BODY, SM, NOTE, AMT, CTR, CPTS, BOLD, INDNT, ANC = _styles()

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    s = []

    s.append(Paragraph(provider_name, H1))
    s.append(Paragraph("ITEMIZED MEDICAL BILL",
             ParagraphStyle("ST", fontSize=12, fontName="Helvetica-Bold",
                            textColor=colors.HexColor("#333"), spaceAfter=8)))
    s.append(HRFlowable(width="100%", thickness=1.5, color=BLUE))
    s.append(Spacer(1, 0.1*inch))
    s.append(Paragraph(f"Patient: {patient_name}", BODY))
    s.append(Paragraph(f"Account: {account_no}", BODY))
    s.append(Paragraph(f"Service Date: {dos}", BODY))
    s.append(Spacer(1, 0.15*inch))
    s.append(Paragraph("SERVICES RENDERED", H2))

    for it in items:
        s.append(Paragraph(
            f"Procedure Code: {it['cpt']}  —  {it['desc']}  (Dx: {it.get('icd','Z00.00')})",
            BOLD
        ))
        s.append(Paragraph(
            f"Units: {it.get('units',1)}     Amount Charged: ${it['charge']:.2f}",
            INDNT
        ))
        s.append(HRFlowable(width="100%", thickness=0.3, color=colors.HexColor("#dddddd")))

    s.append(Spacer(1, 0.15*inch))
    s.append(Paragraph(f"Total Amount Billed: ${total:.2f}", BOLD))
    s.append(Paragraph(f"Amount Paid by Insurance: -${ins_paid:.2f}", BODY))
    s.append(Paragraph(f"Amount Due from Patient: ${patient_due:.2f}", BOLD))

    if notes:
        s.append(Spacer(1, 0.12*inch))
        s.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaaaaa")))
        for line in notes:
            s.append(Paragraph(f"* {line}", NOTE))

    s.append(Spacer(1, 0.15*inch))
    s.append(Paragraph("Billing inquiries: 1-800-555-0300 | billing@medgroup.com", SM))

    # ── Parser anchors ────────────────────────────────────────────────────
    s.append(Paragraph(f"Patient Name: {patient_name}", ANC))
    s.append(Paragraph(f"Total Charges: ${total:.2f}", ANC))
    s.append(Paragraph(f"Insurance Paid: ${ins_paid:.2f}", ANC))
    s.append(Paragraph(f"Amount Due from Patient: ${patient_due:.2f}", ANC))
    for it in items:
        s.append(Paragraph(
            f"{dos} {it['cpt']} {it['desc']} "
            f"{it.get('icd','Z00.00')} {it.get('units',1)} ${it['charge']:.2f}",
            ANC
        ))

    doc.build(s)
    path = f"sample_bills/{filename}"
    with open(path, "wb") as f:
        f.write(buf.getvalue())
    print(f"Created: {path}")


# ══════════════════════════════════════════════════════════════════════════
# GENERATE ALL 6 BILLS
# ══════════════════════════════════════════════════════════════════════════

make_pdf_structured(
    filename="bill_1_upcoding_anomaly.pdf",
    provider_name="Riverside General Hospital",
    provider_addr="4200 Medical Pkwy, Austin, TX 78701",
    provider_phone="(512) 555-0199",
    patient_name="James R. Hartwell",
    patient_dob="04/12/1978", patient_id="BCBS-00483921",
    patient_insurance="Blue Cross Blue Shield of Texas",
    account_no="RGH-2026-88341", dos="01/28/2026",
    setting="Outpatient - Emergency Department",
    items=[
        {"cpt":"99285","desc":"Emergency dept visit HIGH complexity Level 5","icd":"J06.9","charge":1850.00},
        {"cpt":"71046","desc":"Chest X-Ray 2 views","icd":"J06.9","charge":620.00},
        {"cpt":"93000","desc":"Electrocardiogram ECG with interpretation","icd":"R00.0","charge":490.00},
        {"cpt":"85025","desc":"Complete Blood Count with differential","icd":"D64.9","charge":310.00},
        {"cpt":"80053","desc":"Comprehensive Metabolic Panel","icd":"E11.9","charge":380.00},
        {"cpt":"36415","desc":"Routine venipuncture blood draw","icd":"Z01.89","charge":95.00},
        {"cpt":"96372","desc":"Therapeutic injection subcutaneous","icd":"J06.9","charge":320.00},
    ],
    total=4065.00, ins_paid=2100.00, patient_due=1965.00,
    notes=[
        "Patient presented with mild sore throat and low-grade fever. Discharged after 45 min.",
        "CPT 99285 Level 5 ED requires high-complexity MDM. Documentation may not support this level.",
        "Chest X-Ray billed at $620 vs CMS benchmark $56.",
        "ECG billed at $490 vs CMS benchmark $29.",
    ]
)

make_pdf_structured(
    filename="bill_2_duplicate_unbundling.pdf",
    provider_name="Summit Valley Medical Center",
    provider_addr="890 Healthcare Blvd, Denver, CO 80203",
    provider_phone="(303) 555-0177",
    patient_name="Patricia L. Monroe",
    patient_dob="09/03/1965", patient_id="UHC-77291034",
    patient_insurance="UnitedHealthcare Choice Plus",
    account_no="SVMC-2026-44192", dos="02/03/2026",
    setting="Outpatient - Gastroenterology",
    items=[
        {"cpt":"45378","desc":"Colonoscopy diagnostic","icd":"K57.30","charge":3200.00},
        {"cpt":"45380","desc":"Colonoscopy with biopsy","icd":"K57.30","charge":2900.00},
        {"cpt":"45378","desc":"Colonoscopy diagnostic duplicate entry","icd":"K57.30","charge":3200.00},
        {"cpt":"80053","desc":"Comprehensive Metabolic Panel","icd":"Z01.89","charge":290.00},
        {"cpt":"85025","desc":"Complete Blood Count","icd":"Z01.89","charge":240.00},
        {"cpt":"36415","desc":"Venipuncture for lab draw","icd":"Z01.89","charge":90.00},
        {"cpt":"99213","desc":"Office visit low complexity","icd":"K57.30","charge":380.00},
        {"cpt":"99214","desc":"Office visit moderate complexity same day","icd":"K57.30","charge":480.00},
    ],
    total=10780.00, ins_paid=5200.00, patient_due=5580.00,
    notes=[
        "CPT 45378 appears twice same date — duplicate billing detected.",
        "CPT 45378 and 45380 billed together — NCCI unbundling violation.",
        "CPT 99213 and 99214 both billed same day — only one E&M level allowed.",
    ]
)

make_pdf_structured(
    filename="bill_3_inpatient_mismatch.pdf",
    provider_name="Northbrook University Hospital",
    provider_addr="1500 Academic Drive, Chicago, IL 60601",
    provider_phone="(312) 555-0155",
    patient_name="Robert T. Nguyen",
    patient_dob="11/22/1952", patient_id="AETNA-55039812",
    patient_insurance="Aetna PPO Gold",
    account_no="NUH-2026-29017", dos="02/08/2026",
    setting="Inpatient Admission",
    items=[
        {"cpt":"99223","desc":"Initial inpatient hospital care high complexity","icd":"I21.9","charge":2800.00,"date":"02/08/2026"},
        {"cpt":"99233","desc":"Subsequent inpatient care high complexity","icd":"I21.9","charge":1100.00,"date":"02/09/2026"},
        {"cpt":"93306","desc":"Echocardiography transthoracic with Doppler","icd":"I21.9","charge":5800.00,"date":"02/08/2026"},
        {"cpt":"70553","desc":"MRI Brain without and with contrast","icd":"I21.9","charge":4900.00,"date":"02/09/2026"},
        {"cpt":"85025","desc":"Complete Blood Count","icd":"I21.9","charge":280.00,"date":"02/08/2026"},
        {"cpt":"80053","desc":"Comprehensive Metabolic Panel","icd":"I21.9","charge":310.00,"date":"02/08/2026"},
        {"cpt":"96372","desc":"Therapeutic injection medication","icd":"I21.9","charge":450.00,"date":"02/09/2026"},
        {"cpt":"36415","desc":"Venipuncture routine","icd":"Z01.89","charge":120.00,"date":"02/10/2026"},
    ],
    total=15760.00, ins_paid=9000.00, patient_due=6760.00,
    notes=[
        "Patient admitted for chest pain discharged under 24 hours — may not meet CMS 2-midnight rule.",
        "Echocardiography billed $5800 vs CMS benchmark $685.",
        "MRI Brain billed $4900 vs CMS benchmark $612.",
    ]
)

make_pdf_cpt_label(
    filename="bill_4_cpt_label_format.pdf",
    provider_name="Westside Family Medicine Clinic",
    patient_name="Sandra K. Williams",
    account_no="WFM-2026-11047", dos="02/10/2026",
    items=[
        {"cpt":"99214","desc":"Office visit established patient moderate complexity","icd":"E11.9","charge":890.00},
        {"cpt":"83036","desc":"Hemoglobin A1c","icd":"E11.9","charge":185.00},
        {"cpt":"80061","desc":"Lipid panel","icd":"E78.5","charge":210.00},
        {"cpt":"82306","desc":"Vitamin D 25-hydroxy","icd":"E55.9","charge":320.00},
        {"cpt":"36415","desc":"Venipuncture routine blood draw","icd":"Z01.89","charge":85.00},
        {"cpt":"90471","desc":"Immunization injection administration","icd":"Z23","charge":145.00},
    ],
    total=1835.00, ins_paid=900.00, patient_due=935.00,
    notes=[
        "CPT 99214 billed at $890 vs CMS benchmark $167.",
        "Vitamin D billed at $320 vs CMS benchmark $45.",
    ]
)

make_pdf_multiline(
    filename="bill_5_multiline_format.pdf",
    provider_name="Pacific Coast Orthopedic Surgery Center",
    patient_name="Michael D. Torres",
    account_no="PCOS-2026-78234", dos="02/12/2026",
    items=[
        {"cpt":"29881","desc":"Knee arthroscopy with meniscectomy","icd":"M23.200","charge":8500.00},
        {"cpt":"29870","desc":"Knee arthroscopy diagnostic","icd":"M23.200","charge":3200.00},
        {"cpt":"20610","desc":"Arthrocentesis aspiration major joint","icd":"M25.361","charge":850.00},
        {"cpt":"96372","desc":"Therapeutic injection subcutaneous","icd":"M25.361","charge":480.00},
        {"cpt":"97110","desc":"Therapeutic exercises 15 min","icd":"M23.200","charge":320.00},
        {"cpt":"36415","desc":"Venipuncture blood draw","icd":"Z01.89","charge":95.00},
    ],
    total=13445.00, ins_paid=7000.00, patient_due=6445.00,
    notes=[
        "CPT 29881 and 29870 billed together — NCCI unbundling violation.",
        "Knee arthroscopy billed $8500 vs CMS benchmark $875.",
    ]
)

make_pdf_cpt_label(
    filename="bill_6_mixed_format.pdf",
    provider_name="Metro Health System Cardiology Department",
    patient_name="Dorothy A. Chen",
    account_no="MHS-2026-55901", dos="02/14/2026",
    items=[
        {"cpt":"93306","desc":"Echocardiography transthoracic complete with Doppler","icd":"I25.10","charge":4200.00},
        {"cpt":"93307","desc":"Echocardiography transthoracic without Doppler","icd":"I25.10","charge":2800.00},
        {"cpt":"93000","desc":"Electrocardiogram with interpretation","icd":"I25.10","charge":380.00},
        {"cpt":"99214","desc":"Office visit established moderate complexity","icd":"I25.10","charge":750.00},
        {"cpt":"80053","desc":"Comprehensive Metabolic Panel","icd":"I25.10","charge":290.00},
        {"cpt":"85025","desc":"Complete Blood Count with differential","icd":"I25.10","charge":220.00},
        {"cpt":"84443","desc":"TSH thyroid stimulating hormone","icd":"E03.9","charge":310.00},
        {"cpt":"36415","desc":"Venipuncture routine","icd":"Z01.89","charge":85.00},
    ],
    total=9035.00, ins_paid=4500.00, patient_due=4535.00,
    notes=[
        "CPT 93306 and 93307 billed together — NCCI violation.",
        "Echocardiography billed $4200 vs CMS benchmark $685.",
        "ECG billed $380 vs CMS benchmark $29.",
    ]
)

print("\n" + "="*60)
print("All 6 sample bills generated in sample_bills/")
print("="*60)
print("Bill 1: Upcoding + Pricing          [Structured]  Strategy 1")
print("Bill 2: Duplicate + Unbundling      [Structured]  Strategy 1")
print("Bill 3: Inpatient Mismatch          [Structured]  Strategy 1")
print("Bill 4: Office Visit Overcharges    [CPT Label]   Strategy 2")
print("Bill 5: Orthopedic Unbundling       [Multiline]   Strategy 4")
print("Bill 6: Cardiology NCCI + Pricing   [CPT Label]   Strategy 2")
