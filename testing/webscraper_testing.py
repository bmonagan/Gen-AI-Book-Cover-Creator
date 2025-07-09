import requests
from bs4 import BeautifulSoup
import os
import time
import random
from urllib.parse import urljoin # Useful for constructing full image URLs


search_url = "https://www.goodreads.com/list/show/43342.NEW_ADULT_fantasy_paranormal_romance"

# Simulate a browser by adding a User-Agent header
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def fetch_page(url, headers):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

html_content = fetch_page(search_url, headers)
if not html_content:
    exit("Could not fetch the search page. Exiting.")

def extract_goodreads_image_urls(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    image_urls = set()

    # --- Selector for the main book cover on a book details page ---
    # Example: Look for an image within a div with specific attributes, or by its ID
    main_cover_img = soup.find('img', class_='ResponsiveImage') # Common Goodreads class
    if main_cover_img and main_cover_img.get('src'):
        src = main_cover_img.get('src')
        if src.startswith('//'): # Handle protocol-relative URLs
            src = 'https:' + src
        image_urls.add(src)
        print(f"Found main cover: {src}")

    # --- Selectors for book covers on a list page ---
    # (If your target_url is a list page)
    # Example: Find all book entries, then find the image within each
    book_items = soup.find_all('img', class_='bookCover') # Or other relevant class like 'listBook__img'
    for img in book_items:
        src = img.get('src')
        if src:
            if src.startswith('//'):
                src = 'https:' + src
            image_urls.add(src)
            print(f"Found list cover: {src}")

    return list(image_urls)

goodreads_image_urls = extract_goodreads_image_urls(html_content, target_url)
print(f"Found {len(goodreads_image_urls)} potential image URLs.")