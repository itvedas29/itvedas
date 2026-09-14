"""
Gemini API client helper for ITVedas automation.
Supports GEMINI_API_KEY with gemini-2.5-flash model via standard library
urllib.request so it requires zero external dependencies and runs reliably.
"""
import os
import json
import urllib.request
import urllib.error

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

def generate_text(prompt, system_instruction=None, max_tokens=8192, temperature=0.7):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Warning: GEMINI_API_KEY is not configured in environment.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": min(max_tokens, 8192)
        }
    }
    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            candidates = result.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    except Exception as e:
        print(f"Gemini API call error: {e}")
        return None
