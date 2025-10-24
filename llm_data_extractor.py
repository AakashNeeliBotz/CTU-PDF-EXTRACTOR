import os
import json
import requests
from typing import Any
from config import OLLAMA_MODEL, OLLAMA_URL

# --- Ollama-only Configuration ---
# We will use the Ollama HTTP API exclusively for LLM inference.
print(f"[+] Targeting Ollama model '{OLLAMA_MODEL}' at {OLLAMA_URL}.")

SYSTEM_PROMPT = """
You are a structured data extractor. Read the text and return a single JSON object with key "extracted_data" as a list of records. Use null for missing values.
"""

def _ollama_chat(text_content: str, system_prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text_content}
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,  # Lower temperature for more deterministic output
            "num_predict": 4096  # Allow longer responses for large JSON
        }
    }
    # Note: Removed "format": "json" as it causes 500 errors with gemma3:4b
    try:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=600)
        r.raise_for_status()
        body: Any = r.json()
        return body.get("message", {}).get("content", "")
    except requests.exceptions.HTTPError as e:
        print(f"[!] HTTP Error {e.response.status_code}: {e.response.text[:200]}")
        raise


def _strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        # Remove leading and trailing triple backticks blocks
        parts = s.split("```")
        # Heuristic: return the largest segment
        return max(parts, key=len).strip()
    return s


def _extract_json_text(s: str) -> str:
    """Extract a JSON-looking substring from the response."""
    s = _strip_code_fences(s)
    s = s.strip()
    # If it already starts with { or [, use as-is
    if s.startswith("{") or s.startswith("["):
        return s
    # Fallback: find first '{' and last '}' or '[' and ']'
    start_obj = s.find("{")
    end_obj = s.rfind("}")
    start_arr = s.find("[")
    end_arr = s.rfind("]")
    candidates = []
    if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
        candidates.append(s[start_obj:end_obj+1])
    if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
        candidates.append(s[start_arr:end_arr+1])
    if candidates:
        # Pick longest candidate
        return max(candidates, key=len)
    # As last resort, return original string (will likely fail)
    return s


def _normalize_structured(obj: Any) -> dict | None:
    """Coerce various JSON shapes into {"extracted_data": [...]}."""
    try:
        if isinstance(obj, dict):
            data = obj.get("extracted_data")
            if isinstance(data, list):
                return {"extracted_data": data}
            # Look for any list value that looks like records
            for v in obj.values():
                if isinstance(v, list):
                    if not v or isinstance(v[0], dict):
                        return {"extracted_data": v}
            # Treat the dict itself as a single record
            return {"extracted_data": [obj]}
        if isinstance(obj, list):
            return {"extracted_data": obj}
        return None
    except Exception:
        return None


def extract_structured_data(text_content: str, system_prompt: str | None = None):
    """
    Sends the extracted text to the Ollama server to get structured data back.
    """
    if not text_content:
        print("[!] Text content is empty. Skipping LLM extraction.")
        return None

    print("[*] Sending text to Ollama for data extraction...")
    response_content: str = ""
    try:
        effective_prompt = system_prompt if system_prompt is not None else SYSTEM_PROMPT
        response_content = _ollama_chat(text_content, effective_prompt)

        if not response_content:
            print("[!] Empty response from Ollama.")
            return None

        json_text = _extract_json_text(response_content)
        raw_obj = json.loads(json_text)
        structured_data = _normalize_structured(raw_obj)
        if structured_data is None or not isinstance(structured_data.get("extracted_data"), list):
            print("[!] Ollama returned JSON, but not in expected shape. Normalization failed.")
            return None

        print("[+] Successfully extracted structured data.")
        return structured_data

    except json.JSONDecodeError:
        print("[!] Failed to decode JSON from the Ollama response.")
        print(f"    Raw response: {response_content}")
        return None
    except requests.RequestException as e:
        print(f"[!] HTTP error when calling Ollama: {e}")
        return None
    except Exception as e:
        print(f"[!] An unexpected error occurred during Ollama extraction: {e}")
        return None
