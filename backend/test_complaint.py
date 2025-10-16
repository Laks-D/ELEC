# backend/test_complaint.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.tangedco_complaint import generate_tangedco_complaint
from tangedco_complaint import generate_tangedco_complaint
parsed = {
    "consumer_name": "R. Kumar",
    "consumer_no": "12345678901",
    "address": "No 12, Anna St., Chennai - 600001",
    "phone": "99400XXXXX",
    "email": "test@example.com",
    "billing_period": "Aug-Sep 2025",
    "prev_read": "12345",
    "cur_read": "12965",
    "units": "620",
    "amount": "4310"
}
anomaly = "Spike detected — possible cumulative billing"
extra = "User reports sudden spike after no change in usage patterns."
attachments = ["bill_photo.png", "previous_bill.pdf"]
out = generate_tangedco_complaint(parsed, anomaly, extra, attachments, "data/outputs/tangedco_complaint_demo.pdf")
print("Saved:", out)
