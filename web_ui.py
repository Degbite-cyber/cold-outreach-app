"""
Cold Outreach Web App - Final Version
Uses Gmail Compose URL (no SMTP needed - works on Render free tier)
Author: Adegbite David
"""

from flask import Flask, request, jsonify, render_template_string
import csv, os, json, urllib.parse, urllib.request

app = Flask(__name__)

# ── CONFIG ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY   = os.environ.get("GROQ_API_KEY", "")
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
            # Filter generic/role addresses
            blocked = ["info@","support@","sales@","hello@","admin@","contact@","noreply@","no-reply@","team@","help@"]
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

# ── GEMINI PITCH GENERATOR ────────────────────────────────────────────────────
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

Return ONLY valid JSON: {{"subject": "...", "body": "..."}}"""

def generate_pitch_gemini(lead):
    if not GEMINI_API_KEY:
        return None, "GEMINI_API_KEY missing"
    
    prompt = SUSANA_PROMPT.format(
        sender_name=SENDER_NAME,
        first_name=lead["first_name"],
        title=lead["title"],
        business_name=lead["business_name"],
        website=lead["website"]
    )
    
    # Try models in order
    models = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-1.5-flash"]
    
    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 512}
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())
            raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw.strip())
            return result, None
        except Exception as e:
            last_err = str(e)
            continue
    
    return None, f"Gemini failed: {last_err}"

def generate_pitch_groq(lead):
    if not GROQ_API_KEY:
        return None, "GROQ_API_KEY missing"
    
    prompt = SUSANA_PROMPT.format(
        sender_name=SENDER_NAME,
        first_name=lead["first_name"],
        title=lead["title"],
        business_name=lead["business_name"],
        website=lead["website"]
    )
    
    groq_models = ["llama3-70b-8192", "mixtral-8x7b-32768", "llama3-8b-8192"]
    
    for model in groq_models:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 512
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}"
            })
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())
            raw = data["choices"][0]["message"]["content"].strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw.strip())
            return result, None
        except Exception as e:
            last_err = str(e)
            continue
    
    return None, f"Groq failed: {last_err}"

def generate_pitch(lead):
    result, err = generate_pitch_gemini(lead)
    if result:
        return result, "gemini"
    result, err2 = generate_pitch_groq(lead)
    if result:
        return result, "groq"
    # Final fallback - template pitch
    fallback = {
        "subject": f"Quick automation idea for {lead['business_name']}",
        "body": (
            f"Hi {lead['first_name']},\n\n"
            f"I noticed {lead['business_name']} handles client acquisition manually - "
            f"an n8n workflow can automate your lead intake, CRM updates, and follow-up emails in one click.\n"
            f"Most agency owners save 8-12 hours per week after setup.\n\n"
            f"Would a 10-minute walkthrough make sense this week?\n\n"
            f"Best,\n{SENDER_NAME}\n{SENDER_EMAIL}\n\n"
            f"--\nThis email was sent from {SENDER_ADDRESS}. "
            f"Reply STOP to unsubscribe."
        )
    }
    return fallback, "fallback"

# ── CAN-SPAM FOOTER ───────────────────────────────────────────────────────────
def add_footer(body, lead):
    footer = (
        f"\n\nBest,\n{SENDER_NAME}\n{SENDER_EMAIL}\n\n"
        f"--\n"
        f"You are receiving this because you are listed as {lead['title']} at {lead['business_name']}. "
        f"Sent from {SENDER_ADDRESS}. "
        f"Reply STOP to unsubscribe."
    )
    return body + footer

# ── GMAIL COMPOSE URL ─────────────────────────────────────────────────────────
def build_gmail_url(to_email, subject, body):
    params = urllib.parse.urlencode({
        "view": "cm",
        "fs": "1",
        "to": to_email,
        "su": subject,
        "body": body
    })
    return f"https://mail.google.com/mail/?{params}"

# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    leads = load_leads()
    return render_template_string(HTML_TEMPLATE, leads=leads, count=len(leads))

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    idx = data.get("idx", 0)
    leads = load_leads()
    if idx >= len(leads):
        return jsonify({"error": "Lead index out of range"}), 400
    
    lead = leads[idx]
    result, source = generate_pitch(lead)
    
    subject = result.get("subject", f"Quick note for {lead['first_name']}")
    body = result.get("body", "")
    body_with_footer = add_footer(body, lead)
    
    gmail_url = build_gmail_url(lead["email"], subject, body_with_footer)
    
    return jsonify({
        "subject": subject,
        "body": body_with_footer,
        "gmail_url": gmail_url,
        "source": source,
        "word_count": len(body.split())
    })

@app.route("/health")
def health():
    leads = load_leads()
    return jsonify({
        "status": "ok",
        "leads_loaded": len(leads),
        "gemini_key": bool(GEMINI_API_KEY),
        "groq_key": bool(GROQ_API_KEY)
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
  .stats{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px 16px;margin-bottom:20px;display:flex;gap:20px}
  .stat{text-align:center}
  .stat-num{font-size:1.4rem;font-weight:700;color:#58a6ff}
  .stat-label{font-size:.75rem;color:#8b949e}
  .lead-card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px;margin-bottom:14px}
  .lead-name{color:#58a6ff;font-size:1rem;font-weight:700;margin-bottom:4px}
  .lead-meta{color:#8b949e;font-size:.8rem;margin-bottom:4px}
  .lead-email{color:#3fb950;font-size:.82rem;margin-bottom:12px}
  .btn{display:inline-block;padding:10px 18px;border-radius:6px;border:none;cursor:pointer;font-size:.88rem;font-weight:600;text-decoration:none;transition:opacity .2s}
  .btn-generate{background:#1f6feb;color:#fff;width:100%;margin-bottom:10px}
  .btn-send{background:#238636;color:#fff;width:100%;display:none;text-align:center}
  .btn:hover{opacity:.85}
  .pitch-box{display:none;margin-top:12px}
  .pitch-label{font-size:.78rem;color:#8b949e;margin-bottom:4px}
  .pitch-subject{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:10px;font-size:.85rem;color:#e6edf3;margin-bottom:10px;width:100%}
  .pitch-body{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:10px;font-size:.83rem;color:#e6edf3;width:100%;height:160px;resize:vertical;white-space:pre-wrap}
  .word-badge{font-size:.75rem;color:#8b949e;margin-top:4px}
  .source-badge{font-size:.72rem;padding:2px 8px;border-radius:10px;margin-left:8px}
  .source-gemini{background:#1f3a5f;color:#58a6ff}
  .source-groq{background:#2d1f3f;color:#bc8cff}
  .source-fallback{background:#3f2d1f;color:#d29922}
  .loading{color:#8b949e;font-size:.85rem;text-align:center;padding:8px}
  .error-msg{color:#f85149;font-size:.82rem;margin-top:8px}
  .header-bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
  .upload-hint{background:#1c2a1e;border:1px solid #238636;border-radius:8px;padding:12px;margin-bottom:16px;font-size:.82rem;color:#3fb950}
</style>
</head>
<body>
<div class="header-bar">
  <div>
    <h1>Outreach Hub</h1>
    <div class="subtitle">Adegbite David | n8n / Make.com / Zapier Automation Services</div>
  </div>
</div>

<div class="stats">
  <div class="stat"><div class="stat-num">{{ count }}</div><div class="stat-label">Verified Leads</div></div>
  <div class="stat"><div class="stat-num">0</div><div class="stat-label" id="sent-count">Sent Today</div></div>
  <div class="stat"><div class="stat-num">Free</div><div class="stat-label">No SMTP Needed</div></div>
</div>

<div class="upload-hint">
  How it works: Click Generate → review the AI pitch → click Send via Gmail → Gmail opens pre-filled → click Send. Done.
</div>

{% for lead in leads %}
<div class="lead-card" id="card-{{ loop.index0 }}">
  <div class="lead-name">{{ lead.business_name }}</div>
  <div class="lead-meta">{{ lead.title }}: {{ lead.first_name }} | {{ lead.country }} | {{ lead.timezone }}</div>
  <div class="lead-email">{{ lead.email }}</div>
  
  <button class="btn btn-generate" onclick="generatePitch({{ loop.index0 }})">
    Generate AI Pitch for {{ lead.first_name }}
  </button>
  
  <div class="pitch-box" id="pitch-{{ loop.index0 }}">
    <div class="pitch-label">Subject Line <span class="source-badge" id="src-{{ loop.index0 }}"></span></div>
    <input class="pitch-subject" id="subj-{{ loop.index0 }}" type="text" readonly>
    
    <div class="pitch-label" style="margin-top:10px">Personalized Pitch (under 100 words, no em dashes)</div>
    <textarea class="pitch-body" id="body-{{ loop.index0 }}"></textarea>
    <div class="word-badge" id="words-{{ loop.index0 }}"></div>
    
    <a class="btn btn-send" id="send-{{ loop.index0 }}" href="#" target="_blank">
      Send Live to {{ lead.first_name }} via Gmail
    </a>
  </div>
  
  <div class="loading" id="loading-{{ loop.index0 }}" style="display:none">Writing pitch with AI...</div>
  <div class="error-msg" id="err-{{ loop.index0 }}"></div>
</div>
{% endfor %}

<script>
let sentCount = 0;

async function generatePitch(idx) {
  const loadEl  = document.getElementById('loading-' + idx);
  const pitchEl = document.getElementById('pitch-' + idx);
  const sendEl  = document.getElementById('send-' + idx);
  const errEl   = document.getElementById('err-' + idx);
  
  loadEl.style.display = 'block';
  pitchEl.style.display = 'none';
  sendEl.style.display  = 'none';
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
      loadEl.style.display = 'none';
      return;
    }

    document.getElementById('subj-' + idx).value = data.subject;
    document.getElementById('body-' + idx).value  = data.body;
    document.getElementById('words-' + idx).textContent = data.word_count + ' words (body only)';
    
    const srcEl = document.getElementById('src-' + idx);
    srcEl.textContent = data.source.toUpperCase();
    srcEl.className = 'source-badge source-' + data.source;

    sendEl.href = data.gmail_url;
    sendEl.style.display = 'block';
    sendEl.onclick = () => {
      sentCount++;
      document.getElementById('sent-count').textContent = sentCount + ' Sent Today';
    };
    
    pitchEl.style.display = 'block';
  } catch(e) {
    errEl.textContent = 'Network error. Try again.';
  } finally {
    loadEl.style.display = 'none';
  }
}
</script>
</body>
</html>"""

# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
