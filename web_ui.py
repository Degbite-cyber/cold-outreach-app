"""
Cold Outreach Web App - Brevo Auto-Send Version
Fully automated: Gemini writes pitch, Brevo sends email automatically.
No SMTP. No Gmail clicking. Works 100% on Koyeb free tier.
Author: Adegbite David
"""

from flask import Flask, request, jsonify, render_template_string
import csv, os, json, urllib.parse, urllib.request

app = Flask(__name__)

# ── CONFIG ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
BREVO_API_KEY  = os.environ.get("BREVO_API_KEY", "")
SENDER_NAME    = os.environ.get("SENDER_NAME", "Adegbite David")
SENDER_EMAIL   = os.environ.get("SENDER_EMAIL", "adegbiteishola001@gmail.com")
SENDER_ADDRESS = os.environ.get("SENDER_ADDRESS", "Lagos, Nigeria")

LEADS_FILE = os.path.join(os.path.dirname(__file__), "sample_leads.csv")

# ── LOAD LEADS ────────────────────────────────────────────────────────────────
def load_leads():
    leads = []
    if not os.path.exists(LEADS_FILE):
        return leads
    with open(LEADS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("email", "").strip()
            if not email:
                continue
            blocked = ["info@","support@","sales@","hello@","admin@",
                       "contact@","noreply@","no-reply@","team@","help@"]
            if any(email.lower().startswith(b) for b in blocked):
                continue
            leads.append({
                "business_name": row.get("business_name","").strip(),
                "website":       row.get("website","").strip(),
                "first_name":    row.get("first_name","").strip(),
                "email":         email,
                "country":       row.get("country","US").strip(),
                "timezone":      row.get("timezone","America/New_York").strip(),
                "title":         row.get("title","Owner").strip(),
            })
    return leads

# ── AI PITCH GENERATOR ────────────────────────────────────────────────────────
SUSANA_PROMPT = """You are a cold email copywriter following Susana Otokpa's $1K Client in 72 Hours Prompt Playbook.

Write a cold email pitch for {sender_name} who offers n8n/Make.com/Zapier workflow automation services.

Target: {first_name}, {title} at {business_name} ({website})

STRICT RULES:
1. Under 100 words body (excluding greeting and sign-off)
2. NO em dashes (--) anywhere
3. NO filler phrases: "I hope you are well", "I came across your profile", "I wanted to reach out"
4. First sentence must reference something specific from their website or business type
5. Second sentence shows what your automation solves for their exact workflow
6. Third sentence gives a concrete time/money saving stat
7. End with ONE low-friction question (not "Can we schedule a call?")
8. Tone: direct, peer-to-peer, zero fluff

Also write a subject line (under 8 words, no clickbait).

Return ONLY valid JSON with no extra text: {{"subject": "...", "body": "..."}}"""

def call_gemini(prompt):
    if not GEMINI_API_KEY:
        return None, "No Gemini key"
    models = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-1.5-flash"]
    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 512}
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read())
            raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip()), None
        except Exception as e:
            last = str(e)
    return None, last

def call_groq(prompt):
    if not GROQ_API_KEY:
        return None, "No Groq key"
    models = ["llama3-70b-8192", "mixtral-8x7b-32768", "llama3-8b-8192"]
    for model in models:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7, "max_tokens": 512
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}"
            })
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read())
            raw = data["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            return json.loads(raw.strip()), None
        except Exception as e:
            last = str(e)
    return None, last

def generate_pitch(lead):
    prompt = SUSANA_PROMPT.format(
        sender_name=SENDER_NAME,
        first_name=lead["first_name"],
        title=lead["title"],
        business_name=lead["business_name"],
        website=lead["website"]
    )
    result, _ = call_gemini(prompt)
    if result:
        return result, "Gemini"
    result, _ = call_groq(prompt)
    if result:
        return result, "Groq"
    # Fallback template
    return {
        "subject": f"Quick automation idea for {lead['business_name']}",
        "body": (
            f"Hi {lead['first_name']},\n\n"
            f"Running {lead['business_name']} means juggling client intake, "
            f"CRM updates, and follow-ups every day.\n"
            f"An n8n workflow automates all of that in one click, saving most "
            f"agency owners 10 hours a week.\n\n"
            f"Would a quick 10-minute walkthrough be worth it this week?"
        )
    }, "Template"

# ── CAN-SPAM FOOTER ───────────────────────────────────────────────────────────
def add_footer(body, lead):
    return (
        f"{body}\n\n"
        f"Best,\n{SENDER_NAME}\n{SENDER_EMAIL}\n\n"
        f"--\n"
        f"You are receiving this because you are listed as {lead['title']} "
        f"at {lead['business_name']}. Sent from {SENDER_ADDRESS}. "
        f"Reply STOP to unsubscribe."
    )

# ── BREVO EMAIL SENDER ────────────────────────────────────────────────────────
def send_via_brevo(to_email, to_name, subject, body):
    if not BREVO_API_KEY:
        return False, "BREVO_API_KEY not set in environment variables"
    try:
        url = "https://api.brevo.com/v3/smtp/email"
        payload = json.dumps({
            "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
            "to":          [{"email": to_email,  "name":  to_name}],
            "subject":     subject,
            "textContent": body
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "api-key":      BREVO_API_KEY
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp.read()
        return True, "Email sent successfully"
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        return False, f"Brevo error {e.code}: {err_body}"
    except Exception as e:
        return False, str(e)

# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    leads = load_leads()
    return render_template_string(HTML_TEMPLATE, leads=leads, count=len(leads))

@app.route("/generate", methods=["POST"])
def generate():
    data  = request.json
    idx   = data.get("idx", 0)
    leads = load_leads()
    if idx >= len(leads):
        return jsonify({"error": "Lead not found"}), 400
    lead = leads[idx]
    result, source = generate_pitch(lead)
    subject         = result.get("subject", f"Quick note for {lead['first_name']}")
    body            = result.get("body", "")
    body_with_footer = add_footer(body, lead)
    return jsonify({
        "subject":    subject,
        "body":       body_with_footer,
        "source":     source,
        "word_count": len(body.split())
    })

@app.route("/send", methods=["POST"])
def send():
    data  = request.json
    idx   = data.get("idx", 0)
    leads = load_leads()
    if idx >= len(leads):
        return jsonify({"error": "Lead not found"}), 400
    lead    = leads[idx]
    subject = data.get("subject", "")
    body    = data.get("body", "")
    if not subject or not body:
        return jsonify({"error": "Subject and body are required"}), 400
    ok, msg = send_via_brevo(lead["email"], lead["first_name"], subject, body)
    if ok:
        return jsonify({"success": True,  "message": msg})
    else:
        return jsonify({"success": False, "error":   msg}), 500

@app.route("/health")
def health():
    leads = load_leads()
    return jsonify({
        "status":        "ok",
        "leads_loaded":  len(leads),
        "gemini_key":    bool(GEMINI_API_KEY),
        "groq_key":      bool(GROQ_API_KEY),
        "brevo_key":     bool(BREVO_API_KEY)
    })

# ── HTML TEMPLATE ─────────────────────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Outreach Hub | Adegbite David</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d1117;color:#e6edf3;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:16px}
h1{color:#58a6ff;font-size:1.3rem;margin-bottom:4px}
.subtitle{color:#8b949e;font-size:.85rem;margin-bottom:20px}
.stats{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px 16px;margin-bottom:20px;display:flex;gap:20px;flex-wrap:wrap}
.stat{text-align:center}
.stat-num{font-size:1.4rem;font-weight:700;color:#58a6ff}
.stat-label{font-size:.75rem;color:#8b949e}
.lead-card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px;margin-bottom:14px}
.lead-name{color:#58a6ff;font-size:1rem;font-weight:700;margin-bottom:4px}
.lead-meta{color:#8b949e;font-size:.8rem;margin-bottom:4px}
.lead-email{color:#3fb950;font-size:.82rem;margin-bottom:12px}
.btn{display:block;width:100%;padding:11px;border-radius:6px;border:none;cursor:pointer;font-size:.9rem;font-weight:700;margin-bottom:8px;transition:opacity .2s}
.btn-generate{background:#1f6feb;color:#fff}
.btn-send{background:#238636;color:#fff;display:none}
.btn:hover{opacity:.85}
.btn:disabled{opacity:.5;cursor:not-allowed}
.pitch-box{display:none;margin-top:12px}
.pitch-label{font-size:.78rem;color:#8b949e;margin-bottom:4px;margin-top:10px}
.pitch-subject{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:10px;font-size:.85rem;color:#e6edf3;width:100%}
.pitch-body{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:10px;font-size:.83rem;color:#e6edf3;width:100%;height:170px;resize:vertical;font-family:inherit}
.word-badge{font-size:.75rem;color:#8b949e;margin-top:4px}
.source-badge{font-size:.72rem;padding:2px 8px;border-radius:10px;margin-left:8px;font-weight:600}
.src-Gemini{background:#1f3a5f;color:#58a6ff}
.src-Groq{background:#2d1f3f;color:#bc8cff}
.src-Template{background:#3f2d1f;color:#d29922}
.loading{color:#8b949e;font-size:.85rem;text-align:center;padding:10px}
.msg-success{color:#3fb950;font-size:.85rem;margin-top:8px;font-weight:600}
.msg-error{color:#f85149;font-size:.85rem;margin-top:8px}
.sent-stamp{background:#1c2a1e;border:1px solid #238636;border-radius:6px;padding:8px 12px;color:#3fb950;font-size:.85rem;margin-top:8px;display:none}
</style>
</head>
<body>

<h1>Outreach Hub</h1>
<div class="subtitle">Adegbite David | n8n / Make.com / Zapier Automation Services</div>

<div class="stats">
  <div class="stat"><div class="stat-num">{{ count }}</div><div class="stat-label">Real Leads</div></div>
  <div class="stat"><div class="stat-num" id="sent-count">0</div><div class="stat-label">Emails Sent</div></div>
  <div class="stat"><div class="stat-num">Auto</div><div class="stat-label">Brevo API</div></div>
  <div class="stat"><div class="stat-num">Free</div><div class="stat-label">300/day</div></div>
</div>

{% for lead in leads %}
<div class="lead-card" id="card-{{ loop.index0 }}">
  <div class="lead-name">{{ lead.business_name }}</div>
  <div class="lead-meta">{{ lead.title }}: {{ lead.first_name }} | {{ lead.country }}</div>
  <div class="lead-email">{{ lead.email }}</div>

  <button class="btn btn-generate" id="genbtn-{{ loop.index0 }}"
          onclick="generatePitch({{ loop.index0 }})">
    Generate AI Pitch for {{ lead.first_name }}
  </button>

  <div class="loading" id="genload-{{ loop.index0 }}" style="display:none">
    Writing pitch with AI...
  </div>

  <div class="pitch-box" id="pitch-{{ loop.index0 }}">
    <div class="pitch-label">Subject Line
      <span class="source-badge" id="src-{{ loop.index0 }}"></span>
    </div>
    <input class="pitch-subject" id="subj-{{ loop.index0 }}" type="text">

    <div class="pitch-label">Personalized Pitch (under 100 words, Susana Otokpa playbook)</div>
    <textarea class="pitch-body" id="body-{{ loop.index0 }}"></textarea>
    <div class="word-badge" id="words-{{ loop.index0 }}"></div>

    <button class="btn btn-send" id="sendbtn-{{ loop.index0 }}"
            onclick="sendEmail({{ loop.index0 }})">
      Send Email to {{ lead.first_name }} Automatically
    </button>

    <div class="loading" id="sendload-{{ loop.index0 }}" style="display:none">
      Sending via Brevo...
    </div>

    <div class="sent-stamp" id="stamp-{{ loop.index0 }}">
      Email delivered to {{ lead.email }}
    </div>
  </div>

  <div class="msg-error" id="err-{{ loop.index0 }}"></div>
</div>
{% endfor %}

<script>
let totalSent = 0;

async function generatePitch(idx) {
  const genBtn  = document.getElementById('genbtn-'  + idx);
  const genLoad = document.getElementById('genload-' + idx);
  const pitchEl = document.getElementById('pitch-'   + idx);
  const sendBtn = document.getElementById('sendbtn-' + idx);
  const errEl   = document.getElementById('err-'     + idx);

  genBtn.disabled = true;
  genLoad.style.display = 'block';
  pitchEl.style.display = 'none';
  errEl.textContent = '';

  try {
    const res  = await fetch('/generate', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({idx})
    });
    const data = await res.json();

    if (data.error) {
      errEl.textContent = 'Error: ' + data.error;
      genBtn.disabled = false;
      return;
    }

    document.getElementById('subj-'  + idx).value = data.subject;
    document.getElementById('body-'  + idx).value = data.body;
    document.getElementById('words-' + idx).textContent = data.word_count + ' words (body only)';

    const srcEl = document.getElementById('src-' + idx);
    srcEl.textContent = data.source;
    srcEl.className   = 'source-badge src-' + data.source;

    pitchEl.style.display = 'block';
    sendBtn.style.display  = 'block';
    genBtn.textContent = 'Regenerate Pitch';
    genBtn.disabled    = false;

  } catch(e) {
    errEl.textContent = 'Connection error. Try again.';
    genBtn.disabled   = false;
  } finally {
    genLoad.style.display = 'none';
  }
}

async function sendEmail(idx) {
  const sendBtn  = document.getElementById('sendbtn-'  + idx);
  const sendLoad = document.getElementById('sendload-' + idx);
  const stampEl  = document.getElementById('stamp-'   + idx);
  const errEl    = document.getElementById('err-'     + idx);
  const subject  = document.getElementById('subj-'    + idx).value;
  const body     = document.getElementById('body-'    + idx).value;

  sendBtn.disabled = true;
  sendLoad.style.display = 'block';
  errEl.textContent = '';

  try {
    const res  = await fetch('/send', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({idx, subject, body})
    });
    const data = await res.json();

    if (data.success) {
      stampEl.style.display = 'block';
      sendBtn.textContent   = 'Sent!';
      totalSent++;
      document.getElementById('sent-count').textContent = totalSent;
    } else {
      errEl.textContent = 'Send failed: ' + (data.error || 'Unknown error');
      sendBtn.disabled  = false;
    }
  } catch(e) {
    errEl.textContent = 'Connection error. Try again.';
    sendBtn.disabled  = false;
  } finally {
    sendLoad.style.display = 'none';
  }
}
</script>
</body>
</html>"""

# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
