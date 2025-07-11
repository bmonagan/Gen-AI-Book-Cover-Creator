import requests
import os
import time
import random
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin # Useful for constructing full image URLs

#TODO FUNCTION TYPING


list_page_url = "https://www.goodreads.com/list/show/43342.NEW_ADULT_fantasy_paranormal_romance"
# Simulate a browser by adding a User-Agent header
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


# Create directories
IMAGE_DIR = "goodreads data/goodreads_book_covers"
DATA_DIR = "goodreads data/goodreads_book_data"
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)


def fetch_page(url: str, headers: dict, delay_min: float = 5, delay_max: float = 10) -> str:
    print(f"Fetching: {url}")
    time.sleep(random.uniform(delay_min, delay_max)) # Critical delay
    try:
        response = requests.get(url, headers=headers, timeout=15) # Add timeout
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_book_links_from_list_page(html: str, base_url: str) -> list[str]:
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

if not initial_html:
    print("Failed to get initial list page. Exiting.")
    exit()
def get_next_goodreads_page_url(html: str, current_url: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    next_page_link = soup.find('a', class_='next_page')
    if next_page_link and next_page_link.get('href'):
        next_page_relative_url = next_page_link['href']
        return urljoin(current_url, next_page_relative_url)
    return None
 
book_detail_urls = []
next_page = True
while next_page:
    book_detail_urls.extend(extract_book_links_from_list_page(initial_html, list_page_url))

    next_page = get_next_goodreads_page_url(initial_html, list_page_url)
    if next_page:
        print(f"Found next page: {next_page}")
        initial_html = fetch_page(next_page, headers)
    else:
        print("No more pages found.")
        next_page = False
print(f"Total book detail URLs found: {len(book_detail_urls)}")

 # To save data in a structured format

def extract_book_details(book_html: str, book_url: str) -> dict:
    soup = BeautifulSoup(book_html, 'html.parser')
    book_data = {
        'url': book_url,
        'title': None,
        'author': None,
        'image_url': None,
        'description': None,
        'genres': [],
        'pages': None,
        'publication_year': None,
        'average_rating': None,
        'ratings_count': None,
        'reviews_count': None,
        'description': None,
    }

    try:
        # Title
        title_tag = soup.find('h1', class_='Text__title1') # New Goodreads UI
        if not title_tag: # Fallback for older UI or variations
             title_tag = soup.find('h1', id='bookTitle')
        if title_tag:
            book_data['title'] = title_tag.get_text(strip=True)

        # Author
        author_tag = soup.find('span', class_='ContributorLink__name') # New Goodreads UI
        if not author_tag: # Fallback
            author_tag = soup.find('a', class_='authorName')
        if author_tag:
            book_data['author'] = author_tag.get_text(strip=True)

        # Main Image URL
        image_tag = soup.find('img', class_='ResponsiveImage') # New Goodreads UI
        if not image_tag: # Fallback
            image_tag = soup.find('img', id='bookCover')
        if image_tag and image_tag.get('src'):
            src = image_tag.get('src')
            if src.startswith('//'):
                src = 'https:' + src
            book_data['image_url'] = src

        # Description (often in a div with a "show more" button)
        # This is where Selenium often becomes necessary for full text if truncated
        description_div = soup.find('div', id='description')
        if description_div:
            # Look for the full description text. It might be in a 'span' that expands.
            full_description_span = description_div.find('span', style='display:none') # If expanded
            if full_description_span:
                book_data['description'] = full_description_span.get_text(strip=True)
            else: # If description is fully visible
                book_data['description'] = description_div.get_text(strip=True, separator=' ')
                # Clean up "more..." or "less..." if present
                book_data['description'] = book_data['description'].replace('...more', '').replace('...less', '').strip()


        # Genres (often found in a div or section)
        genre_tags = soup.find_all('a', class_='Button--tag-small') # Example for new UI tags
        if not genre_tags: # Fallback
             genre_tags = soup.select('div[data-testid="genresList"] a span.Button__labelItem')
        book_data['genres'] = [genre.get_text(strip=True) for genre in genre_tags]

        # Pages
        pages_tag = soup.find('p', {'data-testid': 'pagesFormat'}) # New Goodreads UI
        if pages_tag:
            pages_text = pages_tag.get_text(strip=True)
            # Extract numbers from "X pages" or "X pages, Y parts"
            import re
            match = re.search(r'(\d+)\s+pages', pages_text)
            if match:
                book_data['pages'] = int(match.group(1))

        # Publication Year (often within a publication info paragraph)
        pub_info_tag = soup.find('p', {'data-testid': 'publicationInfo'}) # New Goodreads UI
        if pub_info_tag:
            pub_info_text = pub_info_tag.get_text(strip=True)
            match = re.search(r'published\s+(\d{4})', pub_info_text)
            if match:
                book_data['publication_year'] = int(match.group(1))
            else: # Sometimes just the year is present
                 match = re.search(r'\b(\d{4})\b', pub_info_text)
                 if match:
                     book_data['publication_year'] = int(match.group(1))


        # Ratings and Reviews
        # These selectors are very prone to change.
        average_rating_tag = soup.find('div', class_='RatingStatistics__rating')
        if average_rating_tag:
            book_data['average_rating'] = float(average_rating_tag.get_text(strip=True))

        ratings_reviews_span = soup.find('span', class_='RatingStatistics__info')
        if ratings_reviews_span:
            text = ratings_reviews_span.get_text(strip=True).replace(',', '') # Remove commas for numbers
            ratings_match = re.search(r'(\d+)\s+ratings', text)
            if ratings_match:
                book_data['ratings_count'] = int(ratings_match.group(1))

            reviews_match = re.search(r'(\d+)\s+reviews', text)
            if reviews_match:
                book_data['reviews_count'] = int(reviews_match.group(1))
        
        # Formatted tag which is the book description
        desc_tag = soup.find('div', {'data-testid': 'contentContainer'})
        if desc_tag:
            book_data['description'] = desc_tag.get_text(strip=True)

        


    except Exception as e:
        print(f"Error parsing details for {book_url}: {e}")

    return book_data

def download_image(image_url: str, save_path: str) -> None:
    """
    Downloads an image from a given URL and saves it to a specified path.
    Includes crucial delays for ethical scraping on Goodreads.
    """
    print(f"Attempting to download: {image_url}")
    try:
        # Goodreads has a more strict scraping policy, so need to include the random delays
        # This delay is *in addition* to delays before fetching HTML pages.
        time.sleep(random.uniform(3, 7)) # Wait 3-7 seconds between each image download

        response = requests.get(image_url, stream=True, headers=headers, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        with open(save_path, 'wb') as out_file:
            # Use iter_content for efficient downloading of large files
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)
        print(f"Successfully downloaded: {os.path.basename(save_path)}")

    except requests.exceptions.RequestException as e:
        print(f"Error downloading {image_url}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while downloading {image_url}: {e}")


# Iterate and scrape details

all_books_data = []

for i, book_url in enumerate(book_detail_urls):
    print(f"Scraping details for book {i+1}/{len(book_detail_urls)}: {book_url}")
    book_html = fetch_page(book_url, headers, delay_min=5, delay_max=15) # Longer delay for detail pages

    if book_html:
        book_details = extract_book_details(book_html, book_url)
        all_books_data.append(book_details)

        # Download image if URL found
        if book_details['image_url']:
            filename_suffix = book_details['image_url'].split('/')[-1].split('?')[0]
            # Use book title for filename if available, otherwise generic
            if book_details['title']:
                sanitized_title = "".join([c for c in book_details['title'] if c.isalnum() or c.isspace()]).strip()
                filename = os.path.join(IMAGE_DIR, f"{sanitized_title[:50]}_{filename_suffix}")
            else:
                filename = os.path.join(IMAGE_DIR, f"book_cover_{i+1}_{filename_suffix}")
            download_image(book_details['image_url'], filename)
    else:
        print(f"Skipping details for {book_url} due to fetch error.")

# Save all collected data
data_filename = os.path.join(DATA_DIR, "goodreads_books_data.json")
with open(data_filename, 'w', encoding='utf-8') as f:
    json.dump(all_books_data, f, ensure_ascii=False, indent=4)
print(f"All book data saved to {data_filename}")