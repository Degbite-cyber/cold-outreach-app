import os
import requests
from flask import Flask, render_template_string, request

from safety_guard import SafetyGuard
from verifier import EmailVerifier
from researcher import WebsiteResearcher
from copywriter import AICopywriter
from scout import AutoLeadScout

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>B2B Autonomous Lead Machine - Adegbite David</title>
  <style>
    * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: #0f172a; color: #f8fafc; margin: 0; padding: 16px; }
    .container { max-width: 650px; margin: auto; }
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
    .lead-box { background: #0f172a; padding: 14px; border-radius: 8px; border-left: 4px solid #38bdf8; margin-top: 14px; }
    pre { white-space: pre-wrap; font-family: inherit; font-size: 14px; line-height: 1.5; color: #f1f5f9; background: #020617; padding: 10px; border-radius: 6px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">
      <h2>🤖 Autonomous B2B Lead & Outreach Machine</h2>
      <p class="subtitle">Finds businesses, finds their emails, verifies them, and writes emails automatically.</p>

      <form method="POST">
        <label>Target Niche / Industry:</label>
        <input type="text" name="niche" placeholder="e.g. Solar Contractors, Roofing, Dental Clinics" required value="{{ niche or 'Digital Marketing Agency' }}">

        <label>Target Location / City:</label>
        <input type="text" name="location" placeholder="e.g. Austin Texas, London UK, Miami" required value="{{ location or 'Austin Texas' }}">

        <label>How Many Leads to Hunt:</label>
        <input type="number" name="count" min="1" max="5" value="{{ count or 3 }}" required>

        <button type="submit">⚡ Hunt Leads & Auto-Generate Outreach</button>
      </form>
    </div>

    {% if results %}
    <div class="card">
      <h3>🎯 Discovered & Processed Leads ({{ results|length }})</h3>
      {% for item in results %}
        <div class="lead-box">
          <h4 style="margin: 0; color: #38bdf8;">{{ item.biz }}</h4>
          <p style="margin: 4px 0; font-size: 13px; color: #94a3b8;">
            Website: <a href="{{ item.web }}" target="_blank" style="color: #38bdf8;">{{ item.web }}</a> | Email: <strong>{{ item.email }}</strong>
          </p>
          <p style="margin: 4px 0;">
            <strong>Verification:</strong> 
            <span class="badge {% if item.is_safe %}badge-valid{% else %}badge-invalid{% endif %}">
              {{ item.v_status }}
            </span>
          </p>
          {% if item.draft %}
            <p style="margin: 6px 0 2px 0; font-size: 13px;"><strong>Subject:</strong> {{ item.draft.subject }}</p>
            <pre>{{ item.draft.body }}</pre>
          {% endif %}
        </div>
      {% endfor %}
    </div>
    {% endif %}
  </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    niche = "Digital Marketing Agency"
    location = "Austin Texas"
    count = 3

    if request.method == "POST":
        niche = request.form.get("niche", "").strip()
        location = request.form.get("location", "").strip()
        count = int(request.form.get("count", 3))

        scout = AutoLeadScout()
        found_leads = scout.scout(niche, location, count=count)

        guard = SafetyGuard(sender_address=os.getenv("SENDER_ADDRESS", "Lagos, Nigeria"))
        verifier = EmailVerifier(api_key=os.getenv("REOON_API_KEY", ""))
        researcher = WebsiteResearcher(firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY", ""))
        copywriter = AICopywriter(
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            sender_name=os.getenv("SENDER_NAME", "Adegbite David")
        )

        for l in found_leads:
            biz = l["business_name"]
            web = l["website"]
            email = l["email"]
            name = l["first_name"]

            v_res = verifier.verify(email)
            draft = None
            if v_res.get("is_safe_to_send", True):
                site_data = researcher.research(web)
                draft = copywriter.generate_draft(biz, name, site_data.get("text", ""))

            results.append({
                "biz": biz,
                "web": web,
                "email": email,
                "v_status": v_res.get("status", "VALID"),
                "is_safe": v_res.get("is_safe_to_send", True),
                "draft": draft
            })

    return render_template_string(HTML_TEMPLATE, results=results, niche=niche, location=location, count=count)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
