import json, os
os.makedirs("app/data", exist_ok=True)

cpt_benchmarks = {
    # ── E&M New Patient ──
    "99202": {"description":"Office visit new patient 15-29min","median":93.0,"range_low":70.0,"range_high":140.0,"category":"E&M","setting":"outpatient"},
    "99203": {"description":"Office visit new patient 30-44min","median":142.0,"range_low":100.0,"range_high":210.0,"category":"E&M","setting":"outpatient"},
    "99204": {"description":"Office visit new patient 45-59min","median":211.0,"range_low":150.0,"range_high":310.0,"category":"E&M","setting":"outpatient"},
    "99205": {"description":"Office visit new patient 60-74min","median":284.0,"range_low":200.0,"range_high":400.0,"category":"E&M","setting":"outpatient"},
    # ── E&M Established ──
    "99211": {"description":"Office visit established minimal","median":45.0,"range_low":25.0,"range_high":75.0,"category":"E&M","setting":"outpatient"},
    "99212": {"description":"Office visit established 10-19min","median":77.0,"range_low":50.0,"range_high":120.0,"category":"E&M","setting":"outpatient"},
    "99213": {"description":"Office visit established 20-29min","median":111.0,"range_low":80.0,"range_high":170.0,"category":"E&M","setting":"outpatient"},
    "99214": {"description":"Office visit established 30-39min","median":167.0,"range_low":120.0,"range_high":250.0,"category":"E&M","setting":"outpatient"},
    "99215": {"description":"Office visit established 40-54min","median":232.0,"range_low":170.0,"range_high":340.0,"category":"E&M","setting":"outpatient"},
    # ── Hospital Initial ──
    "99221": {"description":"Initial hospital care low complexity","median":118.0,"range_low":85.0,"range_high":175.0,"category":"Inpatient","setting":"inpatient"},
    "99222": {"description":"Initial hospital care moderate complexity","median":176.0,"range_low":125.0,"range_high":260.0,"category":"Inpatient","setting":"inpatient"},
    "99223": {"description":"Initial hospital care high complexity","median":263.0,"range_low":190.0,"range_high":390.0,"category":"Inpatient","setting":"inpatient"},
    # ── Hospital Subsequent ──
    "99231": {"description":"Subsequent hospital care low complexity","median":72.0,"range_low":50.0,"range_high":110.0,"category":"Inpatient","setting":"inpatient"},
    "99232": {"description":"Subsequent hospital care moderate complexity","median":113.0,"range_low":80.0,"range_high":170.0,"category":"Inpatient","setting":"inpatient"},
    "99233": {"description":"Subsequent hospital care high complexity","median":164.0,"range_low":115.0,"range_high":245.0,"category":"Inpatient","setting":"inpatient"},
    # ── Hospital Discharge ──
    "99238": {"description":"Hospital discharge 30min or less","median":145.0,"range_low":100.0,"range_high":220.0,"category":"Inpatient","setting":"inpatient"},
    "99239": {"description":"Hospital discharge more than 30min","median":209.0,"range_low":150.0,"range_high":310.0,"category":"Inpatient","setting":"inpatient"},
    # ── Emergency Department ──
    "99281": {"description":"ED visit self-limited minor","median":45.0,"range_low":30.0,"range_high":70.0,"category":"Emergency","setting":"outpatient"},
    "99282": {"description":"ED visit low complexity","median":86.0,"range_low":60.0,"range_high":130.0,"category":"Emergency","setting":"outpatient"},
    "99283": {"description":"ED visit moderate complexity","median":148.0,"range_low":105.0,"range_high":220.0,"category":"Emergency","setting":"outpatient"},
    "99284": {"description":"ED visit moderately high complexity","median":232.0,"range_low":165.0,"range_high":345.0,"category":"Emergency","setting":"outpatient"},
    "99285": {"description":"ED visit high complexity","median":319.0,"range_low":225.0,"range_high":475.0,"category":"Emergency","setting":"outpatient"},
    # ── Critical Care ──
    "99291": {"description":"Critical care first 30-74min","median":420.0,"range_low":295.0,"range_high":625.0,"category":"Critical","setting":"inpatient"},
    "99292": {"description":"Critical care each additional 30min","median":210.0,"range_low":148.0,"range_high":313.0,"category":"Critical","setting":"inpatient"},
    # ── Preventive ──
    "99385": {"description":"Preventive visit new patient 18-39yrs","median":213.0,"range_low":150.0,"range_high":317.0,"category":"Preventive","setting":"outpatient"},
    "99386": {"description":"Preventive visit new patient 40-64yrs","median":252.0,"range_low":178.0,"range_high":375.0,"category":"Preventive","setting":"outpatient"},
    "99395": {"description":"Preventive visit established 18-39yrs","median":184.0,"range_low":130.0,"range_high":274.0,"category":"Preventive","setting":"outpatient"},
    "99396": {"description":"Preventive visit established 40-64yrs","median":214.0,"range_low":150.0,"range_high":319.0,"category":"Preventive","setting":"outpatient"},
    # ── Telehealth ──
    "99441": {"description":"Telephone E&M 5-10min","median":50.0,"range_low":35.0,"range_high":75.0,"category":"Telehealth","setting":"outpatient"},
    "99442": {"description":"Telephone E&M 11-20min","median":90.0,"range_low":63.0,"range_high":134.0,"category":"Telehealth","setting":"outpatient"},
    "99443": {"description":"Telephone E&M 21-30min","median":130.0,"range_low":91.0,"range_high":193.0,"category":"Telehealth","setting":"outpatient"},
    # ── Radiology ──
    "70450": {"description":"CT head without contrast","median":225.0,"range_low":158.0,"range_high":335.0,"category":"Radiology","setting":"outpatient"},
    "70553": {"description":"MRI brain without and with contrast","median":612.0,"range_low":430.0,"range_high":910.0,"category":"Radiology","setting":"outpatient"},
    "70551": {"description":"MRI brain without contrast","median":491.0,"range_low":345.0,"range_high":730.0,"category":"Radiology","setting":"outpatient"},
    "71046": {"description":"Chest X-ray 2 views","median":56.0,"range_low":39.0,"range_high":83.0,"category":"Radiology","setting":"outpatient"},
    "71045": {"description":"Chest X-ray 1 view","median":40.0,"range_low":28.0,"range_high":59.0,"category":"Radiology","setting":"outpatient"},
    "71250": {"description":"CT thorax without contrast","median":310.0,"range_low":217.0,"range_high":461.0,"category":"Radiology","setting":"outpatient"},
    "71270": {"description":"CT thorax without and with contrast","median":445.0,"range_low":312.0,"range_high":662.0,"category":"Radiology","setting":"outpatient"},
    "72141": {"description":"MRI spine cervical without contrast","median":497.0,"range_low":348.0,"range_high":739.0,"category":"Radiology","setting":"outpatient"},
    "72148": {"description":"MRI spine lumbar without contrast","median":497.0,"range_low":348.0,"range_high":739.0,"category":"Radiology","setting":"outpatient"},
    "74177": {"description":"CT abdomen pelvis without contrast","median":360.0,"range_low":252.0,"range_high":535.0,"category":"Radiology","setting":"outpatient"},
    "74178": {"description":"CT abdomen pelvis with contrast","median":450.0,"range_low":315.0,"range_high":669.0,"category":"Radiology","setting":"outpatient"},
    "76700": {"description":"Ultrasound abdomen complete","median":225.0,"range_low":158.0,"range_high":335.0,"category":"Radiology","setting":"outpatient"},
    "77067": {"description":"Screening mammography bilateral","median":162.0,"range_low":114.0,"range_high":241.0,"category":"Radiology","setting":"outpatient"},
    "78816": {"description":"PET scan whole body","median":1650.0,"range_low":1155.0,"range_high":2453.0,"category":"Radiology","setting":"outpatient"},
    # ── Cardiology ──
    "93000": {"description":"ECG with interpretation","median":29.0,"range_low":20.0,"range_high":43.0,"category":"Cardiology","setting":"outpatient"},
    "93005": {"description":"ECG tracing only","median":16.0,"range_low":11.0,"range_high":24.0,"category":"Cardiology","setting":"outpatient"},
    "93010": {"description":"ECG interpretation only","median":14.0,"range_low":10.0,"range_high":21.0,"category":"Cardiology","setting":"outpatient"},
    "93306": {"description":"Echocardiography transthoracic with Doppler","median":685.0,"range_low":480.0,"range_high":1019.0,"category":"Cardiology","setting":"outpatient"},
    "93307": {"description":"Echocardiography transthoracic without Doppler","median":437.0,"range_low":306.0,"range_high":650.0,"category":"Cardiology","setting":"outpatient"},
    "93017": {"description":"Cardiovascular stress test tracing","median":100.0,"range_low":70.0,"range_high":149.0,"category":"Cardiology","setting":"outpatient"},
    "93452": {"description":"Left heart catheterization","median":1845.0,"range_low":1292.0,"range_high":2744.0,"category":"Cardiology","setting":"outpatient"},
    # ── Laboratory ──
    "36415": {"description":"Venipuncture routine blood draw","median":4.0,"range_low":3.0,"range_high":6.0,"category":"Lab","setting":"outpatient"},
    "80048": {"description":"Basic metabolic panel","median":14.0,"range_low":10.0,"range_high":21.0,"category":"Lab","setting":"outpatient"},
    "80053": {"description":"Comprehensive metabolic panel","median":15.0,"range_low":11.0,"range_high":22.0,"category":"Lab","setting":"outpatient"},
    "80061": {"description":"Lipid panel","median":22.0,"range_low":15.0,"range_high":33.0,"category":"Lab","setting":"outpatient"},
    "85025": {"description":"Complete blood count with differential","median":11.0,"range_low":8.0,"range_high":16.0,"category":"Lab","setting":"outpatient"},
    "85610": {"description":"Prothrombin time PT/INR","median":8.0,"range_low":6.0,"range_high":12.0,"category":"Lab","setting":"outpatient"},
    "83036": {"description":"Hemoglobin A1c","median":14.0,"range_low":10.0,"range_high":21.0,"category":"Lab","setting":"outpatient"},
    "84153": {"description":"PSA prostate specific antigen","median":27.0,"range_low":19.0,"range_high":40.0,"category":"Lab","setting":"outpatient"},
    "84443": {"description":"TSH thyroid stimulating hormone","median":27.0,"range_low":19.0,"range_high":40.0,"category":"Lab","setting":"outpatient"},
    "82306": {"description":"Vitamin D 25-hydroxy","median":45.0,"range_low":32.0,"range_high":67.0,"category":"Lab","setting":"outpatient"},
    "82607": {"description":"Vitamin B12","median":27.0,"range_low":19.0,"range_high":40.0,"category":"Lab","setting":"outpatient"},
    "87804": {"description":"Influenza rapid antigen test","median":19.0,"range_low":13.0,"range_high":28.0,"category":"Lab","setting":"outpatient"},
    "87880": {"description":"Strep A rapid test","median":19.0,"range_low":13.0,"range_high":28.0,"category":"Lab","setting":"outpatient"},
    "84550": {"description":"Uric acid blood","median":9.0,"range_low":6.0,"range_high":13.0,"category":"Lab","setting":"outpatient"},
    "82947": {"description":"Glucose quantitative","median":7.0,"range_low":5.0,"range_high":10.0,"category":"Lab","setting":"outpatient"},
    # ── GI ──
    "43239": {"description":"Upper GI endoscopy with biopsy","median":590.0,"range_low":413.0,"range_high":878.0,"category":"GI","setting":"outpatient"},
    "43235": {"description":"Upper GI endoscopy diagnostic","median":455.0,"range_low":319.0,"range_high":677.0,"category":"GI","setting":"outpatient"},
    "45378": {"description":"Colonoscopy diagnostic","median":325.0,"range_low":228.0,"range_high":483.0,"category":"GI","setting":"outpatient"},
    "45380": {"description":"Colonoscopy with biopsy","median":430.0,"range_low":301.0,"range_high":640.0,"category":"GI","setting":"outpatient"},
    "45385": {"description":"Colonoscopy with polyp removal snare","median":663.0,"range_low":464.0,"range_high":986.0,"category":"GI","setting":"outpatient"},
    # ── Surgery ──
    "27447": {"description":"Total knee arthroplasty","median":1802.0,"range_low":1261.0,"range_high":2681.0,"category":"Surgery","setting":"inpatient"},
    "27130": {"description":"Total hip arthroplasty","median":1947.0,"range_low":1363.0,"range_high":2896.0,"category":"Surgery","setting":"inpatient"},
    "29881": {"description":"Knee arthroscopy with meniscectomy","median":875.0,"range_low":613.0,"range_high":1301.0,"category":"Surgery","setting":"outpatient"},
    "47562": {"description":"Laparoscopic cholecystectomy","median":1155.0,"range_low":809.0,"range_high":1718.0,"category":"Surgery","setting":"inpatient"},
    "44970": {"description":"Laparoscopic appendectomy","median":890.0,"range_low":623.0,"range_high":1324.0,"category":"Surgery","setting":"inpatient"},
    "49505": {"description":"Inguinal hernia repair initial","median":875.0,"range_low":613.0,"range_high":1301.0,"category":"Surgery","setting":"outpatient"},
    # ── Injections ──
    "96372": {"description":"Therapeutic injection subcutaneous IM","median":25.0,"range_low":18.0,"range_high":37.0,"category":"Injection","setting":"outpatient"},
    "96374": {"description":"IV push single drug","median":87.0,"range_low":61.0,"range_high":129.0,"category":"Injection","setting":"outpatient"},
    "96365": {"description":"IV infusion initial up to 1 hour","median":130.0,"range_low":91.0,"range_high":193.0,"category":"Injection","setting":"outpatient"},
    "96366": {"description":"IV infusion each additional hour","median":34.0,"range_low":24.0,"range_high":51.0,"category":"Injection","setting":"outpatient"},
    "20610": {"description":"Arthrocentesis major joint","median":100.0,"range_low":70.0,"range_high":149.0,"category":"Injection","setting":"outpatient"},
    "90471": {"description":"Immunization injection single","median":25.0,"range_low":18.0,"range_high":37.0,"category":"Injection","setting":"outpatient"},
    # ── Mental Health ──
    "90832": {"description":"Psychotherapy 16-37min","median":90.0,"range_low":63.0,"range_high":134.0,"category":"MentalHealth","setting":"outpatient"},
    "90834": {"description":"Psychotherapy 38-52min","median":130.0,"range_low":91.0,"range_high":193.0,"category":"MentalHealth","setting":"outpatient"},
    "90837": {"description":"Psychotherapy 53+min","median":175.0,"range_low":123.0,"range_high":260.0,"category":"MentalHealth","setting":"outpatient"},
    "90791": {"description":"Psychiatric diagnostic evaluation","median":260.0,"range_low":182.0,"range_high":387.0,"category":"MentalHealth","setting":"outpatient"},
    # ── Physical Therapy ──
    "97110": {"description":"Therapeutic exercises","median":55.0,"range_low":39.0,"range_high":82.0,"category":"PT","setting":"outpatient"},
    "97140": {"description":"Manual therapy techniques","median":55.0,"range_low":39.0,"range_high":82.0,"category":"PT","setting":"outpatient"},
    "97530": {"description":"Therapeutic activities","median":55.0,"range_low":39.0,"range_high":82.0,"category":"PT","setting":"outpatient"},
    "97010": {"description":"Hot cold pack application","median":11.0,"range_low":8.0,"range_high":16.0,"category":"PT","setting":"outpatient"},
    "97014": {"description":"Electrical stimulation unattended","median":14.0,"range_low":10.0,"range_high":21.0,"category":"PT","setting":"outpatient"},
    # ── OB/GYN ──
    "59400": {"description":"Routine obstetric care vaginal delivery","median":2340.0,"range_low":1638.0,"range_high":3480.0,"category":"OBGYN","setting":"inpatient"},
    "59510": {"description":"Routine obstetric care cesarean delivery","median":2875.0,"range_low":2013.0,"range_high":4276.0,"category":"OBGYN","setting":"inpatient"},
    "57454": {"description":"Colposcopy with biopsy","median":310.0,"range_low":217.0,"range_high":461.0,"category":"OBGYN","setting":"outpatient"},
}

ncci_edits = {
    "45378": ["45380","45381","45382","45383","45384","45385","45386","45387"],
    "45380": ["45378","45381","45384","45385"],
    "45385": ["45378","45380","45381","45384"],
    "43235": ["43239","43241","43243","43244","43245","43246","43247","43248","43249"],
    "43239": ["43235","43241","43246"],
    "99213": ["99214","99215","99212","99211"],
    "99214": ["99213","99215","99212","99211"],
    "99215": ["99213","99214","99212","99211"],
    "99202": ["99203","99204","99205"],
    "99203": ["99202","99204","99205"],
    "99204": ["99202","99203","99205"],
    "93000": ["93005","93010"],
    "93005": ["93000"],
    "93010": ["93000"],
    "93306": ["93307","93308"],
    "93307": ["93306","93308"],
    "80053": ["80048","82310","82374","82435","82565","82947","84132","84295","84520"],
    "80048": ["82310","82374","82435","82565","82947","84132","84295"],
    "85025": ["85027","85004","85032"],
    "47562": ["47600","47605"],
    "44970": ["44950","44960"],
    "29881": ["29870","29871","29874","29875","29876"],
    "96372": ["96374","96375","96376"],
    "96374": ["96372","96375","96376"],
}

lcd_mappings = {
    "70553": {"description":"MRI Brain requires neurological indication","allowed_icd_prefixes":["G","C71","C72","D33","I","R51","S09","Q","F","R41","R42"],"denial_risk":"high"},
    "70551": {"description":"MRI Brain without contrast neurological indication","allowed_icd_prefixes":["G","C","I","R51","S09","Q","F"],"denial_risk":"high"},
    "93306": {"description":"Echocardiography cardiac indication required","allowed_icd_prefixes":["I","R00","R01","R07","Z87.3","Q20","Q21","Q22","Q23","Q24"],"denial_risk":"high"},
    "93452": {"description":"Left heart cath significant cardiac indication","allowed_icd_prefixes":["I20","I21","I22","I23","I24","I25","I35","I36"],"denial_risk":"high"},
    "78816": {"description":"PET Scan oncological or neurological indication","allowed_icd_prefixes":["C","D","G30","G31","G35","F02","F03"],"denial_risk":"high"},
    "77067": {"description":"Screening mammography age 40+ or high risk","allowed_icd_prefixes":["Z12.3","Z12.31","C50","D05","Z80.3","N63"],"denial_risk":"medium"},
    "45378": {"description":"Colonoscopy GI indication or age 45+ screening","allowed_icd_prefixes":["K","C18","C19","C20","D12","Z12.1","Z80.0","R19"],"denial_risk":"medium"},
    "72148": {"description":"MRI Lumbar Spine back pain with neurological symptoms","allowed_icd_prefixes":["M47","M48","M50","M51","M54","G35","G54","S32","C"],"denial_risk":"medium"},
    "99291": {"description":"Critical care life threatening condition required","allowed_icd_prefixes":["I21","I46","J96","J80","N17","G93","R57","T"],"denial_risk":"high"},
}

with open("app/data/cpt_benchmarks.json","w") as f: json.dump(cpt_benchmarks, f, indent=2)
with open("app/data/ncci_edits.json","w") as f: json.dump(ncci_edits, f, indent=2)
with open("app/data/lcd_mappings.json","w") as f: json.dump(lcd_mappings, f, indent=2)
print(f"Done! {len(cpt_benchmarks)} CPT codes, {len(ncci_edits)} NCCI pairs, {len(lcd_mappings)} LCD rules")
