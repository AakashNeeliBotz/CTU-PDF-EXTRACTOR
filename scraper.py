import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# Use a consistent user agent to mimic a real browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def find_pdf_links(source_id, source_url):
    """
    Finds all PDF links on a given URL, tailored for a specific source.

    Args:
        source_id (str): The identifier for the data source (e.g., "SN1").
        source_url (str): The URL to scrape.

    Returns:
        list: A list of absolute URLs to PDF files found on the page.
    """
    print(f"  [*] Scraping {source_id} at URL: {source_url}")
    
    # Handle direct PDF links
    if source_url.lower().endswith('.pdf'):
        print("  [+] Direct PDF link found.")
        return [source_url]

    try:
        response = requests.get(source_url, headers=HEADERS, timeout=20)
        response.raise_for_status() # Raise an exception for bad status codes
        
        soup = BeautifulSoup(response.content, 'html.parser')
        pdf_links = set() # Use a set to avoid duplicate links

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.lower().endswith('.pdf'):
                # Convert relative URL to absolute URL
                absolute_url = urljoin(source_url, href)
                pdf_links.add(absolute_url)

        if not pdf_links:
            print(f"  [~] No PDF links found for {source_id}.")
        else:
            print(f"  [+] Found {len(pdf_links)} PDF links for {source_id}.")
            
        return list(pdf_links)

    except requests.exceptions.RequestException as e:
        print(f"  [!] Could not fetch URL for {source_id}: {e}")
        return []

def scrape_all_sources(data_sources_dict):
    """
    Iterates through the data sources config and scrapes each one.
    
    Args:
        data_sources_dict (dict): The DATA_SOURCES dictionary from config.py.
        
    Returns:
        dict: A dictionary mapping each source_id to a list of its PDF links.
    """
    all_links = {}
    for source_id, source_url in data_sources_dict.items():
        links = find_pdf_links(source_id, source_url)
        if links:
            all_links[source_id] = links
        time.sleep(1) # Be respectful to the server by waiting a second
    return all_links

