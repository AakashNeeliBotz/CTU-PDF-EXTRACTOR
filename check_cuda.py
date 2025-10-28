import torch

print("=" * 60)
print("CUDA CHECK")
print("=" * 60)
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU device: {torch.cuda.get_device_name(0)}")
    print(f"GPU count: {torch.cuda.device_count()}")
else:
    print("\n⚠️  CUDA NOT AVAILABLE")
    print("\nYou have CPU-only PyTorch installed.")
    print("For GPU acceleration, you need to install PyTorch with CUDA support.")
    print("\nYour GPU: NVIDIA GTX 1080 (supports CUDA)")
    print("\nTo fix this, uninstall current torch and install CUDA version:")
    print("\n  pip uninstall torch torchvision torchaudio")
    print("  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    print("\n(CUDA 11.8 is compatible with GTX 1080)")
print("=" * 60)
