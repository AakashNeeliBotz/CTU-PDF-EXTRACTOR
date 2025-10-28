"""
Check if the Hugging Face model is properly downloaded and cached.
"""

from pathlib import Path
import json


def check_model_status():
    """Check the status of google/gemma-3-4b-it model download."""
    
    model_name = "google/gemma-3-4b-it"
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    model_dir = cache_dir / "models--google--gemma-3-4b-it"
    
    print("=" * 70)
    print("HUGGING FACE MODEL STATUS CHECK")
    print("=" * 70)
    print(f"\nModel: {model_name}")
    print(f"Cache directory: {cache_dir}")
    print(f"Model directory: {model_dir}")
    print()
    
    # Check if model directory exists
    if not model_dir.exists():
        print("❌ MODEL NOT FOUND")
        print("   The model directory does not exist.")
        print("\n   Next steps:")
        print("   → Run: python download_model_safe.py")
        return False
    
    print("✓ Model directory exists")
    
    # Check subdirectories
    subdirs = ["blobs", "snapshots", "refs"]
    for subdir in subdirs:
        subdir_path = model_dir / subdir
        if subdir_path.exists():
            print(f"  ✓ {subdir}/ directory found")
        else:
            print(f"  ✗ {subdir}/ directory missing")
    
    # Check blobs (actual model files)
    blobs_dir = model_dir / "blobs"
    
    if not blobs_dir.exists():
        print("\n❌ INCOMPLETE DOWNLOAD")
        print("   The blobs directory is missing.")
        print("\n   Next steps:")
        print("   → Run: python cleanup_model.py")
        print("   → Then: python download_model_safe.py")
        return False
    
    # Count files and calculate size
    blob_files = list(blobs_dir.iterdir())
    
    if not blob_files:
        print("\n❌ INCOMPLETE DOWNLOAD")
        print("   The blobs directory is empty.")
        print("\n   Next steps:")
        print("   → Run: python cleanup_model.py")
        print("   → Then: python download_model_safe.py")
        return False
    
    total_size = 0
    file_count = 0
    
    for file_path in blob_files:
        if file_path.is_file():
            total_size += file_path.stat().st_size
            file_count += 1
    
    size_gb = total_size / (1024 ** 3)
    
    print(f"\n📊 DOWNLOAD STATUS:")
    print(f"   Files in blobs/: {file_count}")
    print(f"   Total size: {size_gb:.2f} GB")
    
    # Expected size is ~8.5 GB
    if size_gb < 7.0:
        print(f"\n⚠️  POSSIBLY INCOMPLETE")
        print(f"   Expected: ~8.5 GB")
        print(f"   Found: {size_gb:.2f} GB")
        print("\n   The download may be incomplete.")
        print("\n   Options:")
        print("   1. Run download script again (it will resume): python download_model_safe.py")
        print("   2. Or clean and re-download: python cleanup_model.py")
        return False
    
    elif size_gb >= 7.0 and size_gb < 10.0:
        print(f"\n✅ DOWNLOAD COMPLETE!")
        print(f"   The model appears to be fully downloaded.")
        print(f"   Size is within expected range (8-9 GB).")
        
        # Check snapshots
        snapshots_dir = model_dir / "snapshots"
        if snapshots_dir.exists():
            snapshot_folders = [d for d in snapshots_dir.iterdir() if d.is_dir()]
            if snapshot_folders:
                print(f"   Snapshot versions: {len(snapshot_folders)}")
        
        print("\n   ✓ Ready to use!")
        print("\n   Next steps:")
        print("   → Run: python test_main_skip_download.py")
        return True
    
    else:
        print(f"\n⚠️  UNEXPECTED SIZE")
        print(f"   The model size ({size_gb:.2f} GB) is larger than expected.")
        print(f"   This might indicate multiple versions or corrupted files.")
        print("\n   The model should still work. Try running:")
        print("   → python test_main_skip_download.py")
        return True


def check_model_loadable():
    """Try to verify model can be loaded (optional quick check)."""
    
    print("\n" + "=" * 70)
    print("QUICK LOAD TEST (Optional)")
    print("=" * 70)
    
    try:
        from transformers import AutoTokenizer
        
        print("\n🔄 Attempting to load tokenizer (quick test)...")
        tokenizer = AutoTokenizer.from_pretrained(
            "google/gemma-3-4b-it",
            trust_remote_code=True
        )
        print("✓ Tokenizer loaded successfully!")
        print("  This confirms the model files are accessible and valid.")
        return True
        
    except Exception as e:
        print(f"✗ Error loading tokenizer: {e}")
        print("\n  This might indicate corrupted download.")
        print("  Try cleaning and re-downloading.")
        return False


if __name__ == "__main__":
    model_ok = check_model_status()
    
    if model_ok:
        # Only do load test if model appears complete
        print("\n" + "─" * 70)
        response = input("\nDo you want to run a quick load test? (y/n): ").strip().lower()
        if response == 'y':
            check_model_loadable()
    
    print("\n" + "=" * 70)
