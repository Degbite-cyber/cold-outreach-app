import os
import requests
from flask import Flask, render_template_string, request

from safety_guard import SafetyGuard
from verifier import EmailVerifier
from researcher import WebsiteResearcher
from copywriter import AICopywriter

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
    .container { max-width: 520px; margin: auto; }
    .card { background: #1e293b; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); margin-bottom: 20px; }
    h2 { color: #38bdf8; margin-top: 0; font-size: 22px; }
    p.subtitle { color: #94a3b8; font-size: 14px; margin-top: -6px; }
    label { font-size: 13px; color: #cbd5e1; font-weight: 600; margin-top: 12px; display: block; }
    input { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: white; font-size: 15px; margin-top: 6px; }
    input:focus { outline: none; border-color: #38bdf8; }
    button { width: 100%; background: #0284c7; color: white; padding: 14px; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; margin-top: 20px; }
    button:active { background: #0369a1; }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-valid { background: #166534; color: #bbf7d0; }
    .badge-invalid { background: #991b1b; color: #fecaca; }
    .result-box { background: #0f172a; padding: 14px; border-radius: 8px; border-left: 4px solid #38bdf8; margin-top: 12px; }
    pre { white-space: pre-wrap; font-family: inherit; font-size: 14px; line-height: 1.5; color: #f1f5f9; }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <h2>🚀 Cold Outreach Engine</h2>
      <p class="subtitle">Personalized n8n / Make Automation Outreach</p>

      <form method="POST">
        <label>Company / Business Name:</label>
        <input type="text" name="biz" placeholder="e.g. Skyline Logistics" required value="{{ biz or '' }}">

        <label>Website URL:</label>
        <input type="url" name="web" placeholder="e.g. https://skylinelogistics.com" required value="{{ web or '' }}">

        <label>Recipient Work Email:</label>
        <input type="email" name="email" placeholder="e.g. john@skylinelogistics.com" required value="{{ email or '' }}">

        <label>First Name (Optional):</label>
        <input type="text" name="name" placeholder="e.g. John" value="{{ name or '' }}">

        <button type="submit">Verify & Generate Cold Email</button>
      </form>
    </div>

    {% if result %}
    <div class="card">
      <h3>Outcome & Verification</h3>
      <p>
        <strong>Email Status:</strong> 
        <span class="badge {% if result.safe %}badge-valid{% else %}badge-invalid{% endif %}">
          {{ result.status }}
        </span>
      </p>

      {% if result.draft %}
      <div class="result-box">
        <strong>Subject:</strong> {{ result.draft.subject }}<br><br>
        <strong>Body Preview:</strong>
        <pre>{{ result.draft.body }}</pre>
      </div>
      <p style="font-size: 12px; color: #94a3b8;">Generated via Gemini 3.8 / Groq adhering strictly to the &lt;100-word Susana Playbook rule.</p>
      {% endif %}
    </div>
    {% endif %}
  </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    biz = web = email = name = ""

    if request.method == "POST":
        biz = request.form.get("biz", "").strip()
        web = request.form.get("web", "").strip()
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()

        # Load keys from environment
        guard = SafetyGuard(sender_address=os.getenv("SENDER_ADDRESS", "Lagos, Nigeria"))
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

        result = {
            "status": v_res.get("status", "UNKNOWN"),
            "safe": v_res.get("is_safe_to_send", False),
            "draft": draft
        }

    return render_template_string(HTML_TEMPLATE, result=result, biz=biz, web=web, email=email, name=name)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
