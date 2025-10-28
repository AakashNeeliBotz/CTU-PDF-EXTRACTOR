"""
Cleanup script to remove incomplete model downloads.
Run this before attempting a fresh model download.
"""

import shutil
from pathlib import Path


def cleanup_model():
    """Remove incomplete model download from HuggingFace cache."""
    
    model_name = "google/gemma-3-4b-it"
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    model_dir = cache_dir / "models--google--gemma-3-4b-it"
    
    print("=" * 60)
    print("MODEL CLEANUP SCRIPT")
    print("=" * 60)
    print(f"\nModel: {model_name}")
    print(f"Cache directory: {cache_dir}")
    print(f"Model directory: {model_dir}")
    
    if not model_dir.exists():
        print("\n✓ No incomplete download found. Directory doesn't exist.")
        print("  You can proceed directly to download_model_safe.py")
        return
    
    # Check current size
    total_size = 0
    file_count = 0
    
    for file_path in model_dir.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size
            file_count += 1
    
    size_gb = total_size / (1024 ** 3)
    
    print(f"\n⚠ Found existing model directory:")
    print(f"  Files: {file_count}")
    print(f"  Total size: {size_gb:.2f} GB")
    
    if size_gb > 8.0:
        print("\n⚠ WARNING: Directory appears to contain a complete download!")
        print("  The model size should be ~8.5 GB when complete.")
        print("  You may not need to delete this.")
    else:
        print("\n✓ This appears to be an incomplete download.")
        print("  Safe to delete and re-download.")
    
    print("\n" + "=" * 60)
    print("⚠ DANGER: This will permanently delete the model cache!")
    print("=" * 60)
    
    response = input("\nType 'DELETE' (all caps) to confirm deletion: ").strip()
    
    if response == "DELETE":
        print("\n🗑 Deleting model directory...")
        try:
            shutil.rmtree(model_dir)
            print("✓ Successfully deleted incomplete download!")
            print("\nNext steps:")
            print("  1. Close all unnecessary applications")
            print("  2. Run: python download_model_safe.py")
        except Exception as e:
            print(f"✗ Error during deletion: {e}")
            print("\nYou may need to:")
            print("  1. Close any Python processes using the model")
            print("  2. Run this script as administrator")
    else:
        print("\n✗ Deletion cancelled. No changes made.")
        print(f"  You typed: '{response}'")
        print("  Required: 'DELETE'")


if __name__ == "__main__":
    cleanup_model()
