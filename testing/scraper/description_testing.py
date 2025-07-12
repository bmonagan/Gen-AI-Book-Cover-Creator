import requests
from bs4 import BeautifulSoup


search_url = "https://www.goodreads.com/book/show/9738483-archangel-s-storm"

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

print(html_content[:1000])  # Print the first 1000 characters

soup = BeautifulSoup(html_content, 'html.parser')
desc_tag = soup.find('div', {'data-testid': 'contentContainer'})
description_div = desc_tag.get_text(strip=True) if desc_tag else "N/A"
print(f"Description: {description_div}")