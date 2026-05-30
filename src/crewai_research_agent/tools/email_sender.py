import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_summary_email(subject: str, body: str) -> str:
    msg = MIMEMultipart()
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["EMAIL_TO"]
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.send_message(msg)
    return f"Email sent to {os.environ['EMAIL_TO']}"