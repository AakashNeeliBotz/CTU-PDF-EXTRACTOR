# CTU Automated PDF Data Extraction Pipeline

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Automated extraction of structured data from Indian government energy sector PDF documents using AI-powered semantic extraction. Scrapes 14+ data sources, processes PDFs (digital + scanned), and generates multi-sheet Excel reports.

## 🚀 Features

- **AI-Powered Extraction**: Uses Ollama (gemma3:4b) for semantic understanding, not just keyword matching
- **Multi-Format Support**: Handles both digital PDFs and scanned documents (OCR)
- **14 Data Sources**: Automatically scrapes CTU, CEA, PFCCL, and RECPDCL websites
- **5 Excel Sheets**: Generates comprehensive reports with 90+ structured fields
- **Optimized Performance**: 80% smaller prompts (v2.1), faster processing
- **Sheet-First Architecture**: Easy to configure and extend

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Performance](#performance)
- [Contributing](#contributing)

---

## 🔧 Prerequisites

### Required Software

1. **Python 3.13** or higher
   - Download from [python.org](https://www.python.org/downloads/)
   - Ensure `pip` is installed

2. **Ollama** with gemma3:4b model
   - Download Ollama from [ollama.com](https://ollama.com)
   - Install and start the Ollama application
   - Pull the required model (see installation steps)

3. **Git** (optional, for version control)
   - Download from [git-scm.com](https://git-scm.com/)

### System Requirements

- **OS**: Windows 10/11, macOS, or Linux
- **RAM**: 8 GB minimum (16 GB recommended for OCR)
- **Disk**: 10 GB free space (for models and PDFs)
- **CPU**: Multi-core processor (GPU optional but recommended)

---

## 📦 Installation

### Step 1: Clone or Download the Repository

```bash
# Option 1: Clone with Git
git clone <repository-url>
cd CTU-automated-pdf-extraction

# Option 2: Download and extract ZIP
# Then navigate to the extracted folder
```

### Step 2: Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv myvenv

# Activate virtual environment
# On Windows:
myvenv\Scripts\activate.bat

# On macOS/Linux:
source myvenv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# This will install:
# - PyMuPDF (PDF processing)
# - transformers, torch (OCR model)
# - requests, beautifulsoup4 (web scraping)
# - pandas, openpyxl (Excel handling)
# - and more...
```

### Step 4: Install and Configure Ollama

```bash
# 1. Install Ollama application (if not already installed)
# Download from: https://ollama.com

# 2. Start Ollama (it should start automatically after installation)

# 3. Pull the gemma3:4b model
ollama pull gemma3:4b

# 4. Verify the model is installed
ollama list
# Should show: gemma3:4b

# 5. Test Ollama is running
curl http://localhost:11434/api/tags
# Should return JSON with available models
```

### Step 5: Verify Installation

```bash
# Check Python version
python --version
# Should show: Python 3.13.x

# Check if all packages installed
pip list | grep -E "(PyMuPDF|transformers|requests|pandas|openpyxl)"

# On Windows PowerShell:
pip list | Select-String -Pattern "PyMuPDF|transformers|requests|pandas|openpyxl"
```

---

## ⚙️ Configuration

### 1. Data Sources Configuration

Edit `config.py` to configure which data sources to scrape:

```python
# config.py

# Available sources (already configured):
DATA_SOURCES = {
    "SN1": "https://ctuil.in/ists-consultation-meeting",  # CMETS meetings
    "SN2": "https://ctuil.in/ists-joint-coordination-meeting",  # JCC meetings
    "SN3": "https://www.ctuil.in/regenerators",  # RE generator status
    "SN4": "https://www.ctuil.in/reallocation_meetings",  # Re-allocation
    # ... and 10 more sources
}
```

### 2. Sheet Configuration

Configure which Excel sheets to populate and their data sources:

```python
# config.py

SHEET_CONFIG = {
    "Data to be captured": {
        "sources": ["SN1", "SN2", "SN3", "SN4", "SN7", "SN8", "SN9", "SN11"],
        "prompt": PROMPT_DATA_TO_BE_CAPTURED
    },
    # Add other sheets as needed:
    # "RE Potential": {
    #     "sources": ["SN9", "SN10a"],
    #     "prompt": PROMPT_RE_POTENTIAL
    # },
    # ... etc.
}
```

### 3. Processing Parameters

Adjust performance settings in `main.py`:

```python
# main.py

MAX_WORKERS = 2  # Number of parallel PDF processes (increase for faster processing)
chunk_size = 6000  # Characters per LLM chunk
overlap = 100  # Character overlap between chunks
```

---

## 🎯 Usage

### Basic Usage

#### 1. Run the Full Pipeline

This will scrape all configured sources, download PDFs, extract data, and generate Excel output:

```bash
# Make sure virtual environment is activated
python main.py
```

**Output**: `Connectivity_Application_Data_OUTPUT2.xlsx`

#### 2. Test with Existing PDFs (Skip Download)

If you already have PDFs in `downloaded_pdfs/` folder:

```bash
# Process only existing PDFs (no scraping/downloading)
python test_main_skip_download.py
```

This is useful for:
- Testing LLM extraction
- Re-processing existing PDFs with updated prompts
- Faster iteration during development

### Advanced Usage

#### Process Specific Data Sources Only

Edit `config.py` temporarily:

```python
SHEET_CONFIG = {
    "Data to be captured": {
        "sources": ["SN4"],  # Only process SN4
        "prompt": PROMPT_DATA_TO_BE_CAPTURED
    }
}
```

Then run:
```bash
python main.py
```

#### Check Ollama Status

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# On Windows PowerShell:
Invoke-WebRequest -Uri http://localhost:11434/api/tags
```

#### View Downloaded PDFs

PDFs are organized by source:
```
downloaded_pdfs/
├── SN1/  # CMETS meeting PDFs
├── SN2/  # JCC meeting PDFs
├── SN3/  # RE generator status PDFs
├── SN4/  # Re-allocation meeting PDFs
└── ...
```

---

## 📁 Project Structure

```
CTU-automated-pdf-extraction/
│
├── main.py                          # Main pipeline orchestrator
├── config.py                        # Configuration (sources, sheets, settings)
├── prompts.py                       # LLM extraction prompts (optimized v2.1)
│
├── scraper.py                       # Web scraping logic
├── downloader.py                    # PDF download handler
├── pdf_processor.py                 # Text extraction + OCR
├── llm_data_extractor.py           # Ollama LLM integration (fixed v2.1)
├── excel_handler.py                 # Excel output writer
│
├── test_main_skip_download.py      # Test script (skip scraping)
├── requirements.txt                 # Python dependencies
├── .gitignore                       # Git ignore rules
├── README.md                        # This file
│
├── Connectivity Application Data.xlsx           # Template (input)
├── Connectivity_Application_Data_OUTPUT2.xlsx  # Generated output
│
├── downloaded_pdfs/                 # Downloaded PDFs by source
│   ├── SN1/, SN2/, ..., SN14/
│
├── myvenv/                          # Virtual environment (gitignored)
│
└── Documentation/
    ├── PROJECT_DOCUMENTATION.md     # Detailed technical documentation
    ├── FIX_SUMMARY.md              # v2.1 fixes documentation
    └── prd2.txt                    # Product requirements
```

---

## 🔍 How It Works

### Pipeline Phases

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   PHASE 1   │───▶│   PHASE 2    │───▶│   PHASE 3   │───▶│   PHASE 4    │
│  Scraping   │    │ Downloading  │    │ Processing  │    │Excel Writing │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
      │                   │                    │                   │
  Find PDF            Save PDFs          Extract Data         Write to
   links              by source           via LLM              Excel
```

**Phase 1: Scraping**
- Visits configured government websites
- Finds all PDF download links
- Handles direct PDF URLs

**Phase 2: Downloading**
- Downloads PDFs to `downloaded_pdfs/{source_id}/`
- Skips existing files (caching)
- Respects rate limits (1 second delay)

**Phase 3: Processing**
- Extracts text from PDFs (PyMuPDF for digital, OCR for scanned)
- Chunks text (6000 chars, 100 overlap)
- Sends chunks to Ollama LLM
- Extracts structured JSON data
- Aggregates results per PDF

**Phase 4: Excel Writing**
- Appends extracted records to appropriate Excel sheet
- Preserves template formatting
- Generates final output file

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Connection refused (Ollama)"

**Problem**: Ollama server is not running

**Solution**:
```bash
# Start Ollama application
# Windows: Launch from Start Menu
# macOS: Open Ollama.app
# Linux: ollama serve

# Verify it's running:
curl http://localhost:11434/api/tags
```

#### 2. "Model 'gemma3:4b' not found"

**Problem**: LLM model not installed

**Solution**:
```bash
ollama pull gemma3:4b
ollama list  # Verify installation
```

#### 3. Empty Excel Output

**Problem**: LLM extraction failed or returned no data

**Solutions**:
- Check terminal for error messages
- Verify Ollama is responding: `curl http://localhost:11434/api/tags`
- Ensure you're using optimized prompts (v2.1)
- Check if PDFs actually contain relevant data

#### 4. OCR Model Loading Fails

**Problem**: Insufficient memory or corrupted download

**Solutions**:
- Close other applications to free memory
- Delete cached model and re-download:
  ```bash
  # Clear Hugging Face cache
  rm -rf ~/.cache/huggingface/transformers/
  # Re-run pipeline
  ```
- Skip scanned PDFs temporarily (process digital PDFs only)

#### 5. Import Errors

**Problem**: Missing Python packages

**Solution**:
```bash
# Ensure virtual environment is activated
myvenv\Scripts\activate.bat  # Windows
source myvenv/bin/activate   # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

#### 6. Slow Processing

**Problem**: CPU-based LLM inference is slow

**Solutions**:
- Reduce `MAX_WORKERS` to 1 to avoid CPU overload
- Reduce chunk size from 6000 to 4000
- Process fewer sources at a time
- Consider GPU acceleration (requires CUDA setup)

---

## ⚡ Performance

### Benchmarks (CPU)

| Scenario | Time | Notes |
|----------|------|-------|
| Single digital PDF (10 pages) | ~3 minutes | Mainly LLM inference |
| Single scanned PDF (5 pages) | ~6 minutes | OCR + LLM |
| 10 PDFs (mixed) | 20-30 minutes | With MAX_WORKERS=2 |
| 200 PDFs (production) | 6-10 hours | Full pipeline |

### Optimization Tips

1. **Increase Parallel Workers**:
   ```python
   MAX_WORKERS = 4  # In main.py (if you have 8+ CPU cores)
   ```

2. **Reduce Chunk Size** (fewer LLM calls):
   ```python
   chunk_size = 8000  # Larger chunks (risky with context limits)
   overlap = 50  # Less overlap
   ```

3. **Skip OCR** for digital-only PDFs

4. **Use GPU** (5-10x faster):
   - Install CUDA
   - Use GPU-enabled Ollama
   - Expected: 1-2 hours for 200 PDFs

---

## 📊 Output

### Excel Sheets Generated

| Sheet Name | Fields | Data Sources |
|------------|--------|--------------|
| Data to be captured | 35 | SN1, SN2, SN3, SN4, SN7, SN8, SN9, SN11 |
| RE Potential | 16 | SN9, SN10a |
| Margin | 12 | SN9 |
| Transformation Capacity | 7 | SN9 |
| Element Status | 20 | SN10b, SN10c, SN10d |

### Sample Output Fields

**Data to be captured sheet**:
- Application ID, Developer Name, State, Region
- Capacity (MW), Project Type (Solar/Wind/Hybrid)
- Meeting dates, Approval status
- Coordinates, Substation details
- And 25+ more fields...

---

## 🔄 Updates & Changelog

### v2.1 (2025-10-23) - Current
- ✅ Optimized prompts (80% size reduction)
- ✅ Fixed Ollama 500 errors (removed `"format": "json"`)
- ✅ Improved accuracy with retained field disambiguation
- ✅ Better error handling in LLM extraction

### v2.0 (2025-10-21)
- Migrated from llama.cpp to Ollama
- Sheet-first architecture
- Multi-source support (14 sources)
- OCR integration for scanned PDFs

---

## 📝 Configuration Reference

### Environment Variables (Optional)

Create a `.env` file for custom settings:

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
MAX_WORKERS=2
CHUNK_SIZE=6000
OVERLAP=100
```

### Prompt Customization

Edit `prompts.py` to customize extraction behavior:

```python
# prompts.py

PROMPT_DATA_TO_BE_CAPTURED = """
Your custom extraction instructions here...
"""
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🆘 Support

For issues, questions, or feature requests:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) for detailed technical docs
3. Open an issue on the repository

---

## 🙏 Acknowledgments

- **Ollama** - For local LLM inference
- **Google Gemma** - For the gemma3:4b model
- **PyMuPDF** - For PDF text extraction
- **HuggingFace** - For OCR models and transformers

---

**Built with ❤️ for automating regulatory data extraction**
