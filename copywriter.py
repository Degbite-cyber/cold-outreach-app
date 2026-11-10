import json
import re
import requests
from typing import Dict, Any

class AICopywriter:
    """
    Generates personalized cold emails following Susana Otokpa's Prompt Playbook:
    - Under 100 words plain text
    - Zero em dashes (—), zero filler ("I hope you're well")
    - Genuine finding from company website
    - Starter offer for n8n/Make/Zapier lead automation
    - Low-friction yes/no closing question
    Primary: Google Gemini (gemini-3.8-flash / gemini-2.5-flash-lite)
    Fallback 1: Groq (openai/gpt-oss-120b or qwen/qwen3.8-27b)
    Fallback 2: Deterministic bulletproof template
    """

    def __init__(self, gemini_api_key: str = "", groq_api_key: str = "", sender_name: str = "Adegbite David"):
        self.gemini_api_key = gemini_api_key
        self.groq_api_key = groq_api_key
        self.sender_name = sender_name

    def generate_draft(self, business_name: str, first_name: str, site_summary: str) -> Dict[str, str]:
        prompt = self._build_prompt(business_name, first_name, site_summary)

        # 1. Try Gemini
        if self.gemini_api_key:
            for model in ["gemini-3.8-flash", "gemini-2.5-flash-lite", "gemini-2.5-flash"]:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_api_key}"
                    payload = {
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"responseMimeType": "application/json"}
                    }
                    res = requests.post(url, json=payload, timeout=12)
                    if res.status_code == 200:
                        data = res.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        return json.loads(text)
                except Exception:
                    continue

        # 2. Try Groq (with available models: openai/gpt-oss-120b, qwen/qwen3.8-27b)
        if self.groq_api_key:
            for g_model in ["openai/gpt-oss-120b", "qwen/qwen3.8-27b"]:
                try:
                    url = "https://api.groq.com/openai/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": g_model,
                        "messages": [
                            {"role": "system", "content": "You output only valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "response_format": {"type": "json_object"}
                    }
                    res = requests.post(url, headers=headers, json=payload, timeout=12)
                    if res.status_code == 200:
                        content = res.json()["choices"][0]["message"]["content"]
                        return json.loads(content)
                except Exception:
                    continue

        # 3. Deterministic Playbook Fallback
        name_clean = first_name if first_name else "there"
        return {
            "subject": f"quick question for {business_name}",
            "body": (
                f"Hi {name_clean},\n\n"
                f"I checked out {business_name} and noticed your customer intake flow. "
                f"I build automated pipelines using n8n and Make that connect lead forms directly to CRMs, "
                f"cutting down manual data entry and cutting lead response time to under 60 seconds.\n\n"
                f"Worth a 10-minute chat this Thursday to see if this fits your current setup?\n\n"
                f"Best,\n{self.sender_name}"
            )
        }

    def _build_prompt(self, business_name: str, first_name: str, site_summary: str) -> str:
        salutation = f"Hi {first_name}," if first_name else "Hi,"
        return f"""You are a senior cold outreach copywriter.
Write a personalized cold email from {self.sender_name} to {business_name}.
Target: Business owner or operations lead.
Service: Workflow automation using n8n, Make.com, and Zapier (connecting web forms, CRMs, booking tools to eliminate manual copy-pasting and follow up with leads in under 60 seconds).
Website text snippet:
\"\"\"{site_summary[:1000]}\"\"\"

CRITICAL RULES (Susana Otokpa Framework):
1. UNDER 100 WORDS total in body.
2. ZERO em dashes (—) or double hyphens (--).
3. No buzzwords, no hype, no fluff like "I hope you are well".
4. Line 1: Reference one genuine fact about their business or service and the workflow bottleneck it creates.
5. Lines 2-3: How an n8n or Make.com automation saves 10+ hours a week or speeds up client response times.
6. Closing: One simple, low-pressure yes/no question (e.g. "Worth a quick 10-minute chat this Thursday?").
7. Sign off: {self.sender_name}
8. Subject line: 3 to 5 lowercase words, sounds like an internal note, no hype.

Return ONLY a valid JSON object in this exact format:
{{
  "subject": "quick question regarding lead intake",
  "body": "{salutation}\\n\\n[body under 100 words]\\n\\nBest,\\n{self.sender_name}"
}}"""
