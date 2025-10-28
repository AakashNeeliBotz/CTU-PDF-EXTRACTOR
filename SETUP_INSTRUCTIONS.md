# Setup Instructions

## Installation Steps

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR (for Docling)

**Windows:**
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (tesseract-ocr-w64-setup-5.3.x.exe)
3. During installation, note the installation path (default: `C:\Program Files\Tesseract-OCR`)
4. Add Tesseract to PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" under System variables
   - Add: `C:\Program Files\Tesseract-OCR`
5. Set TESSDATA_PREFIX:
   - Add new System variable: `TESSDATA_PREFIX`
   - Value: `C:\Program Files\Tesseract-OCR\tessdata`
6. Restart your terminal/IDE

**Verify Installation:**
```bash
tesseract --version
```

### 3. Install Ghostscript (Optional, for Camelot lattice mode)

**Windows:**
1. Download from: https://ghostscript.com/releases/gsdnld.html
2. Install the 64-bit version
3. Add to PATH: `C:\Program Files\gs\gs10.xx.x\bin`

**Without Ghostscript:**
- Camelot will use 'stream' flavor (less accurate but works)

### 4. Install PyTorch with CUDA (for GPU acceleration)

Already installed if you followed previous steps. Verify:

```bash
python check_cuda.py
```

Should show:
- CUDA available: True
- GPU: NVIDIA GeForce GTX 1080

## Troubleshooting

### Docling Import Error

If you see:
```
ImportError: cannot import name 'DocumentConverter' from 'docling.document_converter'
```

Try:
```bash
pip uninstall docling
pip install docling --no-cache-dir
```

### Camelot Ghostscript Error

If you see:
```
Ghostscript not found
```

Either:
1. Install Ghostscript (recommended)
2. The script will automatically fall back to 'stream' flavor

### Tesseract Not Found

If you see:
```
Tesseract is not installed or it's not in your PATH
```

1. Verify installation: `tesseract --version`
2. Check PATH includes Tesseract directory
3. Check TESSDATA_PREFIX is set correctly
4. Restart terminal/IDE after setting environment variables

##Keys to Success

- **Camelot**: Works best with tabular PDFs with clear table structures
- **PyMuPDF**: Fast for digital PDFs with selectable text
- **Docling OCR**: For scanned/image-based PDFs (slowest but most comprehensive)

The pipeline will automatically choose the best method for each PDF!
