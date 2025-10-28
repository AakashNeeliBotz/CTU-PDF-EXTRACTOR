"""
Verify that the model was actually downloaded successfully.
"""

from pathlib import Path


def verify_model_download() -> bool:
    """Check all possible locations for model files."""
    
    print("=" * 70)
    print("MODEL DOWNLOAD VERIFICATION")
    print("=" * 70)
    
    model_dir = Path.home() / ".cache" / "huggingface" / "hub" / "models--google--gemma-3-4b-it"
    
    if not model_dir.exists():
        print("\n❌ Model directory not found!")
        return False
    
    print(f"\n✓ Model directory exists: {model_dir}")
    
    # Check all subdirectories and their sizes
    total_size = 0
    file_count = 0
    
    for subdir in ["blobs", "snapshots", "refs"]:
        subdir_path = model_dir / subdir
        if subdir_path.exists():
            subdir_size = 0
            subdir_files = 0
            
            for file_path in subdir_path.rglob("*"):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    subdir_size += file_size
                    subdir_files += 1
                    total_size += file_size
                    file_count += 1
            
            size_gb = subdir_size / (1024 ** 3)
            print(f"  {subdir}/: {subdir_files} files, {size_gb:.2f} GB")
    
    total_gb = total_size / (1024 ** 3)
    
    print(f"\n📊 TOTAL: {file_count} files, {total_gb:.2f} GB")
    
    # Check if download is complete
    if total_gb > 8.0:
        print("\n✅ MODEL DOWNLOAD COMPLETE!")
        print(f"   Downloaded: {total_gb:.2f} GB (expected ~8.5 GB)")
        print("\n🎉 You're ready to run the pipeline!")
        print("\nNext step:")
        print("  → Run: python test_main_skip_download.py")
        return True
    else:
        print(f"\n⚠️  Model may be incomplete")
        print(f"   Expected: ~8.5 GB")
        print(f"   Found: {total_gb:.2f} GB")
        return False


if __name__ == "__main__":
    verify_model_download()
    print("\n" + "=" * 70)
