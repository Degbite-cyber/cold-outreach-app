import os
import sys
import csv
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json

from safety_guard import SafetyGuard
from verifier import EmailVerifier
from researcher import WebsiteResearcher
from copywriter import AICopywriter
from scheduler import TimezoneScheduler
from sender import GmailSender

def load_env():
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")

class WebUIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        html = """<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Outreach Control Panel</title>
  <style>
    body { font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; max-width: 600px; margin: auto; }
    h2 { color: #38bdf8; }
    input, button { width: 100%; padding: 12px; margin: 8px 0; border-radius: 6px; border: 1px solid #334155; font-size: 16px; box-sizing: border-box; }
    input { background: #1e293b; color: white; }
    button { background: #0284c7; color: white; font-weight: bold; cursor: pointer; border: none; }
    .card { background: #1e293b; padding: 16px; border-radius: 8px; margin-top: 16px; }
  </style>
</head>
<body>
  <h2>🚀 Cold Outreach Mobile UI</h2>
  <p>Owner: Adegbite David | n8n & Make Automation</p>
  
  <div class="card">
    <h3>Add a Business Lead</h3>
    <form method="POST" action="/run">
      <label>Business Name:</label>
      <input type="text" name="biz" placeholder="e.g. Apex Digital" required>
      <label>Website URL:</label>
      <input type="url" name="web" placeholder="e.g. https://apex.com" required>
      <label>Contact Email:</label>
      <input type="email" name="email" placeholder="e.g. founder@apex.com" required>
      <label>First Name:</label>
      <input type="text" name="name" placeholder="e.g. Marcus">
      <button type="submit">Run Gemini & Verify</button>
    </form>
  </div>
</body>
</html>"""
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length).decode('utf-8')
        params = urllib.parse.parse_qs(body)

        biz = params.get('biz', [''])[0]
        web = params.get('web', [''])[0]
        email = params.get('email', [''])[0]
        name = params.get('name', [''])[0]

        load_env()
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

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        resp_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Results</title>
  <style>
    body {{ font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; max-width: 600px; margin: auto; }}
    .box {{ background: #1e293b; padding: 16px; border-radius: 8px; margin-top: 16px; border-left: 4px solid #38bdf8; }}
    pre {{ white-space: pre-wrap; font-family: inherit; }}
    a {{ color: #38bdf8; text-decoration: none; }}
  </style>
</head>
<body>
  <h2>✅ Lead Processed</h2>
  <div class="box">
    <strong>Verification:</strong> {v_res.get('status')} (Safe: {v_res.get('is_safe_to_send')})<br>
    <strong>Target:</strong> {biz} ({email})<br><br>
    <strong>Subject:</strong> {draft.get('subject')}<br><br>
    <strong>Personalized Email:</strong>
    <pre>{draft.get('body')}</pre>
  </div>
  <p><a href="/">← Back to Control Panel</a></p>
</body>
</html>"""
        self.wfile.write(resp_html.encode("utf-8"))

def start_server():
    server = HTTPServer(("0.0.0.0", 8080), WebUIHandler)
    print("Web control panel running at http://localhost:8080")
    server.serve_forever()

if __name__ == "__main__":
    start_server()
