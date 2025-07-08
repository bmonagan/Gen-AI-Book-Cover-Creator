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

