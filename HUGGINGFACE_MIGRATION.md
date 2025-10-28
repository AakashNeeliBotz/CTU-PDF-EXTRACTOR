# Migration from Ollama to Hugging Face Transformers

**Date**: 2025-10-24  
**Version**: 3.0  
**Status**: Ready for Testing

---

## 🎯 Overview

Migrated from Ollama API-based inference to **direct Hugging Face Transformers** with GPU acceleration for significantly faster processing.

## 🔧 Changes Made

### 1. Core Model Integration (`llm_data_extractor.py`)

**Before**: Used Ollama HTTP API (localhost:11434)
```python
requests.post(f"{OLLAMA_URL}/api/chat", json=payload)
```

**After**: Direct Hugging Face Transformers pipeline with GPU
```python
from transformers import pipeline

_llm_pipeline = pipeline(
    task="text-generation",
    model="google/gemma-3-4b-it",
    device=0,  # GPU
    torch_dtype=torch.bfloat16
)
```

**Key Features**:
- ✅ Lazy loading (model loads on first use)
- ✅ GPU auto-detection (CUDA if available, CPU fallback)
- ✅ VRAM monitoring and reporting
- ✅ Optimized parameters: `temperature=0.1`, `max_new_tokens=4096`
- ✅ Proper error handling and retry logic

### 2. Configuration Updates (`config.py`)

**Changed**:
```python
# Old
OLLAMA_MODEL = "gemma3:4b"
OLLAMA_URL = "http://localhost:11434"

# New
HF_MODEL = "google/gemma-3-4b-it"
```

### 3. Dependencies (`requirements.txt`)

**Added**:
- `transformers>=4.51.3` - Latest version with Gemma 3 support
- `torch>=2.4.0` - PyTorch for GPU acceleration
- `accelerate>=0.20.0` - Hugging Face GPU optimization
- `sentencepiece` - Tokenizer for Gemma models

**Removed**:
- `llama-cpp-python` - No longer needed

---

## 🚀 Setup Instructions

### Step 1: Install/Upgrade Dependencies

```bash
# Activate your virtual environment
myvenv\Scripts\activate

# Install new dependencies
pip install --upgrade -r requirements.txt

# For GPU support, ensure CUDA is installed
# Check: nvidia-smi
```

### Step 2: First Run (Model Download)

On first execution, the model will be downloaded (~8-9 GB):

```bash
python test_main_skip_download.py
```

**Expected output**:
```
[*] Loading Hugging Face model pipeline...
    This may take 1-2 minutes on first run (downloading ~8GB model)...
    [*] Using device: GPU (CUDA)
    [*] GPU: NVIDIA GeForce GTX 1080
    [*] VRAM Available: 8.00 GB
[+] Model pipeline loaded successfully!
```

### Step 3: Verify GPU Usage

During processing, you can monitor GPU usage:
```bash
# In another terminal
nvidia-smi -l 1
```

You should see:
- **GPU utilization**: 80-100%
- **Memory usage**: ~6-7 GB
- **Process**: python.exe

---

## 📊 Performance Improvements

### Expected Speed Gains (GTX 1080 8GB)

| Metric | Ollama (CPU) | Transformers (GPU) | Improvement |
|--------|--------------|-------------------|-------------|
| Model loading | N/A (always on) | 30-60s (one-time) | - |
| Single chunk (6000 chars) | 10-15s | 2-3s | **5x faster** |
| Single PDF (10 chunks) | 100-150s | 20-30s | **5x faster** |
| 10 PDFs | 20-30 min | 4-6 min | **5x faster** |
| 200 PDFs (production) | 6-10 hours | 1-2 hours | **5x faster** |

### Memory Usage

- **System RAM**: ~2-3 GB (Python + data)
- **VRAM**: ~6-7 GB (model + inference)
- **Total**: Well within GTX 1080 limits

---

## 🔍 Technical Details

### Model Specifications

- **Model ID**: `google/gemma-3-4b-it`
- **Type**: Instruction-tuned text generation
- **Parameters**: 4 billion
- **Architecture**: Gemma 3 (Decoder-only Transformer)
- **Precision**: bfloat16 (GPU), float32 (CPU fallback)
- **Context window**: 128K tokens (using ~6K per chunk)

### Generation Parameters

```python
max_new_tokens=4096      # Allow long JSON responses
temperature=0.1          # Low = more deterministic
do_sample=True           # Enable temperature control
return_full_text=False   # Don't echo prompt back
```

### Chat Format

Messages are formatted as:
```python
[
    {"role": "system", "content": "<optimized_prompt>"},
    {"role": "user", "content": "<pdf_chunk_text>"}
]
```

---

## ✅ Testing Checklist

- [ ] Dependencies installed successfully
- [ ] Model downloads on first run
- [ ] GPU detected and utilized
- [ ] Single PDF processes correctly
- [ ] Excel output contains data
- [ ] Extraction accuracy maintained
- [ ] Performance improvement confirmed
- [ ] No CUDA errors or OOM (out of memory)

---

## 🐛 Troubleshooting

### Issue: "CUDA out of memory"

**Solution**: Reduce chunk size in `main.py`:
```python
def chunk_text(text, max_chars=4000, overlap=100):  # Reduced from 6000
```

### Issue: "Model not found"

**Solution**: First run downloads model. Ensure internet connection:
```bash
# Manual download (optional)
from transformers import pipeline
pipeline("text-generation", model="google/gemma-3-4b-it")
```

### Issue: "torch not compiled with CUDA"

**Solution**: Install PyTorch with CUDA support:
```bash
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### Issue: Slower than expected

**Check**:
1. Confirm GPU is being used: `nvidia-smi`
2. Check if other apps are using GPU
3. Verify bfloat16 is enabled (check console output)
4. Close browser/games to free VRAM

---

## 🔄 Rollback (if needed)

If you need to revert to Ollama:

1. Restore old `llm_data_extractor.py` from git
2. Restore old `config.py` settings
3. Start Ollama service
4. Run pipeline as before

---

## 📝 Migration Checklist

- [x] Updated `llm_data_extractor.py` - Transformers implementation
- [x] Updated `config.py` - HF_MODEL configuration
- [x] Updated `requirements.txt` - New dependencies
- [x] Created migration documentation
- [ ] Tested on single PDF
- [ ] Tested on full pipeline
- [ ] Verified accuracy vs Ollama
- [ ] Updated PROJECT_DOCUMENTATION.md

---

## 🎓 Key Learnings

1. **Model Choice**: `google/gemma-3-4b-it` is the correct model for text generation (NOT `AutoModelForImageTextToText`)
2. **GPU Optimization**: `torch.bfloat16` reduces VRAM usage by 50% vs float32
3. **Lazy Loading**: Load model on-demand to avoid startup delays
4. **Chat Format**: Use message-based format for better instruction following
5. **Temperature**: 0.1 gives consistent JSON without sacrificing extraction quality

---

## 📚 References

- [Gemma 3 Hugging Face Docs](https://ai.google.dev/gemma/docs/core/huggingface_inference)
- [Transformers Pipeline API](https://huggingface.co/docs/transformers/main_classes/pipelines)
- [google/gemma-3-4b-it Model Card](https://huggingface.co/google/gemma-3-4b-it)

---

**End of Migration Guide**
