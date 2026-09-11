"""
Gemini API client helper for ITVedas automation.
Supports GEMINI_API_KEY with gemini-2.5-flash model via standard library
urllib.request so it requires zero external dependencies and runs reliably.
"""
import os
import json
import urllib.request
import urllib.error

def generate_text(prompt, system_instruction=None, max_tokens=8192):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Fallback to ANTHROPIC_API_KEY if present
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=anthropic_key, timeout=180.0)
                msg = client.messages.create(
                    model='claude-sonnet-5',
                    max_tokens=max_tokens,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                return msg.content[0].text.strip()
            except Exception as e:
                print(f"Anthropic fallback error: {e}")
        print("Warning: Neither GEMINI_API_KEY nor ANTHROPIC_API_KEY is configured.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
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
