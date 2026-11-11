import os
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request

from safety_guard import SafetyGuard
from verifier import EmailVerifier
from researcher import WebsiteResearcher
from copywriter import AICopywriter
from sender import GmailSender
from sequence_manager import SequenceFollowUpManager

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

def auto_discover_company(company_name: str):
    """
    Given ONLY a company name (e.g. 'Apex Roofing Austin' or 'Flight Digital Agency'):
    1. Finds their real website URL automatically.
    2. Scrapes the website to find their public contact/decision-maker email.
    3. Guesses a clean first name.
    """
    clean_name = company_name.strip()
    query = f'"{clean_name}" official website'
    search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
    website = ""
    discovered_email = ""
    first_name = "there"

    try:
        r = requests.get(search_url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            for link in soup.find_all("a", class_="result__url"):
                href = link.get("href", "")
                if "//duckduckgo.com/l/?uddg=" in href:
                    real_url = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                    domain = urllib.parse.urlparse(real_url).netloc.lower()
                    if not any(bad in domain for bad in ["facebook", "linkedin", "yelp", "yellowpages", "instagram", "wikipedia"]):
                        website = f"https://{domain}"
                        break
    except Exception:
        pass

    if not website:
        # Fallback domain guess
        slug = re.sub(r'[^a-zA-Z0-9]', '', clean_name.lower().split()[0])
        website = f"https://{slug}.com"

    # Scrape website for contact email
    pages = [website, f"{website}/contact", f"{website}/about"]
    found_emails = set()
    for p in pages:
        try:
            res = requests.get(p, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                emails = EMAIL_REGEX.findall(res.text)
                for e in emails:
                    cl = e.lower().strip(".")
                    if not any(cl.endswith(ext) for ext in [".png", ".jpg", ".webp", ".svg", ".js", ".css"]):
                        found_emails.add(cl)
        except Exception:
            continue

    direct = [e for e in found_emails if not any(e.startswith(r) for r in ["info@", "support@", "admin@", "sales@", "contact@"])]
    discovered_email = direct[0] if direct else (list(found_emails)[0] if found_emails else f"contact@{urllib.parse.urlparse(website).netloc.replace('www.', '')}")

    if "." in discovered_email.split("@")[0]:
        first_name = discovered_email.split("@")[0].split(".")[0].capitalize()
    else:
        first_name = "Team"

    return {
        "website": website,
        "email": discovered_email,
        "first_name": first_name
    }

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Smart Outreach - Adegbite David</title>
  <style>
    * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: #0f172a; color: #f8fafc; margin: 0; padding: 16px; }
    .container { max-width: 550px; margin: auto; }
    .card { background: #1e293b; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); margin-bottom: 20px; }
    h2 { color: #38bdf8; margin-top: 0; font-size: 22px; }
    p.subtitle { color: #94a3b8; font-size: 14px; margin-top: -6px; }
    label { font-size: 13px; color: #cbd5e1; font-weight: 600; margin-top: 12px; display: block; }
    input, textarea { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; font-size: 15px; margin-top: 6px; }
    button { width: 100%; padding: 14px; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; margin-top: 16px; }
    .btn-search { background: #0284c7; color: white; }
    .btn-send { background: #16a34a; color: white; }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-valid { background: #166534; color: #bbf7d0; }
    .badge-invalid { background: #991b1b; color: #fecaca; }
    .auto-badge { background: #1e3a8a; color: #93c5fd; padding: 3px 8px; border-radius: 4px; font-size: 11px; margin-left: 6px; }
    .alert-success { background: #064e3b; border: 1px solid #059669; color: #a7f3d0; padding: 12px; border-radius: 8px; margin-bottom: 16px; }
    .alert-error { background: #7f1d1d; border: 1px solid #dc2626; color: #fecaca; padding: 12px; border-radius: 8px; margin-bottom: 16px; }
  </style>
</head>
<body>
  <div class="container">
    {% if send_message %}
      <div class="{% if send_success %}alert-success{% else %}alert-error{% endif %}">
        {{ send_message }}
      </div>
    {% endif %}

    <div class="card">
      <h2>⚡ 1-Click Smart Outreach</h2>
      <p class="subtitle">Just enter the company name. The app finds the website, email, and drafts the pitch automatically.</p>

      <form method="POST" action="/search">
        <label>Company / Business Name (That's all you need!):</label>
        <input type="text" name="biz" placeholder="e.g. Apex Roofing Austin, Flight Digital Agency" required value="{{ biz or '' }}">

        <button type="submit" class="btn-search">🔎 Auto-Find & Generate Outreach</button>
      </form>
    </div>

    {% if draft %}
    <div class="card">
      <h3>🎯 Discovered Info & Draft</h3>
      
      <form method="POST" action="/send">
        <label>Company Name:</label>
        <input type="text" name="biz" value="{{ biz }}" readonly>

        <label>Discovered Website: <span class="auto-badge">Auto-Found</span></label>
        <input type="url" name="web" value="{{ web }}" required>

        <label>Target Email: <span class="auto-badge">Auto-Found</span></label>
        <input type="email" name="to_email" value="{{ email }}" required>

        <p style="margin: 8px 0;">
          <strong>Reoon Status:</strong> 
          <span class="badge {% if is_safe %}badge-valid{% else %}badge-invalid{% endif %}">{{ v_status }}</span>
        </p>

        <label>Subject Line:</label>
        <input type="text" name="subject" value="{{ draft.subject }}" required>

        <label>Personalized Pitch (&lt;100 Words):</label>
        <textarea name="body" rows="8" required>{{ draft.body }}</textarea>

        <button type="submit" class="btn-send">✉️ Approve & Send Live Email</button>
      </form>
    </div>
    {% endif %}
  </div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/search", methods=["POST"])
def search():
    biz = request.form.get("biz", "").strip()
    
    # 1. AUTO-FIND WEBSITE & EMAIL FROM JUST THE NAME
    discovered = auto_discover_company(biz)
    web = discovered["website"]
    email = discovered["email"]
    name = discovered["first_name"]

    # 2. VERIFY EMAIL
    verifier = EmailVerifier(api_key=os.getenv("REOON_API_KEY", ""))
    v_res = verifier.verify(email)

    # 3. RESEARCH & DRAFT WITH GEMINI
    researcher = WebsiteResearcher(firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY", ""))
    site_data = researcher.research(web)

    copywriter = AICopywriter(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        sender_name=os.getenv("SENDER_NAME", "Adegbite David")
    )
    draft = copywriter.generate_draft(biz, name, site_data.get("text", ""))

    return render_template_string(
        HTML_TEMPLATE,
        biz=biz,
        web=web,
        email=email,
        v_status=v_res.get("status", "VALID"),
        is_safe=v_res.get("is_safe_to_send", True),
        draft=draft
    )

@app.route("/send", methods=["POST"])
def send_email_action():
    to_email = request.form.get("to_email", "").strip()
    subject = request.form.get("subject", "").strip()
    body = request.form.get("body", "").strip()

    sender_email = os.getenv("SENDER_EMAIL", "adegbiteishola001@gmail.com")
    app_password = os.getenv("GMAIL_APP_PASSWORD", "")
    sender_name = os.getenv("SENDER_NAME", "Adegbite David")
    dry_run = os.getenv("DRY_RUN", "False").lower() in ("true", "1")

    guard = SafetyGuard(sender_address=os.getenv("SENDER_ADDRESS", "Lagos, Nigeria"))
    full_body = guard.append_can_spam_footer(body)

    sender = GmailSender(sender_email, app_password, sender_name, dry_run=dry_run)
    res = sender.send_email(to_email, subject, full_body)

    msg = res.get("message") or res.get("error") or "Email sent successfully!"
    success = res.get("success", False)

    return render_template_string(HTML_TEMPLATE, send_message=msg, send_success=success)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
