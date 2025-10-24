import os
import requests
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def download_pdfs_for_source(source_id, pdf_links, base_download_dir):
    """
    Downloads PDFs for a single source into a dedicated subfolder.
    """
    source_folder = os.path.join(base_download_dir, source_id)
    if not os.path.exists(source_folder):
        os.makedirs(source_folder)
        print(f"  [*] Created directory: {source_folder}")

    for link in pdf_links:
        try:
            filename = link.split('/')[-1]
            # Clean filename to be safe for file systems
            filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in ('.', '-', '_')]).rstrip()
            
            if not filename:
                filename = f"downloaded_{int(time.time())}.pdf" # Fallback filename
                
            filepath = os.path.join(source_folder, filename)

            if os.path.exists(filepath):
                print(f"  [~] File '{filename}' already exists. Skipping.")
                continue

            print(f"  [*] Downloading '{filename}'...")
            response = requests.get(link, headers=HEADERS, timeout=30, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"  [+] Saved to '{filepath}'")
            time.sleep(1) # Pause between downloads

        except requests.exceptions.RequestException as e:
            print(f"  [!] Failed to download {link}: {e}")

def download_all_pdfs(all_links_by_source, base_download_dir):
    """
    Orchestrates the download process for all sources.
    """
    for source_id, links in all_links_by_source.items():
        print(f"\n--- Downloading PDFs for {source_id} ---")
        download_pdfs_for_source(source_id, links, base_download_dir)


