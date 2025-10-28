# Quick Test Setup - CTU PDF Extractor v3.0

**Before running the test, follow these simple steps:**

---

## 📁 Step 1: Place Your Test PDFs

You mentioned you have **2 PDFs ready**. Place them in one of these folders:

### Option A: Use SN3 folder (Recommended)
```
downloaded_pdfs/SN3/
```

**Why SN3?** 
- SN3 is used by the "Data to be captured" sheet (default test sheet)
- Easiest for testing

### Option B: Use any of these folders
The "Data to be captured" sheet accepts PDFs from any of these sources:
```
downloaded_pdfs/SN1/
downloaded_pdfs/SN2/
downloaded_pdfs/SN3/  ← Recommended
downloaded_pdfs/SN4/
downloaded_pdfs/SN7/
downloaded_pdfs/SN8/
downloaded_pdfs/SN9/
downloaded_pdfs/SN11/
```

**The test script will auto-detect** whichever folder has PDFs!

---

## 🔧 Step 2: Ensure Prerequisites Installed

### Check 1: Tesseract OCR
```bash
tesseract --version
```

✅ If you see version info → Good!  
❌ If "command not found" → Install from: https://github.com/UB-Mannheim/tesseract/wiki

### Check 2: Python Packages
```bash
# Activate virtual environment
myvenv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Check 3: GPU Detection
```bash
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

✅ If `CUDA: True` → GPU ready!  
⚠️ If `CUDA: False` → Will use CPU (slower, but works)

---

## 🚀 Step 3: Run the Test

```bash
# Make sure you're in the project directory
cd C:\Users\PT\code\CTU-PDF-EXTRACTOR

# Activate virtual environment
myvenv\Scripts\activate

# Run test script
python test_main_skip_download.py
```

---

## 📝 What to Expect

### First Run (one-time setup)
```
[*] Loading Hugging Face model pipeline...
    This may take 1-2 minutes on first run (downloading ~8GB model)...
    [*] Using device: GPU (CUDA)
    [*] GPU: NVIDIA GeForce GTX 1080
    [*] VRAM Available: 8.00 GB
[+] Model pipeline loaded successfully!
```

**⏱️ Time**: ~5-10 minutes (downloads Gemma 3 4B model)

### Subsequent Runs
```
[*] Auto-detecting source folder with PDFs...
    [+] Found 2 PDF(s) in SN3
[*] Using source: SN3

  [*] Reading PDFs from source: SN3
  [+] Found 2 PDF(s) to process (limited to 2 for testing):
      - your_pdf_1.pdf
      - your_pdf_2.pdf

    - Processing file: your_pdf_1.pdf
      [+] Successfully extracted text directly from 'your_pdf_1.pdf'.
      [*] Split into 3 chunks
      [*] Chunk 1/3 sending to LLM (len=6000)...
      [+] Chunk 1: 5 records.
      ...

  [*] Total records collected: 12
  [+] Successfully wrote data to 'Data to be captured'
  
[+] Output file: Connectivity_Application_Data_TEST_SN3_betterPrompts.xlsx
```

**⏱️ Time**: ~2-4 minutes per PDF (with GPU)

---

## 📊 Expected Output

After successful run, you'll find:

**Excel File**: `Connectivity_Application_Data_TEST_SN3_betterPrompts.xlsx`

**Open it and check**:
- Sheet: "Data to be captured"
- Data should start at row 3, column B
- Should contain 35 columns (all fields)
- Records extracted from your PDFs

---

## 🐛 Common Issues

### Issue 1: "No PDFs found in any source folder"

**Solution**: 
```bash
# Check if you created the folder
dir downloaded_pdfs\SN3

# If not, create it
mkdir downloaded_pdfs\SN3

# Copy your PDFs there
copy "C:\path\to\your\test.pdf" "downloaded_pdfs\SN3\"
```

### Issue 2: "Tesseract not found"

**Solution**:
1. Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. Add to PATH
3. Restart terminal

### Issue 3: "CUDA out of memory"

**Solution**: Edit `test_main_skip_download.py`, reduce chunk size:
```python
def chunk_text(text, max_chars=4000, overlap=100):  # Reduced from 6000
```

### Issue 4: Model download slow/fails

**Solution**:
- Ensure stable internet connection
- Model is ~8GB, takes 5-10 min
- Download happens only once
- Files cached in: `~/.cache/huggingface/`

---

## ✅ Quick Checklist

Before running test:
- [ ] 2 PDFs placed in `downloaded_pdfs/SN3/` (or any supported folder)
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Tesseract installed and in PATH
- [ ] PyTorch with CUDA installed (for GPU)
- [ ] Template file exists: `Connectivity Application Data.xlsx`

---

## 🎯 Ready to Test!

Once checklist is complete, simply run:

```bash
python test_main_skip_download.py
```

The script will:
1. ✅ Auto-detect your PDFs
2. ✅ Load the model (downloads first time)
3. ✅ Extract text (PyMuPDF or Docling OCR)
4. ✅ Run LLM extraction (GPU-accelerated)
5. ✅ Write to Excel

**Output**: `Connectivity_Application_Data_TEST_SN3_betterPrompts.xlsx`

---

**Good luck! 🚀**
