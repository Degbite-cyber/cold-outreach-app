# Free B2B Cold Outreach Engine

An automated, safety-first cold outreach system built for **Adegbite David** offering business automation (n8n, Make.com, Zapier) to international clients.

Follows the exact principles from **"Close Your First $1K Client in 72 Hours: The Prompt Playbook"** by Susana Onyowoicho Otokpa.

---

## 🛠️ Features & Architecture

* **100% Free Stack:** GitHub Actions, Google Gemini / Groq API, Firecrawl fallback, Reoon Email Verifier, and Gmail SMTP.
* **Domain & Reputation Protection:**
  * Auto-skips generic role addresses (`info@`, `support@`, `sales@`).
  * Auto-skips unverified / disposable / catch-all emails.
  * Instant circuit breaker: stops sending if bounce rate exceeds 5%.
  * CAN-SPAM compliant: physical address and one-click unsubscribe auto-appended.
* **Strict Copy Rules (Susana Playbook):**
  * Strictly under 100 words.
  * **Zero em dashes (—)** or double hyphens (`--`).
  * No fluff (`"I hope you are well"` / `"I came across your profile"`).
  * High-intent starter offer focused on connecting forms & CRMs to respond to leads in under 60 seconds.
* **Timezone Window Scheduling:**
  * Only sends Tuesday to Thursday between 9:00 AM and 10:00 AM in the recipient's local timezone.
* **Offline Testing & Simulation:**
  * `DRY_RUN=True` ensures you can test everything without sending real emails until you are ready.

---

## 🚀 Setup Checklist

### 1. Local Setup
1. Clone or copy this folder to your machine.
2. Ensure you have Python installed.
3. Install dependencies:
   ```bash
   pip install requests beautifulsoup4
   ```
4. Verify your settings in `.env` (your API keys are already filled in!).

### 2. Run the Offline Safety Tests
Run unit tests to ensure all anti-spam rules and circuit breakers pass:
```bash
python tests/test_engine_unit.py
```

### 3. Run a Dry-Run Pipeline
Simulate the full workflow across sample leads:
```bash
python engine.py
```

---

## ☁️ Deploying to GitHub Actions (Free 24/7 Automation)

1. Create a **Private** repository on GitHub (e.g. `cold-outreach-engine`).
2. Push this entire folder to your repository.
3. In GitHub, go to **Settings > Secrets and variables > Actions > New repository secret**.
4. Add the following secrets from your `.env`:
   * `SENDER_NAME`: `Adegbite David`
   * `SENDER_EMAIL`: `adegbiteishola001@gmail.com`
   * `GMAIL_APP_PASSWORD`: `[Your 16-letter App Password]`
   * `SENDER_ADDRESS`: `Lagos, Nigeria`
   * `GEMINI_API_KEY`: `[Your Gemini Key]`
   * `GROQ_API_KEY`: `[Your Groq Key]`
   * `FIRECRAWL_API_KEY`: `[Your Firecrawl Key]`
   * `REOON_API_KEY`: `[Your Reoon Key]`
   * `DRY_RUN`: `True` (Change to `False` only when ready to send live)

The GitHub Action (`.github/workflows/outreach.yml`) will run automatically on Tuesday, Wednesday, and Thursday every hour during US morning hours, check which leads are in their 9:00-10:00 AM window, and execute the sends safely.
