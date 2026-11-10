import os
import sys
import csv
from typing import Dict, Any

from safety_guard import SafetyGuard
from verifier import EmailVerifier
from researcher import WebsiteResearcher
from copywriter import AICopywriter
from scheduler import TimezoneScheduler
from sender import GmailSender
from sheets_manager import SheetsManager

def load_local_env(env_path: str = ".env"):
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ[k] = v

def run_pipeline():
    load_local_env()

    print("=" * 65)
    print("COLD OUTREACH AUTOMATION ENGINE: RUNNER")
    print("=" * 65)

    sender_name = os.getenv("SENDER_NAME", "Adegbite David")
    sender_email = os.getenv("SENDER_EMAIL", "adegbiteishola001@gmail.com")
    app_password = os.getenv("GMAIL_APP_PASSWORD", "")
    sender_address = os.getenv("SENDER_ADDRESS", "Lagos, Nigeria")
    dry_run = os.getenv("DRY_RUN", "True").lower() in ("true", "1")

    # Initialize modules
    guard = SafetyGuard(sender_address=sender_address)
    verifier = EmailVerifier(api_key=os.getenv("REOON_API_KEY", ""))
    researcher = WebsiteResearcher(firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY", ""))
    copywriter = AICopywriter(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        sender_name=sender_name
    )
    scheduler = TimezoneScheduler()
    sender = GmailSender(sender_email, app_password, sender_name, dry_run=dry_run)
    sheets = SheetsManager(webapp_url=os.getenv("GOOGLE_SHEET_WEBAPP_URL", ""))

    # 1. Fetch leads: Google Sheets first, fallback to sample_leads.csv
    leads = []
    use_sheets = sheets.is_connected()

    if use_sheets:
        print("[SHEETS] Fetching live leads from Google Sheets...")
        sheet_data = sheets.get_leads()
        if sheet_data.get("is_paused"):
            print("🛑 MASTER_PAUSE switch is PAUSED in Google Sheet! Halting execution.")
            return
        leads = sheet_data.get("leads", [])
        print(f"Loaded {len(leads)} leads from Google Sheets.")
    else:
        print("[CSV] Using local sample_leads.csv (Google Sheets not yet linked)...")
        with open("sample_leads.csv", mode="r", encoding="utf-8") as f:
            leads = list(csv.DictReader(f))
        for idx, l in enumerate(leads, start=2):
            l["_row_number"] = idx

    print(f"Total leads to process: {len(leads)}\n")

    for i, lead in enumerate(leads, 1):
        biz = lead.get("business_name", "")
        email = lead.get("email", "")
        website = lead.get("website", "")
        name = lead.get("first_name", "")
        country = lead.get("country", "US")
        status = lead.get("status", "")
        row_num = lead.get("_row_number", i + 1)

        print(f"[{i}/{len(leads)}] Processing Target: {biz} ({email})")

        # Skip already completed or held
        if status in ["SENT", "FOLLOWUP_1", "REPLIED", "HOLD"]:
            print(f"  [SKIPPED] Status is already '{status}'.\n")
            continue

        # Step 1: Role address check
        if guard.is_role_address(email):
            print(f"  [SKIPPED] Generic role address ({email}).\n")
            if use_sheets:
                sheets.update_lead(row_num, {"email_status": "ROLE_ADDRESS", "status": "SKIPPED"})
            continue

        # Step 2: Email Verification
        print(f"  [CHECK] Verifying email hygiene via Reoon API...")
        v_res = verifier.verify(email)
        print(f"     Status: {v_res['status']} | Safe: {v_res.get('is_safe_to_send')}")
        if not v_res["is_safe_to_send"]:
            print(f"  [SKIPPED] Verification failed.\n")
            if use_sheets:
                sheets.update_lead(row_num, {"email_status": v_res["status"], "status": "INVALID"})
            continue

        # Step 3: Website Research
        print(f"  [RESEARCH] Reading website ({website})...")
        site_data = researcher.research(website)
        print(f"     Retrieved: {len(site_data.get('text', ''))} chars")

        # Step 4: AI Drafting (Susana Playbook)
        print(f"  [DRAFT] Drafting outreach with Gemini / Groq...")
        draft = copywriter.generate_draft(biz, name, site_data.get("text", ""))
        validated = guard.validate_copy(draft["subject"], draft["body"])
        if not validated["valid"]:
            print(f"  [WARNING] Draft rejected: {validated['issues']}\n")
            continue

        full_body = guard.append_can_spam_footer(draft["body"])
        print(f"     Subject: {draft['subject']} ({validated['word_count']} words)")

        # Step 5: Timezone Check
        tz = scheduler.resolve_timezone(lead.get("timezone"), country)
        window = scheduler.is_in_send_window(tz)
        print(f"  [SCHEDULE] Timezone: {tz} | In Send Window (Tue-Thu 9-10 AM): {window['can_send']}")

        # Save draft to Google Sheets if connected
        if use_sheets:
            sheets.update_lead(row_num, {
                "email_status": "VALID",
                "research_notes": site_data.get("text", "")[:150],
                "draft_subject": draft["subject"],
                "draft_body": draft["body"],
                "status": "DRAFTED"
            })

        # Step 6: Dispatch / Dry-Run
        approved = str(lead.get("approved", "")).strip().upper()
        if approved == "N":
            print(f"  [HOLD] Marked N in sheet. Pausing send.\n")
            continue

        send_res = sender.send_email(email, draft["subject"], full_body)
        print(f"  [ACTION] {send_res.get('message', 'Complete')}\n")

        if use_sheets and not dry_run and send_res.get("success"):
            sheets.update_lead(row_num, {"status": "SENT"})

    print("=" * 65)
    print("PIPELINE EXECUTION COMPLETE")
    print("=" * 65)

if __name__ == "__main__":
    run_pipeline()
