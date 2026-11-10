import os
import smtplib

def test_smtp_587():
    with open(".env") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

    user = os.environ.get("SENDER_EMAIL")
    pw = os.environ.get("GMAIL_APP_PASSWORD")

    print(f"Connecting to Gmail SMTP via Port 587 (TLS)...")
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(user, pw)
        print(">>> SUCCESS: Port 587 TLS Authenticated Perfectly! <<<")
        server.quit()
    except Exception as e:
        print(f"FAILED on 587: {e}")

if __name__ == "__main__":
    test_smtp_587()
