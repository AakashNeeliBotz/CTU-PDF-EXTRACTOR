import sys

try:
    import torch
    print(f"✓ PyTorch installed: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"✓ CUDA version: {torch.version.cuda}")
        print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
        print("\n🎉 SUCCESS! GPU support is enabled!")
    else:
        print("\n❌ CUDA not available - CPU only")
        sys.exit(1)
        
except ImportError as e:
    print(f"❌ Error importing torch: {e}")
    sys.exit(1)
