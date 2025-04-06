import os
import hashlib
import yaml
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque

def load_config(file_path="stem-resources.yml"):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)

def clean_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "sup", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True), soup.title.string if soup.title else "Untitled"

def hash_text(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def is_valid(url, domain, include_patterns, exclude_patterns):
    if not domain in urlparse(url).netloc:
        return False
    if any(pattern in url for pattern in exclude_patterns):
        return False
    if include_patterns:
        return any(pattern in url for pattern in include_patterns)
    return True

def crawl_site(config):
    visited = set()
    seen_hashes = set()
    q = deque()

    for url in config["start_urls"]:
        q.append((url, 0))

    source_name = config["name"]
    output_dir = os.path.join("data", source_name)
    os.makedirs(output_dir, exist_ok=True)

    while q:
        url, depth = q.popleft()
        if url in visited or depth > config.get("max_depth", 1):
            continue
        visited.add(url)

        try:
            print(f"Crawling: {url}")
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue

            text, title = clean_text(response.text)
            content_hash = hash_text(text)
            if content_hash in seen_hashes or len(text) < 500:
                continue
            seen_hashes.add(content_hash)

            # Save content
            filename = f"{hash_text(url)}.txt"
            with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
                f.write(f"Title: {title}\nURL: {url}\n\n{text}")

            # Add links to queue
            soup = BeautifulSoup(response.text, "html.parser")
            for a in soup.find_all("a", href=True):
                next_url = urljoin(url, a["href"])
                if is_valid(next_url, config["allowed_domains"][0], config.get("include_patterns", []), config.get("exclude_patterns", [])):
                    q.append((next_url, depth + 1))

        except Exception as e:
            print(f"Error: {url} -> {e}")

def main():
    configs = load_config()
    for config in configs:
        crawl_site(config)

if __name__ == "__main__":
    main()
