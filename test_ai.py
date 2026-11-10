import os
import requests
import json

def test_groq():
    key = "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"
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "Write a 1-sentence hello."}]
    }
    res = requests.post(url, headers=headers, json=payload, timeout=10)
    print("GROQ HTTP Status:", res.status_code)
    if res.status_code == 200:
        print("Groq Response:", res.json()["choices"][0]["message"]["content"])
    else:
        print("Groq Error:", res.text)

if __name__ == "__main__":
    test_groq()
