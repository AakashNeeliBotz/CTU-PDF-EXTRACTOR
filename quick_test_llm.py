"""
Quick test to verify the LLM is working properly.
Tests with a tiny prompt and small input to isolate the issue.
"""

import torch
from transformers import pipeline
import time

print("=" * 60)
print("QUICK LLM TEST")
print("=" * 60)

# Check GPU
print(f"\n[*] CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"[*] GPU: {torch.cuda.get_device_name(0)}")

# Load model
print("\n[*] Loading model...")
start = time.time()

llm = pipeline(
    task="text-generation",
    model="google/gemma-3-4b-it",
    torch_dtype=torch.bfloat16,
    model_kwargs={
        "low_cpu_mem_usage": True,
        "device_map": "auto"
    }
)

load_time = time.time() - start
print(f"[+] Model loaded in {load_time:.1f}s")

# Test generation
print("\n[*] Testing generation with small prompt...")
test_prompt = "Extract the person's name and age from this text: 'John Smith is 35 years old.' Return as JSON."

start = time.time()
output = llm(
    test_prompt,
    max_new_tokens=100,  # Very small
    temperature=0.1,
    do_sample=True,
    return_full_text=False
)
gen_time = time.time() - start

print(f"[+] Generated in {gen_time:.1f}s")
print(f"\nOutput: {output[0]['generated_text']}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print(f"\nIf this worked quickly (< 30s generation), the model is fine.")
print(f"If it was slow (> 60s), there may be a GPU/CUDA issue.")
