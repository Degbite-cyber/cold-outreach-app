import os
import requests

def test_gemini_38():
    with open(".env") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")
    
    key = os.environ.get("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": "Say 'Gemini 3.8 Flash working!'"}]}]
    }
    res = requests.post(url, json=payload, timeout=10)
    print("Gemini Status:", res.status_code)
    if res.status_code == 200:
        print("Gemini Output:", res.json()["candidates"][0]["content"]["parts"][0]["text"])
    else:
        print("Gemini Error:", res.text)

if __name__ == "__main__":
    test_gemini_38()
