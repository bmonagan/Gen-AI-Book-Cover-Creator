import requests
import os
import time
import random
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin # Useful for constructing full image URLs


list_page_url = "https://www.goodreads.com/list/show/43342.NEW_ADULT_fantasy_paranormal_romance"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def fetch_page(url, headers, delay_min=5, delay_max=10):
    print(f"Fetching: {url}")
    time.sleep(random.uniform(delay_min, delay_max)) # Critical delay
    try:
        response = requests.get(url, headers=headers, timeout=15) # Add timeout
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
def extract_book_links_from_list_page(html, base_url):
    soup = BeautifulSoup(html, 'html.parser')
    book_links = []

    # Goodreads list pages typically have table rows or divs for each book
    # Inspect element to find the common container for each book entry
    # Common pattern: tr with itemtype="http://schema.org/Book"
    book_entries = soup.find_all('tr', itemtype='http://schema.org/Book')

    if not book_entries:
        # Fallback for other list page structures, or search results
        book_entries = soup.find_all('div', class_='bookalike') # Another common class
        # Add more specific selectors if these don't work for your target page

    for entry in book_entries:
        # Find the link to the individual book page within each entry
        link_tag = entry.find('a', class_='bookTitle') # Common class for book title link
        if link_tag and link_tag.get('href'):
            relative_url = link_tag['href']
            full_url = urljoin(base_url, relative_url)
            book_links.append(full_url)
    return list(set(book_links)) # Return unique links


initial_html = fetch_page(list_page_url, headers)
def get_next_goodreads_page_url(html: str, current_url: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    next_page_link = soup.find('a', class_='next_page')
    if next_page_link and next_page_link.get('href'):
        next_page_relative_url = next_page_link['href']
        return urljoin(current_url, next_page_relative_url)
    return None
 
book_details_urls = []
next_page = True
while next_page:
    book_details_urls.extend(extract_book_links_from_list_page(initial_html, list_page_url))

    next_page = get_next_goodreads_page_url(initial_html, list_page_url)
    if next_page:
        print(f"Found next page: {next_page}")
        initial_html = fetch_page(next_page, headers)
    else:
        print("No more pages found.")
        next_page = False
print(f"Total book detail URLs found: {len(book_details_urls)}")