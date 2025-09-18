import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from io import BytesIO
from dotenv import load_dotenv
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from io import BytesIO
import json
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
load_dotenv()

def build_offer_letter_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=LETTER,
        rightMargin=50, leftMargin=50,
        topMargin=80, bottomMargin=50
    )
    styles = getSampleStyleSheet()
    pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))

    # Custom styles
    header_style = ParagraphStyle(
        "Header",
        parent=styles["Heading1"],
        fontName="DejaVuSans",
        fontSize=18,
        textColor=colors.HexColor("#0B5394"),
        alignment=1,  # center
        spaceAfter=20
    )
    normal = styles["Normal"]

    elements = []

    # Top header "Business Offer Letter"
    elements.append(Paragraph("Business Offer Letter", header_style))
    elements.append(Spacer(1, 12))

    # Candidate & HR details in table
    info_table = [
        ["Date:", data.get("date", "________")],
        ["Candidate Name:", data.get("fullname", "")],
        ["Role:", data.get("designation", "")],
        ["Company:", data.get("company_name", "")],
        ["Offer Amount:", f"{data.get('currency','')} {data.get('salary','')}"],
        ["Location:", data.get("company_location", "")],
        ["Work Mode:", data.get("work_mode", "")],
        ["HR Contact:", f"{data.get('hiring_hr_name','')} ({data.get('hr_role','')}) - {data.get('hiring_hr_email','')}"]
    ]
    table = Table(info_table, hAlign="LEFT", colWidths=[120, 350])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "DejaVuSans"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Body text
    body_text = f"""
    Dear {data.get("fullname","")},<br/><br/>
    Thank you for choosing <b>{data.get("company_name","")}</b> for your career journey. 
    We are pleased to offer you the role of <b>{data.get("designation","")}</b> with a compensation of 
    <b>{data.get("currency","")} {data.get("salary","")}</b>.<br/><br/>
    Attached is your official offer letter. Please review the details carefully. If acceptable, 
    kindly confirm by clicking the "I Accept" button in your email.<br/><br/>
    For any clarifications, feel free to reach out to your HR representative listed above.<br/><br/>
    Sincerely,<br/><br/>
    {data.get("hiring_hr_name","")}<br/>
    {data.get("hr_role","")}<br/>
    {data.get("company_name","")}
    """
    elements.append(Paragraph(body_text, normal))

    # Footer line
    footer = Paragraph(
        "<para align=center><font size=8 color=grey>This is a system generated document from "
        f"{data.get('company_name','')} HR</font></para>",
        styles["Normal"]
    )
    elements.append(Spacer(1, 50))
    elements.append(footer)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def send_offer_letter_html(data):

    currency_symbols = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "AUD": "A$",
    "CAD": "C$",
    "SGD": "S$",
    "AED": "د.إ"
    }

    # Parse hiring_info JSON
    hiring_info_str = data.get("hiring_info")
    if hiring_info_str:
        try:
            hiring_info = json.loads(hiring_info_str)
            data.update(hiring_info)  # flatten into main dict
        except json.JSONDecodeError:
            print("Invalid hiring_info JSON")
    symbol = currency_symbols.get(hiring_info.get("currency"), data.get("currency"))
    print(data)
    print("-------------------------")
    print(hiring_info)
    data["currency"] = symbol
    gmail_user = os.getenv("GMAIL_USER")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
    to_email = data.get("email")

    subject = f"Offer Letter – {data.get('company_name','')}"

    # Modern HTML email body with I Accept button
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
        <div style="max-width:600px; margin:auto; padding:20px; border:1px solid #ddd; border-radius:10px;">
            <h2 style="color:#4CAF50;">Congratulations {data.get('fullname','')}</h2>
            <p>We are excited to offer you the role of 
               <b>{data.get('designation','')}</b> at <b>{data.get('company_name','our company')}</b>.</p>
            <p>Your offered compensation is 
               <b style="color:#2c3e50;">{data.get('currency','')} {data.get('salary','')}</b>.</p>
            <p>Location: {data.get('company_location','')} | Work Mode: {data.get('work_mode','')}</p>
            <p>Please find your official offer letter attached to this email.</p>
            <p style="margin:20px 0;">
                <a href="http://127.0.0.1:8000/accept_offer?candidateId={data.get('candidateId')}&hiring_stage=offer_letter_accepted" 
                   style="background:#4CAF50;color:white;padding:10px 18px;
                   text-decoration:none;border-radius:6px;">
                   I Accept
                </a>
            </p>
            <p style="color:#888; font-size:13px;">This is an automated notification from {data.get('company_name','')} HR.</p>
        </div>
    </body>
    </html>
    """

    # Generate PDF offer letter in memory
    pdf_buffer = build_offer_letter_pdf(data)

    # Build the email with HTML body
    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    # Attach PDF
    part = MIMEBase("application", "octet-stream")
    part.set_payload(pdf_buffer.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment; filename=Offer_Letter.pdf")
    msg.attach(part)

    # Send email
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_user, gmail_app_password)
        server.send_message(msg)
    print("HTML offer letter email sent successfully!")


if __name__ == "__main__":
    sample_data = {
            "onboardId": "4",
            "candidateId": "4",
            "fullname": "Sayak Samaddar",
            "email": "sayaksamaddar@virtualemployee.com",
            "phone": "7755896226",
            "company_id": "2",
            "hiring_info": "{\"currency\": \"INR\",\"salary\":\"300000\",\"designation\":\"Backend Developer\",\"company_location\": \"Chennai\",\"work_mode\": \"Remote\"}",
            "hiring_hr_name": "Trisha Singh",
            "hiring_hr_email": "trishasingh@cerebree.com",
            "hiringHrId": "1"
        }
    send_offer_letter_html(sample_data)