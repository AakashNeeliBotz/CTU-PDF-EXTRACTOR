"""
Safe model download script with memory optimization.
This script downloads the model separately to avoid system freeze.
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
import psutil


def check_system_resources():
    """Check if system has enough resources for download."""
    
    print("=" * 60)
    print("SYSTEM RESOURCE CHECK")
    print("=" * 60)
    
    # Check disk space
    cache_dir = Path.home() / ".cache" / "huggingface"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    disk_usage = psutil.disk_usage(str(cache_dir))
    free_gb = disk_usage.free / (1024 ** 3)
    
    print(f"\nDisk Space Available: {free_gb:.2f} GB")
    
    if free_gb < 10:
        print("⚠ WARNING: Less than 10 GB free space!")
        print("  Model requires ~8.5 GB. Recommended: 10+ GB free.")
        return False
    
    # Check RAM
    mem = psutil.virtual_memory()
    total_ram_gb = mem.total / (1024 ** 3)
    available_ram_gb = mem.available / (1024 ** 3)
    
    print(f"Total RAM: {total_ram_gb:.2f} GB")
    print(f"Available RAM: {available_ram_gb:.2f} GB")
    
    if available_ram_gb < 3:
        print("⚠ WARNING: Less than 3 GB RAM available!")
        print("  Close some applications before downloading.")
        return False
    
    # Check GPU
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        print(f"GPU: {gpu_name} ({gpu_memory:.2f} GB VRAM)")
    else:
        print("GPU: Not available (CPU mode will be used)")
    
    print("\n✓ System resources look good!")
    return True


def download_model():
    """Download model with memory-efficient settings."""
    
    model_name = "google/gemma-3-4b-it"
    
    print("\n" + "=" * 60)
    print("MODEL DOWNLOAD")
    print("=" * 60)
    print(f"\nModel: {model_name}")
    print("Expected size: ~8.5 GB")
    print("\nThis may take 10-30 minutes depending on internet speed.")
    print("The download uses memory-efficient settings to prevent system freeze.")
    
    input("\nPress ENTER to start download (or Ctrl+C to cancel)...")
    
    try:
        print("\n📥 Step 1/2: Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        print("✓ Tokenizer downloaded successfully!")
        
        print("\n📥 Step 2/2: Downloading model weights...")
        print("⏳ This is the large download (~8.5 GB). Please be patient...")
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,  # ← Critical: Reduces RAM usage during download
            device_map=None,  # Don't load to GPU yet, just download
            trust_remote_code=True
        )
        
        print("\n✓ Model downloaded successfully!")
        
        # Verify download
        model_dir = Path.home() / ".cache" / "huggingface" / "hub" / "models--google--gemma-3-4b-it"
        blobs_dir = model_dir / "blobs"
        
        if blobs_dir.exists():
            total_size = sum(f.stat().st_size for f in blobs_dir.iterdir() if f.is_file())
            size_gb = total_size / (1024 ** 3)
            print(f"\n✓ Downloaded size: {size_gb:.2f} GB")
            
            if size_gb > 8.0:
                print("✓ Download appears COMPLETE!")
            else:
                print("⚠ Warning: Downloaded size seems small. May be incomplete.")
        
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. The model is now cached and ready to use")
        print("  2. Run: python test_main_skip_download.py")
        print("\nThe test script will load the model from cache (no re-download).")
        
    except KeyboardInterrupt:
        print("\n\n✗ Download cancelled by user.")
        print("  Partial downloads are saved and will resume next time.")
    except Exception as e:
        print(f"\n\n✗ Error during download: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your internet connection")
        print("  2. Try running again (downloads resume automatically)")
        print("  3. If repeated failures, check firewall/proxy settings")


if __name__ == "__main__":
    print("\n🚀 SAFE MODEL DOWNLOADER")
    print("This script will download google/gemma-3-4b-it model\n")
    
    if check_system_resources():
        download_model()
    else:
        print("\n✗ Insufficient system resources.")
        print("\nRecommendations:")
        print("  1. Close unnecessary applications (browsers, etc.)")
        print("  2. Free up disk space if needed")
        print("  3. Restart your computer to free up RAM")
        print("  4. Try again after addressing the warnings above")
