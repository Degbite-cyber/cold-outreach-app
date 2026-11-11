import os
import requests
from flask import Flask, render_template_string, request

from safety_guard import SafetyGuard
from verifier import EmailVerifier
from researcher import WebsiteResearcher
from copywriter import AICopywriter
from sender import GmailSender
from sequence_manager import SequenceFollowUpManager

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>B2B Outreach Engine - Adegbite David</title>
  <style>
    * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: #0f172a; color: #f8fafc; margin: 0; padding: 16px; }
    .container { max-width: 600px; margin: auto; }
    .card { background: #1e293b; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); margin-bottom: 20px; }
    h2 { color: #38bdf8; margin-top: 0; font-size: 22px; }
    label { font-size: 13px; color: #cbd5e1; font-weight: 600; margin-top: 12px; display: block; }
    input, textarea { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; font-size: 15px; margin-top: 6px; }
    button { width: 100%; padding: 14px; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; margin-top: 16px; }
    .btn-generate { background: #0284c7; color: white; }
    .btn-send { background: #16a34a; color: white; }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-valid { background: #166534; color: #bbf7d0; }
    .badge-invalid { background: #991b1b; color: #fecaca; }
    .result-box { background: #0f172a; padding: 14px; border-radius: 8px; border-left: 4px solid #38bdf8; margin-top: 12px; }
    pre { white-space: pre-wrap; font-family: inherit; font-size: 14px; line-height: 1.5; color: #f1f5f9; }
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
      <h2>🚀 B2B Cold Outreach Engine</h2>
      <p style="color: #94a3b8; font-size: 14px; margin-top: -6px;">n8n & Make Workflow Automation Pitcher</p>

      <form method="POST" action="/generate">
        <label>Company / Business Name:</label>
        <input type="text" name="biz" placeholder="e.g. Apex Roofing" required value="{{ biz or '' }}">

        <label>Company Website URL:</label>
        <input type="url" name="web" placeholder="e.g. https://apexroofing.com" required value="{{ web or '' }}">

        <label>Decision Maker Work Email:</label>
        <input type="email" name="email" placeholder="e.g. marcus@apexroofing.com" required value="{{ email or '' }}">

        <label>First Name (Optional):</label>
        <input type="text" name="name" placeholder="e.g. Marcus" value="{{ name or '' }}">

        <button type="submit" class="btn-generate">🔍 1. Research & Draft Email</button>
      </form>
    </div>

    {% if draft %}
    <div class="card">
      <h3>📋 Review Generated Outreach</h3>
      <p>
        <strong>Reoon Verification:</strong>
        <span class="badge {% if is_safe %}badge-valid{% else %}badge-invalid{% endif %}">
          {{ v_status }}
        </span>
      </p>

      <form method="POST" action="/send">
        <input type="hidden" name="to_email" value="{{ email }}">
        
        <label>Subject Line:</label>
        <input type="text" name="subject" value="{{ draft.subject }}" required>

        <label>Personalized Body (&lt;100 Words):</label>
        <textarea name="body" rows="9" required>{{ draft.body }}</textarea>

        <button type="submit" class="btn-send">✉️ 2. Approve & Send Live Email</button>
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

@app.route("/generate", methods=["POST"])
def generate():
    biz = request.form.get("biz", "").strip()
    web = request.form.get("web", "").strip()
    email = request.form.get("email", "").strip()
    name = request.form.get("name", "").strip()

    verifier = EmailVerifier(api_key=os.getenv("REOON_API_KEY", ""))
    researcher = WebsiteResearcher(firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY", ""))
    copywriter = AICopywriter(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        sender_name=os.getenv("SENDER_NAME", "Adegbite David")
    )

    v_res = verifier.verify(email)
    site_data = researcher.research(web)
    draft = copywriter.generate_draft(biz, name, site_data.get("text", ""))

    return render_template_string(
        HTML_TEMPLATE,
        biz=biz, web=web, email=email, name=name,
        draft=draft,
        v_status=v_res.get("status", "VALID"),
        is_safe=v_res.get("is_safe_to_send", True)
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

    msg = res.get("message") or res.get("error") or "Complete"
    success = res.get("success", False)

    return render_template_string(HTML_TEMPLATE, send_message=msg, send_success=success)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
