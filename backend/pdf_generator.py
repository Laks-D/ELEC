# backend/pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

def generate_complaint_pdf(parsed, anomaly_reason, outpath):
    """
    parsed: dict from ocr_parser.parse_bill_image
    anomaly_reason: string
    outpath: full path to save PDF
    """
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    c = canvas.Canvas(outpath, pagesize=A4)
    c.setFont("Helvetica-Bold",14)
    c.drawString(40,800,"WhatAmp - Pre-filled Complaint (Tamil Nadu)")
    c.setFont("Helvetica",11)
    y = 760

    # simpler loop
    c.drawString(40,y, f"Consumer No: {parsed.get('consumer_no') or 'N/A'}"); y -= 18
    c.drawString(40,y, f"Previous Reading: {parsed.get('prev_read') or 'N/A'}"); y -= 18
    c.drawString(40,y, f"Present Reading: {parsed.get('cur_read') or 'N/A'}"); y -= 18
    c.drawString(40,y, f"Units (kWh): {parsed.get('units') or 'N/A'}"); y -= 18
    c.drawString(40,y, f"Amount (Rs): {parsed.get('amount') or 'N/A'}"); y -= 18
    y -= 6
    c.drawString(40,y, "Detected Anomaly:")
    y -= 16
    c.drawString(60,y, f"{anomaly_reason}")
    y -= 36
    c.drawString(40,y, "Request: Please re-check my meter reading and issue corrected bill/ provisional billing as applicable.")
    c.save()
    return outpath
