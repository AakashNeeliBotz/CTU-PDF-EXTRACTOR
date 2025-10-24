import os
import fitz  # PyMuPDF
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
import io

# --- Configuration ---
# Check for GPU availability for faster processing, otherwise use CPU.
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"--- Using device: {DEVICE} ---")

# --- Lazy OCR Model Loader ---
processor = None
model = None
ocr_load_failed = False  # Track if OCR loading failed to avoid retry loops

def _ensure_ocr_loaded():
    """Load OCR model on-demand only when needed (skip if already loaded)."""
    global processor, model, ocr_load_failed
    
    # If we already tried and failed, don't retry
    if ocr_load_failed:
        print("[!] OCR loading previously failed, skipping retry.")
        return False
    
    if processor is not None and model is not None:
        print("[*] OCR model already loaded, reusing...")
        return True
    
    try:
        print("[*] Loading Nanonets OCR model on-demand...")
        print("    This may take 1-3 minutes on CPU...")
        model_id = "nanonets/Nanonets-OCR-s"
        
        # Load processor first
        print("    [1/3] Loading processor...")
        processor = AutoProcessor.from_pretrained(
            model_id, 
            trust_remote_code=True, 
            use_fast=False,
            local_files_only=False  # Allow download if needed
        )
        
        # Load model with explicit settings
        print("    [2/3] Loading model checkpoint shards (this is slow on CPU)...")
        compute_dtype = torch.bfloat16 if DEVICE == "cuda" else torch.float32
        model = AutoModelForImageTextToText.from_pretrained(
            model_id,
            trust_remote_code=True,
            torch_dtype=compute_dtype,
            low_cpu_mem_usage=True,  # Reduce memory footprint
            device_map="auto" if DEVICE == "cuda" else None
        )
        
        # Move to device
        print("    [3/3] Moving model to device...")
        if DEVICE == "cpu":
            model = model.to(DEVICE)  # type: ignore[attr-defined]
        
        print("[+] OCR model loaded successfully and ready.")
        return True
        
    except KeyboardInterrupt:
        print("\n[!] OCR loading interrupted by user.")
        processor = None
        model = None
        ocr_load_failed = True
        return False
    except Exception as e:
        print(f"[!] CRITICAL ERROR loading OCR model: {e}")
        print(f"[!] Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        processor = None
        model = None
        ocr_load_failed = True
        return False

def run_ocr_on_image(image):
    """
    Performs OCR on a single PIL Image using the Nanonets model.
    """
    success = _ensure_ocr_loaded()
    if not success or model is None or processor is None:
        print("[!] OCR model not available. Skipping OCR for this page.")
        return ""

    try:
        # The prompt tells the model which task to perform.
        prompt = "<OCR>"
        inputs = processor(text=prompt, images=image, return_tensors="pt").to(DEVICE)

        # Generate the text from the image.
        pixel_dtype = torch.bfloat16 if DEVICE == "cuda" else torch.float32
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"].to(pixel_dtype),
            max_new_tokens=2048,
            do_sample=False
        )

        # Decode the output to get the text.
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # The model's output includes the prompt, so we parse it to get only the result.
        parsed_text = generated_text.split('<OCR>')[-1].strip()
        return parsed_text
    
    except Exception as e:
        print(f"[!] Error during OCR inference: {e}")
        return ""

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF. It first tries direct text extraction.
    If that fails or yields minimal text, it performs OCR on each page.
    """
    full_text = ""
    try:
        # --- 1. Attempt to extract text directly (for digital PDFs) ---
        doc = fitz.open(pdf_path)
        for pno in range(doc.page_count):
            page = doc.load_page(pno)
            txt = page.get_text("text")
            if isinstance(txt, str):
                full_text += txt
            else:
                full_text += str(txt)
        doc.close()

        # --- 2. If direct extraction gives very little text, assume it's a scanned PDF ---
        if len(full_text.strip()) < 100:
            print(f"  [~] Minimal text found in '{os.path.basename(pdf_path)}'. Switching to OCR.")
            
            # Check if OCR is available before attempting
            if ocr_load_failed:
                print(f"  [!] OCR unavailable. Skipping file '{os.path.basename(pdf_path)}'.")
                return ""  # Return empty string to skip this file
            
            full_text = "" # Reset text to fill with OCR results
            
            # Re-open the document to process pages as images
            doc = fitz.open(pdf_path)
            for pno in range(doc.page_count):
                page = doc.load_page(pno)
                print(f"    - Processing page {pno+1} with OCR...")
                try:
                    # Render page to a medium-resolution image for speed
                    pix = page.get_pixmap(dpi=150)
                    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                    
                    # Run OCR on the image
                    page_text = run_ocr_on_image(image)
                    full_text += page_text + "\n"
                except Exception as e:
                    print(f"    [!] Error processing page {pno+1}: {e}")
                    # Continue with next page
                    continue
            doc.close()
            
            if not full_text.strip():
                print(f"  [!] OCR failed to extract any text from '{os.path.basename(pdf_path)}'.")
        else:
            print(f"  [+] Successfully extracted text directly from '{os.path.basename(pdf_path)}'.")

    except Exception as e:
        print(f"  [!] An error occurred while processing {pdf_path}: {e}")
    
    return full_text

if __name__ == '__main__':
    # ==============================================================================
    # --- For Testing ---
    # This block allows you to test the processor on a single PDF file.
    # ==============================================================================
    
    # --- STEP 1: Open 'downloaded_pdfs' and paste a real filename below ---
    test_pdf_filename = "172378378657Bidding Calendar as on 31-07-2024.docx.pdf" # <-- Paste your filename here
    
    # --- STEP 2: RUN THE SCRIPT ---
    download_dir = "downloaded_pdfs"
    test_pdf_path = os.path.join(download_dir, test_pdf_filename)

    # Corrected Logic: First check if the filename is the placeholder. 
    # Then, check if the file actually exists before trying to process it.
    if "PASTE_YOUR_FILENAME_HERE" in test_pdf_filename:
        print("\n[!] Please open pdf_processor.py and change the 'test_pdf_filename' variable to a real file.")
    elif not os.path.exists(test_pdf_path):
        print(f"\n[!] Error: The file '{test_pdf_filename}' was not found in the '{download_dir}' directory.")
        print("Please check the filename spelling and that the 'downloaded_pdfs' folder exists.")
    else:
        print(f"\n--- Processing test file: {test_pdf_filename} ---")
        extracted_content = extract_text_from_pdf(test_pdf_path)
        print("\n--- Extracted Content (First 1000 Chars) ---")
        print(extracted_content[:1000] + "...")
