# backend/tangedco_complaint.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os, textwrap, datetime
from io import BytesIO

styles = getSampleStyleSheet()
normal = styles["Normal"]
bold = ParagraphStyle("Bold", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10)
small = ParagraphStyle("small", parent=styles["Normal"], fontSize=9)

def _wrap(text, width=90):
    return "<br/>".join(textwrap.wrap(text, width))

def generate_tangedco_complaint(parsed: dict, anomaly_reason: str, extra_notes: str, attachments: list, outpath: str):
    """
    Generate a CGRF-style complaint PDF (Annexure-I like) for TANGEDCO/TNEB.
    - parsed: dict with keys consumer_no, prev_read, cur_read, units, amount, raw_text
    - anomaly_reason: short explanation string
    - extra_notes: free-text notes (user-supplied)
    - attachments: list of (filename, bytes) or list of file paths to include as index entries
    - outpath: path to save the generated PDF
    Returns saved path.
    """

    # Prepare document
    os.makedirs(os.path.dirname(outpath) or ".", exist_ok=True)
    doc = SimpleDocTemplate(outpath, pagesize=A4, topMargin=18*mm, leftMargin=15*mm, rightMargin=15*mm, bottomMargin=18*mm)
    flow = []

    # Header: Title + reference
    title_style = ParagraphStyle("title", parent=styles["Heading1"], fontSize=14, alignment=1, leading=16)
    flow.append(Paragraph("ANNEXURE - I", title_style))
    flow.append(Paragraph("<b>CONSUMER REDRESSAL FORUM - COMPLAINT FORMAT</b>", ParagraphStyle("sub", parent=styles["Heading2"], alignment=1, fontSize=11)))
    flow.append(Spacer(1,6))

    # Date
    today = datetime.date.today().strftime("%d-%b-%Y")
    flow.append(Paragraph(f"<b>Date:</b> {today}", small))
    flow.append(Spacer(1,4))

    # Primary complainant info table
    name = parsed.get("consumer_name", "")
    consumer_no = parsed.get("consumer_no", "") or ""
    address = parsed.get("address", "") or ""
    phone = parsed.get("phone", "") or ""
    email = parsed.get("email", "") or ""
    billing_period = parsed.get("billing_period", "") or ""
    prev_read = parsed.get("prev_read", "") or ""
    cur_read = parsed.get("cur_read", "") or ""
    units = parsed.get("units", "") or ""
    amount = parsed.get("amount", "") or ""

    data_info = [
        ["Complainant Name", f"{name or '—'}", "Consumer No.", f"{consumer_no or '—'}"],
        ["Address", f"{address or '—'}", "Phone / Email", f"{phone or '—'} / {email or '—'}"],
        ["Billing Period", f"{billing_period or '—'}", "Bill Amount (Rs)", f"{amount or '—'}"],
        ["Previous Reading", f"{prev_read or '—'}", "Present Reading", f"{cur_read or '—'}"],
        ["Units (kWh)", f"{units or '—'}", "", ""]
    ]
    t = Table(data_info, colWidths=[45*mm, 65*mm, 40*mm, 40*mm])
    t.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1),'Helvetica'),
        ('FONTSIZE',(0,0),(-1,-1),9),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('INNERGRID',(0,0),(-1,-1),0.25,colors.grey),
        ('BOX',(0,0),(-1,-1),0.5,colors.black),
        ('BACKGROUND',(0,0),(1,0),colors.whitesmoke)
    ]))
    flow.append(t)
    flow.append(Spacer(1,8))

    # Complaint category checklist (common categories)
    flow.append(Paragraph("<b>Category of Complaint (tick relevant)</b>", small))
    cats = [
        "Billing Problems (excess bill / wrong bill / cumulative billing)",
        "Meter related problems (faulty meter / zero reading / irregular reading)",
        "Interruption / supply quality (frequent trippings / low voltage)",
        "Service connection issues (new connection / enhancement / shifting)",
        "Deficiency of service / discourtesy of staff / others"
    ]
    chk_lines = []
    for c in cats:
        chk_lines.append(f"☐ {c}")
    flow.append(Paragraph("<br/>".join(chk_lines), small))
    flow.append(Spacer(1,8))

    # Respondent (if known)
    flow.append(Paragraph("<b>Respondent (Licensee / Office / Official)</b>", small))
    flow.append(Paragraph("Name / Designation (if known): _________________________", small))
    flow.append(Paragraph("Office Address: _________________________", small))
    flow.append(Spacer(1,8))

    # Description of complaint
    flow.append(Paragraph("<b>Description of Complaint (brief & precise)</b>", small))
    # Compose a precise description using parsed fields and anomaly
    auto_description = f"The complainant received a bill for {billing_period or 'N/A'} showing {units or 'N/A'} kWh amounting to Rs. {amount or 'N/A'}. Preliminary automated analysis reports: {anomaly_reason}. Request immediate re-check of meter readings and corrected billing / provisional billing as applicable. "
    if extra_notes:
        auto_description += "Additional notes: " + extra_notes
    flow.append(Paragraph(_wrap(auto_description, 120), small))
    flow.append(Spacer(1,10))

    # Attachments index
    flow.append(Paragraph("<b>List of Enclosures / Attachments (mark and number pages)</b>", small))
    # attachments param may be list of tuples (name, path) or list of filenames
    attach_lines = []
    if attachments:
        for i, a in enumerate(attachments, start=1):
            if isinstance(a, (list, tuple)):
                name = a[0]
            else:
                name = os.path.basename(a)
            attach_lines.append(f"{i}. {name}")
    else:
        attach_lines.append("1. Copy of Electricity Bill (scanned/photo)")
    flow.append(Paragraph("<br/>".join(attach_lines), small))
    flow.append(Spacer(1,12))

    # Relief sought
    flow.append(Paragraph("<b>Relief / Reliefs sought</b>", small))
    relief_text = "1. Re-check the meter reading and inspect the meter for errors.\n2. Issue corrected bill / provisional billing as applicable.\n3. Refund/adjustment if overcharging is established."
    flow.append(Paragraph(_wrap(relief_text, 120), small))
    flow.append(Spacer(1,18))

    # Declaration & signature block
    flow.append(Paragraph("I hereby declare that the information given above is true to the best of my knowledge and belief.", small))
    flow.append(Spacer(1,24))
    # signature table
    sign_table = Table([
        ["Date:", datetime.date.today().strftime("%d-%b-%Y"), "", "Signature of Complainant:"],
        ["Place:", "", "", "    ______________________    "]
    ], colWidths=[20*mm, 60*mm, 30*mm, 60*mm])
    sign_table.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Helvetica'), ('FONTSIZE',(0,0),(-1,-1),10)]))
    flow.append(sign_table)
    flow.append(Spacer(1,6))

    # Footer: instruction to submit to CGRF / contact
    footer = ("Note: Please submit this form with copies of relevant documents to the Chairperson, "
              "Consumer Grievance Redressal Forum (CGRF), concerned EDC office of TANGEDCO. "
              "You may also register online at the TANGEDCO CGRF portal and upload this form and attachments.")
    flow.append(Paragraph(_wrap(footer,120), ParagraphStyle("foot", parent=styles["Normal"], fontSize=8)))
    flow.append(Spacer(1,6))

    doc.build(flow)
    return outpath
