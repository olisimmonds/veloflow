import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
from collections import Counter
import concurrent.futures
import unicodedata

def scrape_page(url, headers):
    """
    Scrapes the content of a single page.
    Returns:
      - The concatenated text from all <p> tags.
      - A list of hyperlinks found on the page.
    """
    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        st.error(f"Error accessing {url}: {e}")
        return "", []
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        content = "\n".join(p.get_text() for p in paragraphs)
        raw_links = [a.get('href') for a in soup.find_all('a', href=True)]
        links = [urljoin(url, link) for link in raw_links if link]
        return content, links
    else:
        st.warning(f"Failed to retrieve content from {url}. HTTP Status Code: {response.status_code}")
        return "", []

def crawl_website(start_url, max_depth=2, time_limit=20):
    """
    Crawls a website starting from start_url concurrently.
    
    Parameters:
      start_url (str): The URL of the website to start crawling from.
      max_depth (int): Maximum recursion depth to prevent endless crawling.
      time_limit (int): Maximum time in seconds to let the crawl run.
    
    Returns:
      dict: A mapping from each visited URL to its scraped content.
    """
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/58.0.3029.110 Safari/537.36')
    }
    
    visited = set()      # Keep track of visited URLs to avoid duplication
    results = {}         # Dictionary to store the scraped content by URL
    base_domain = urlparse(start_url).netloc
    start_time = time.time()
    
    # Dictionary to map futures to their (url, depth)
    future_to_task = {}
    
    # Create a thread pool executor for concurrent requests
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)
    
    def schedule_crawl(url, depth):
        if time.time() - start_time > time_limit:
            return
        if depth > max_depth or url in visited:
            return
        visited.add(url)
        future = executor.submit(scrape_page, url, headers)
        future_to_task[future] = (url, depth)
    
    # Begin crawling from the start_url
    schedule_crawl(start_url, 0)
    
    # Process futures as they complete and schedule new tasks
    while future_to_task and (time.time() - start_time) < time_limit:
        # Wait until any of the scheduled tasks is completed
        done, _ = concurrent.futures.wait(future_to_task, return_when=concurrent.futures.FIRST_COMPLETED, timeout=0.5)
        for future in done:
            url, depth = future_to_task.pop(future)
            try:
                content, links = future.result()
                results[url] = content
                for link in links:
                    parsed_link = urlparse(link)
                    if parsed_link.netloc and parsed_link.netloc != base_domain:
                        continue
                    if link not in visited:
                        schedule_crawl(link, depth + 1)
            except Exception as e:
                st.error(f"Error processing {url}: {e}")
    
    # Cancel any futures still pending once the time limit is reached
    for future in future_to_task:
        future.cancel()
    
    executor.shutdown(wait=False)
    return results


def extract_unique_sentences(pages_dict):
    """
    Splits all text into sentences, preprocesses them,
    counts their frequency, and returns only truly unique ones (preprocessed).
    """
    sentence_counter = Counter()
    page_sentences = {}
    sentence_mapping = {}  # Maps original sentence -> preprocessed form

    def preprocess(sentence):
        # Normalize unicode, lowercase, strip punctuation and extra spaces
        sentence = unicodedata.normalize("NFKD", sentence)
        sentence = sentence.lower().strip()
        sentence = re.sub(r'[\s]+', ' ', sentence)
        # sentence = re.sub(r'[^\w\s]', '', sentence)  # remove punctuation
        return sentence

    # First pass: split and preprocess
    for url, content in pages_dict.items():
        sentences = re.split(r'(?<=[.!?])\s+', content.strip())
        page_sentences[url] = sentences
        for s in sentences:
            p = preprocess(s)
            sentence_counter[p] += 1
            sentence_mapping[s] = p

    # Second pass: collect preprocessed sentences that are unique
    unique_sentences = set()
    for sentences in page_sentences.values():
        for s in sentences:
            preprocessed = sentence_mapping[s]
            if sentence_counter[preprocessed] == 1:
                unique_sentences.add(preprocessed)

    return ' '.join(unique_sentences)