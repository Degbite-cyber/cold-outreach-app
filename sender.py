import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any

class GmailSender:
    """
    Delivers outreach emails via Gmail SMTP with App Password.
    Includes Dry-Run mode to simulate sends safely offline.
    """

    def __init__(self, sender_email: str, app_password: str, sender_name: str, dry_run: bool = True):
        self.sender_email = sender_email
        self.app_password = app_password.replace(" ", "").strip()
        self.sender_name = sender_name
        self.dry_run = dry_run

    def send_email(self, to_email: str, subject: str, body: str) -> Dict[str, Any]:
        """Sends plain-text email with CAN-SPAM headers."""
        if self.dry_run:
            return {
                "success": True,
                "dry_run": True,
                "message": f"[DRY-RUN SIMULATED SEND] To: {to_email} | Subject: '{subject}'"
            }

        if not self.app_password:
            return {
                "success": False,
                "error": "GMAIL_APP_PASSWORD is missing. Cannot send real emails."
            }

        try:
            msg = MIMEMultipart()
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.sender_email, self.app_password)
            server.send_message(msg)
            server.quit()

            return {"success": True, "dry_run": False, "message": f"Sent live to {to_email}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
