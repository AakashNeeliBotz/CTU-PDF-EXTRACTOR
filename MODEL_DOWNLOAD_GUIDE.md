# Model Download Guide

This guide explains how to safely download the `google/gemma-3-4b-it` model without freezing your system.

## Why Did My Computer Freeze?

When downloading large models (8.5 GB), HuggingFace temporarily buffers data in RAM. With only 8 GB total RAM and Windows + background apps using 4-5 GB, the download process can exhaust available memory, causing your system to freeze.

## Safe Download Process

### Step 1: Clean Up Incomplete Download

```bash
python cleanup_model.py
```

**What it does:**
- Checks if there's an incomplete model download
- Shows the current size of cached files
- Safely deletes the incomplete download after confirmation
- You must type `DELETE` (all caps) to confirm

### Step 2: Prepare Your System

**Before downloading:**
1. ✅ Close unnecessary applications (browsers, Discord, etc.)
2. ✅ Close other Python/IDE windows
3. ✅ Ensure you have stable internet connection
4. ✅ Make sure you have 10+ GB free disk space

**Optional but helpful:**
- Increase virtual memory (pagefile):
  - Settings → System → About → Advanced system settings
  - Performance Settings → Advanced → Virtual memory
  - Set to "System managed size" or custom (12-16 GB)

### Step 3: Download Safely

```bash
python download_model_safe.py
```

**What it does:**
- Checks disk space (needs 10+ GB free)
- Checks available RAM (needs 3+ GB available)
- Downloads model with memory-efficient settings
- Shows progress and verifies completion

**Expected behavior:**
- Download time: 10-30 minutes (depends on internet speed)
- RAM usage: 2-4 GB peak (instead of 6-8 GB)
- The script will show progress bars

### Step 4: Run Your Test

After successful download:

```bash
python test_main_skip_download.py
```

The model is now cached and will load from disk without re-downloading.

## Troubleshooting

### Problem: Still freezing during download

**Solutions:**
1. Restart computer to free up RAM
2. Increase virtual memory/pagefile to 16 GB
3. Download during off-hours with minimal background processes
4. Use Task Manager to force-close frozen processes (Ctrl+Shift+Esc)

### Problem: Download interrupted/failed

**Solutions:**
- Just run `download_model_safe.py` again
- HuggingFace automatically resumes partial downloads
- No need to delete and start over unless corrupted

### Problem: "Insufficient disk space"

**Solutions:**
1. Free up at least 10 GB on your C: drive
2. Check cache location: `C:\Users\PT\.cache\huggingface\hub\`
3. Delete old cached models if needed

### Problem: Download very slow

**Solutions:**
- Check your internet speed (8.5 GB download)
- Temporarily disable VPN if using one
- Try downloading at different times (less network congestion)

## Model Cache Location

Models are stored at:
```
C:\Users\PT\.cache\huggingface\hub\models--google--gemma-3-4b-it\
```

The actual weights are in the `blobs/` subfolder. When complete, this should be ~8.5 GB.

## Memory Usage Comparison

| Method | Peak RAM Usage | Risk of Freeze |
|--------|---------------|----------------|
| Default download | 6-8 GB | ⚠️ HIGH |
| Safe download (our script) | 2-4 GB | ✅ LOW |

The safe download uses `low_cpu_mem_usage=True` which loads model chunks incrementally instead of buffering the entire model in RAM.

## After Download

Once downloaded, the model stays cached. Future runs will:
1. Load from cache (no download)
2. Initial load to GPU takes 5-15 seconds
3. Subsequent inferences are fast (~2-5 sec per extraction)

## Need Help?

If you encounter issues not covered here:
1. Check the error message carefully
2. Note which step failed (cleanup/download/test)
3. Check Task Manager for RAM/disk usage
4. Try rebooting and running again with ALL apps closed
