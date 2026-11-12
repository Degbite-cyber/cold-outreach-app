import os
import csv
from flask import Flask, render_template_string, request

from safety_guard import SafetyGuard
from verifier import EmailVerifier
from researcher import WebsiteResearcher
from copywriter import AICopywriter
from sender import GmailSender
from scheduler import TimezoneScheduler

app = Flask(__name__)

def load_leads():
    leads = []
    csv_path = "sample_leads.csv"
    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8") as f:
            leads = list(csv.DictReader(f))
    return leads

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>B2B Apollo Campaign Manager - Adegbite David</title>
  <style>
    * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: #0f172a; color: #f8fafc; margin: 0; padding: 16px; }
    .container { max-width: 720px; margin: auto; }
    .card { background: #1e293b; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); margin-bottom: 20px; }
    h2 { color: #38bdf8; margin-top: 0; font-size: 22px; }
    p.subtitle { color: #94a3b8; font-size: 14px; margin-top: -6px; }
    .lead-box { background: #0f172a; padding: 16px; border-radius: 8px; border-left: 4px solid #38bdf8; margin-top: 14px; }
    button { padding: 10px 16px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 14px; margin-top: 8px; }
    .btn-draft { background: #0284c7; color: white; }
    .btn-send { background: #16a34a; color: white; }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }
    .badge-valid { background: #166534; color: #bbf7d0; }
    .badge-invalid { background: #991b1b; color: #fecaca; }
    textarea { width: 100%; padding: 10px; border-radius: 6px; border: 1px solid #334155; background: #020617; color: #f1f5f9; font-family: inherit; font-size: 13px; line-height: 1.5; margin-top: 6px; }
    input[type="text"] { width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #334155; background: #020617; color: white; font-size: 13px; margin-top: 4px; }
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
      <h2>🎯 Active Campaign: Verified Decision-Makers ({{ leads|length }})</h2>
      <p class="subtitle">Direct owners and founders from your Apollo list. Tap below to let Gemini write their pitch & send!</p>
    </div>

    {% for lead in leads %}
      <div class="card" style="margin-bottom: 16px;">
        <h3 style="margin: 0; color: #38bdf8;">{{ lead.business_name }}</h3>
        <p style="margin: 4px 0; font-size: 14px;">
          Owner/CEO: <strong>{{ lead.first_name }}</strong> ({{ lead.title }}) | 
          Email: <span style="color: #38bdf8;">{{ lead.email }}</span>
        </p>
        <p style="margin: 4px 0; font-size: 13px; color: #94a3b8;">
          Website: <a href="{{ lead.website }}" target="_blank" style="color: #94a3b8;">{{ lead.website }}</a> | Timezone: {{ lead.timezone }}
        </p>

        {% if lead.draft %}
          <div class="lead-box">
            <form method="POST" action="/send_email">
              <input type="hidden" name="to_email" value="{{ lead.email }}">
              <label style="font-size: 12px; color: #cbd5e1; font-weight: 600;">Subject Line:</label>
              <input type="text" name="subject" value="{{ lead.draft.subject }}" required>

              <label style="font-size: 12px; color: #cbd5e1; font-weight: 600; margin-top: 8px; display: block;">Personalized Pitch (&lt;100 words, no em dashes):</label>
              <textarea name="body" rows="7" required>{{ lead.draft.body }}</textarea>

              <button type="submit" class="btn-send">✉️ Send Live to {{ lead.first_name }} via Gmail</button>
            </form>
          </div>
        {% else %}
          <form method="POST" action="/generate_pitch">
            <input type="hidden" name="biz" value="{{ lead.business_name }}">
            <input type="hidden" name="name" value="{{ lead.first_name }}">
            <input type="hidden" name="email" value="{{ lead.email }}">
            <input type="hidden" name="website" value="{{ lead.website }}">
            <button type="submit" class="btn-draft">⚡ Generate AI Pitch for {{ lead.first_name }}</button>
          </form>
        {% endif %}
      </div>
    {% endfor %}
  </div>
</body>
</html>
"""

# In-memory storage for generated drafts
DRAFTS_CACHE = {}

@app.route("/")
def home():
    leads = load_leads()
    for l in leads:
        em = l.get("email")
        if em in DRAFTS_CACHE:
            l["draft"] = DRAFTS_CACHE[em]
    return render_template_string(HTML_TEMPLATE, leads=leads)

@app.route("/generate_pitch", methods=["POST"])
def generate_pitch():
    biz = request.form.get("biz", "")
    name = request.form.get("name", "")
    email = request.form.get("email", "")
    website = request.form.get("website", "")

    researcher = WebsiteResearcher(firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY", ""))
    copywriter = AICopywriter(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        sender_name=os.getenv("SENDER_NAME", "Adegbite David")
    )

    site_data = researcher.research(website)
    draft = copywriter.generate_draft(biz, name, site_data.get("text", ""))
    DRAFTS_CACHE[email] = draft

    leads = load_leads()
    for l in leads:
        em = l.get("email")
        if em in DRAFTS_CACHE:
            l["draft"] = DRAFTS_CACHE[em]

    return render_template_string(HTML_TEMPLATE, leads=leads)

@app.route("/send_email", methods=["POST"])
def send_email():
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

    msg = res.get("message") or res.get("error") or f"Successfully sent to {to_email}!"
    success = res.get("success", False)

    leads = load_leads()
    for l in leads:
        em = l.get("email")
        if em in DRAFTS_CACHE:
            l["draft"] = DRAFTS_CACHE[em]

    return render_template_string(HTML_TEMPLATE, leads=leads, send_message=msg, send_success=success)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
