import requests
from bs4 import BeautifulSoup
import os
import time
import random
from urllib.parse import urljoin # Useful for constructing full image URLs

# Create a directory to save images
IMAGE_DIR = "goodreads_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

search_url = "https://www.goodreads.com/list/show/43342.NEW_ADULT_fantasy_paranormal_romance"

# Simulate a browser by adding a User-Agent header
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36" }