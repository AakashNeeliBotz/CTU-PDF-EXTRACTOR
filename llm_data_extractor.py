import os
import csv
import io
import json
import torch
from typing import Any, List, Dict
from transformers import pipeline
from config import HF_MODEL

# --- Hugging Face Transformers Configuration ---
# Using Hugging Face Transformers for direct model inference with GPU acceleration
print(f"[+] Initializing Hugging Face Transformers with model '{HF_MODEL}'...")

# Global pipeline instance (lazy-loaded)
_llm_pipeline = None
_pipeline_load_failed = False

SYSTEM_PROMPT = """
You are a structured data extractor. Read the text and return CSV format with a header row. Use empty values for missing data.
"""

def _ensure_pipeline_loaded():
    """Load the Hugging Face pipeline on-demand (lazy loading)."""
    global _llm_pipeline, _pipeline_load_failed
    
    if _pipeline_load_failed:
        print("[!] Pipeline loading previously failed, skipping retry.")
        return False
    
    if _llm_pipeline is not None:
        return True
    
    try:
        print("[*] Loading Hugging Face model pipeline...")
        print("    This may take 1-2 minutes on first run (downloading ~8GB model)...")
        
        # Check GPU availability
        use_gpu = torch.cuda.is_available()
        device_name = "GPU (CUDA)" if use_gpu else "CPU"
        print(f"    [*] Using device: {device_name}")
        
        if use_gpu:
            print(f"    [*] GPU: {torch.cuda.get_device_name(0)}")
            print(f"    [*] VRAM Available: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
        
        # Load pipeline with optimized settings
        # Note: When using device_map="auto", we cannot specify device parameter
        if use_gpu:
            _llm_pipeline = pipeline(
                task="text-generation",
                model=HF_MODEL,
                torch_dtype=torch.bfloat16,
                model_kwargs={
                    "low_cpu_mem_usage": True,
                    "device_map": "auto"  # Automatically places model on GPU
                }
            )
        else:
            _llm_pipeline = pipeline(
                task="text-generation",
                model=HF_MODEL,
                device=-1,  # CPU
                torch_dtype=torch.float32,
                model_kwargs={
                    "low_cpu_mem_usage": True
                }
            )
        
        print("[+] Model pipeline loaded successfully!")
        return True
        
    except KeyboardInterrupt:
        print("\n[!] Pipeline loading interrupted by user.")
        _llm_pipeline = None
        _pipeline_load_failed = True
        return False
    except Exception as e:
        print(f"[!] CRITICAL ERROR loading pipeline: {e}")
        print(f"[!] Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        _llm_pipeline = None
        _pipeline_load_failed = True
        return False

def _hf_generate(text_content: str, system_prompt: str) -> str:
    """Generate text using Hugging Face Transformers pipeline."""
    success = _ensure_pipeline_loaded()
    if not success or _llm_pipeline is None:
        raise RuntimeError("Pipeline not available. Cannot generate text.")
    
    try:
        # Construct messages in chat format
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text_content}
        ]
        
        print("    [*] Generating response (30-60 seconds expected)...")
        import time
        start_time = time.time()
        
        # Generate with optimized parameters
        outputs = _llm_pipeline(
            messages,
            max_new_tokens=1024,  # Reduced for faster generation (was 2048)
            temperature=0.1,      # More deterministic output
            do_sample=True,       # Enable sampling for temperature to work
            pad_token_id=_llm_pipeline.tokenizer.eos_token_id,  # Avoid warnings
            return_full_text=False,  # Return only generated text, not prompt
            # Add early stopping
            eos_token_id=_llm_pipeline.tokenizer.eos_token_id,
        )
        
        elapsed = time.time() - start_time
        print(f"    [+] Response generated in {elapsed:.1f}s!")
        
        print("    [+] Response generated!")
        
        # Extract generated text from pipeline output
        if outputs and len(outputs) > 0:
            generated = outputs[0].get("generated_text", "")
            return generated if isinstance(generated, str) else str(generated)
        
        return ""
        
    except Exception as e:
        print(f"[!] Error during text generation: {e}")
        raise


def _strip_code_fences(s: str) -> str:
    """Remove markdown code fences from response."""
    s = s.strip()
    if s.startswith("```"):
        # Remove leading and trailing triple backticks blocks
        lines = s.split('\n')
        # Remove first line if it's ```csv or ```
        if lines[0].startswith('```'):
            lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        return '\n'.join(lines).strip()
    return s


def _parse_csv_to_records(csv_text: str) -> List[Dict[str, Any]]:
    """Parse CSV text into list of dictionaries."""
    try:
        csv_text = _strip_code_fences(csv_text)
        
        # Use csv.DictReader to parse CSV
        csv_file = io.StringIO(csv_text)
        reader = csv.DictReader(csv_file)
        
        records = []
        for row in reader:
            # Clean up the record - remove empty strings, convert to None
            cleaned_row = {}
            for key, value in row.items():
                if value is None or value.strip() == '':
                    cleaned_row[key] = None
                else:
                    # Try to convert numeric values
                    cleaned_value = value.strip()
                    # Try integer
                    try:
                        if '.' not in cleaned_value:
                            cleaned_row[key] = int(cleaned_value)
                        else:
                            cleaned_row[key] = float(cleaned_value)
                    except ValueError:
                        # Keep as string
                        cleaned_row[key] = cleaned_value
            
            records.append(cleaned_row)
        
        return records
    
    except Exception as e:
        print(f"[!] Error parsing CSV: {e}")
        print(f"    CSV text preview: {csv_text[:200]}...")
        return []


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
    Sends the extracted text to the Hugging Face model to get structured data back.
    Now expects CSV output from the model.
    """
    if not text_content:
        print("[!] Text content is empty. Skipping LLM extraction.")
        return None

    print("[*] Sending text to Hugging Face model for data extraction...")
    response_content: str = ""
    try:
        effective_prompt = system_prompt if system_prompt is not None else SYSTEM_PROMPT
        response_content = _hf_generate(text_content, effective_prompt)

        if not response_content:
            print("[!] Empty response from model.")
            return None

        # Parse CSV response
        records = _parse_csv_to_records(response_content)
        
        if not records:
            print("[!] Model returned text, but no valid CSV records found.")
            print(f"    Response preview: {response_content[:300]}...")
            return None

        print(f"[+] Successfully extracted {len(records)} records from CSV.")
        
        # Return in the same format as before for compatibility
        return {"extracted_data": records}

    except RuntimeError as e:
        print(f"[!] Runtime error during extraction: {e}")
        return None
    except Exception as e:
        print(f"[!] An unexpected error occurred during extraction: {e}")
        import traceback
        traceback.print_exc()
        return None
