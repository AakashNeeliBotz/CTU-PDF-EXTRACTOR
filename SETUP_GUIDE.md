# Complete Setup Guide - CTU PDF Extractor v3.0

**Date**: 2025-10-24  
**Version**: 3.0 - Hugging Face Transformers + Docling OCR  
**Hardware**: NVIDIA GTX 1080 (8GB VRAM)

---

## 🎯 Overview of Changes

This version replaces:
1. **Ollama** → **Hugging Face Transformers** (direct GPU inference)
2. **Nanonets OCR** → **Docling + Tesseract** (lightweight, efficient OCR)

**Benefits**:
- ✅ 5x faster LLM inference with GPU
- ✅ Much lighter OCR (no multi-GB model download)
- ✅ More reliable and maintainable
- ✅ All-in-one solution

---

## 📋 Prerequisites

### 1. System Requirements

- **OS**: Windows 10/11, macOS, or Linux
- **RAM**: 8GB minimum (16GB recommended)
- **GPU**: NVIDIA GTX 1080 (8GB VRAM) or better
- **Storage**: 15GB free space
- **Python**: 3.13 (already installed in your venv)

### 2. Required Software

#### A. NVIDIA CUDA Toolkit (for GPU acceleration)

**Check if installed**:
```bash
nvidia-smi
```

If not installed, download from:
- https://developer.nvidia.com/cuda-downloads
- Recommended: CUDA 11.8 or 12.1

#### B. Tesseract OCR Engine

Docling uses Tesseract for OCR. Install it separately:

**Windows**:
1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer (e.g., `tesseract-ocr-w64-setup-5.3.3.20231005.exe`)
3. Add to PATH: `C:\Program Files\Tesseract-OCR`
4. Verify: `tesseract --version`

**Set environment variable** (Windows):
```powershell
# In PowerShell (run as Administrator)
[Environment]::SetEnvironmentVariable("TESSDATA_PREFIX", "C:\Program Files\Tesseract-OCR\tessdata\", "Machine")
```

**macOS**:
```bash
brew install tesseract
export TESSDATA_PREFIX=/opt/homebrew/share/tessdata/
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata/
```

---

## 🔧 Installation Steps

### Step 1: Activate Virtual Environment

```bash
cd C:\Users\PT\code\CTU-PDF-EXTRACTOR
myvenv\Scripts\activate
```

### Step 2: Upgrade pip

```bash
python -m pip install --upgrade pip
```

### Step 3: Install PyTorch with CUDA Support

**For NVIDIA GPU (CUDA 11.8)**:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**For CUDA 12.1** (if you have newer CUDA):
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

**Verify GPU detection**:
```bash
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
```

Expected output:
```
CUDA Available: True
GPU: NVIDIA GeForce GTX 1080
```

### Step 4: Install All Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- **Hugging Face Transformers** (for LLM)
- **Docling** (for PDF parsing + OCR)
- **Accelerate** (GPU optimization)
- **All other project dependencies**

**Expected installation time**: 5-10 minutes

---

## 🧪 Testing

### Test 1: Verify Tesseract Installation

```bash
tesseract --version
```

Expected output:
```
tesseract 5.3.x
 leptonica-x.x.x
  ...
```

### Test 2: Verify Python Packages

```bash
python -c "import torch; import transformers; import docling; print('✓ All packages imported successfully')"
```

### Test 3: Test GPU + CUDA

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.version.cuda}'); print(f'cuDNN: {torch.backends.cudnn.version()}'); print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

Expected output:
```
PyTorch: 2.4.x
CUDA: 11.8 (or 12.1)
cuDNN: 8xxx
GPU: NVIDIA GeForce GTX 1080
```

### Test 4: Test PDF Processor with Docling

```bash
python pdf_processor.py
```

This will:
1. Find a PDF in `downloaded_pdfs/` folder
2. Extract text using PyMuPDF (digital) or Docling OCR (scanned)
3. Print first 1000 characters

**Expected output**:
```
--- PDF Processor initialized ---
--- Docling OCR available: True ---

--- Testing Docling PDF Processor ---
--- File: example.pdf ---

  [+] Successfully extracted text directly from 'example.pdf'.
  
--- Extracted Content (First 1000 Chars) ---
[... extracted text ...]
```

### Test 5: Test LLM with Hugging Face

Create a simple test:

```bash
python -c "from transformers import pipeline; print('Loading model...'); pipe = pipeline('text-generation', model='google/gemma-3-4b-it', device=0); print('✓ Model loaded successfully!')"
```

**Note**: First run will download ~8-9GB model (one-time, 5-10 minutes)

---

## 🚀 Running the Pipeline

### Option A: Test with Skip Download (Recommended First)

```bash
python test_main_skip_download.py
```

This will:
1. Skip scraping/downloading (use existing PDFs)
2. Process PDFs with Docling OCR (if scanned)
3. Extract data using Hugging Face Transformers
4. Write to Excel

**Expected first-run output**:
```
[*] Loading Hugging Face model pipeline...
    This may take 1-2 minutes on first run (downloading ~8GB model)...
    [*] Using device: GPU (CUDA)
    [*] GPU: NVIDIA GeForce GTX 1080
    [*] VRAM Available: 8.00 GB
[+] Model pipeline loaded successfully!

[*] Initializing Docling converter with Tesseract OCR...
[+] Docling converter initialized successfully!

[PHASE 3/4] Processing PDFs and extracting data...
...
```

### Option B: Full Pipeline (Scrape + Download + Process)

```bash
python main.py
```

---

## 📊 Performance Expectations

### With GPU (GTX 1080)

| Task | Expected Time |
|------|---------------|
| Model loading (first run) | 30-60 seconds |
| Single PDF chunk (6000 chars) | 2-3 seconds |
| Single PDF (10 chunks) | 20-30 seconds |
| 10 PDFs | 4-6 minutes |
| 200 PDFs (production) | 1-2 hours |

### GPU Utilization During Processing

Monitor with:
```bash
# In another terminal
nvidia-smi -l 1
```

Expected:
- **GPU Utilization**: 80-100%
- **VRAM Usage**: 6-7 GB
- **Temperature**: 60-80°C (varies by cooling)

---

## 🐛 Troubleshooting

### Issue 1: "Tesseract not found"

**Error**:
```
[!] ERROR initializing Docling: ...
```

**Solution**:
1. Install Tesseract (see Prerequisites)
2. Add to system PATH
3. Set `TESSDATA_PREFIX` environment variable
4. Restart terminal/IDE

**Verify**:
```bash
tesseract --version
echo %TESSDATA_PREFIX%  # Windows
```

### Issue 2: "CUDA out of memory"

**Error**:
```
RuntimeError: CUDA out of memory
```

**Solutions**:
1. Reduce chunk size in `main.py`:
   ```python
   def chunk_text(text, max_chars=4000, overlap=100):  # Reduced from 6000
   ```

2. Close other GPU applications (browsers, games)

3. Use CPU fallback (slower):
   ```python
   # In llm_data_extractor.py, temporarily disable GPU
   device = -1  # Force CPU
   ```

### Issue 3: "torch not compiled with CUDA"

**Error**:
```
AssertionError: Torch not compiled with CUDA enabled
```

**Solution**: Install CUDA-enabled PyTorch:
```bash
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Issue 4: Model download fails

**Error**:
```
HTTPError: 403 Forbidden
```

**Solution**: Hugging Face authentication
```bash
pip install huggingface-hub
huggingface-cli login
# Enter your token from: https://huggingface.co/settings/tokens
```

### Issue 5: Docling OCR produces no text

**Possible causes**:
1. PDF is encrypted/protected
2. Image quality too low
3. Tesseract language pack missing

**Solutions**:
1. Check PDF: `pdfinfo filename.pdf`
2. Install English language pack:
   ```bash
   # Windows: included in installer
   # Linux: sudo apt-get install tesseract-ocr-eng
   ```

3. Try forcing OCR in `pdf_processor.py`:
   ```python
   # Lower threshold to always use OCR
   if len(full_text.strip()) < 50:  # Changed from 100
   ```

---

## 🔄 Rollback to Previous Version

If you need to revert:

### Option 1: Git Restore
```bash
git checkout HEAD~1 -- llm_data_extractor.py pdf_processor.py config.py requirements.txt
```

### Option 2: Manual Restore
1. Restore Ollama settings in `config.py`
2. Restore old `llm_data_extractor.py` (Ollama API)
3. Restore old `pdf_processor.py` (Nanonets OCR)
4. Install Ollama and run: `ollama pull gemma3:4b`

---

## 📚 File Changes Summary

| File | Changes |
|------|---------|
| `llm_data_extractor.py` | Replaced Ollama API with HF Transformers pipeline |
| `pdf_processor.py` | Replaced Nanonets OCR with Docling + Tesseract |
| `config.py` | Added `HF_MODEL` config, removed Ollama settings |
| `requirements.txt` | Added `docling`, `accelerate`, `sentencepiece` |
| `HUGGINGFACE_MIGRATION.md` | Documentation for LLM migration |
| `SETUP_GUIDE.md` | This file - complete setup instructions |

---

## 🎓 Next Steps

1. ✅ Follow installation steps above
2. ✅ Run all tests to verify setup
3. ✅ Test with single PDF first
4. ✅ Run full pipeline on small dataset
5. ✅ Monitor GPU usage and performance
6. ✅ Validate Excel output accuracy
7. ✅ Run production dataset

---

## 📞 Support Resources

- **Docling Documentation**: https://docling-project.github.io/docling/
- **Hugging Face Transformers**: https://huggingface.co/docs/transformers
- **Tesseract OCR**: https://tesseract-ocr.github.io/
- **PyTorch CUDA**: https://pytorch.org/get-started/locally/

---

## ✅ Installation Checklist

- [ ] Python 3.13 virtual environment activated
- [ ] NVIDIA drivers installed (`nvidia-smi` works)
- [ ] CUDA Toolkit installed
- [ ] Tesseract OCR installed and in PATH
- [ ] `TESSDATA_PREFIX` environment variable set
- [ ] PyTorch with CUDA installed
- [ ] All Python dependencies installed (`pip install -r requirements.txt`)
- [ ] GPU detected by PyTorch
- [ ] Tesseract accessible from Python
- [ ] Test script runs successfully
- [ ] Model downloads successfully (first run)
- [ ] Excel output generated

---

**Good luck! 🚀**

If you encounter any issues not covered here, check the error messages carefully and refer to the troubleshooting section.
