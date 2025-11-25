import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from models.state import VisibilityState


KEYWORDS = [
    "product", "products", "solutions", "services", "categories", "catalog",
    "our-business", "therapy", "therapeutic", "portfolio", "brands", "what-we-do",
    "pipeline", "research", "overview"
]


def fetch_html(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception:
        return None


def clean_text(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # Remove meaningless tags
    for tag in soup(["script", "style", "noscript", "footer", "header", "nav", "form"]):
        tag.decompose()

    # Extract clean readable text
    text = soup.get_text(separator=" ", strip=True)
    text = " ".join(text.split())  # collapse whitespace
    return text


def discover_relevant_links(base_url: str, html: str):
    soup = BeautifulSoup(html, "html.parser")
    domain = urlparse(base_url).netloc

    links = set()

    for a in soup.find_all("a", href=True):
        href = a['href']

        # Convert relative → absolute
        full_url = urljoin(base_url, href)

        # Only include internal pages
        if domain not in full_url:
            continue

        # Only include business-relevant links
        if any(keyword in full_url.lower() for keyword in KEYWORDS):
            links.add(full_url)

    return list(links)


def web_scraper(state: VisibilityState):
    """
    Intelligent web scraper:
    - Scrapes main page
    - Detects business-relevant subpages
    - Scrapes them too
    - Returns clean + relevant text
    """

    base_url = state.website_url
    all_text_chunks = []
    raw_html_store = {}

    # 1. Fetch main page
    main_html = fetch_html(base_url)
    if not main_html:
        return {
            "raw_website_html": "ERROR: Unable to fetch URL",
            "extracted_content": ""
        }

    raw_html_store[base_url] = main_html
    all_text_chunks.append(clean_text(main_html))

    # 2. Discover relevant subpages
    links = discover_relevant_links(base_url, main_html)

    # Limit to avoid huge crawls
    links = links[:5]

    # 3. Fetch & extract from subpages
    for link in links:
        sub_html = fetch_html(link)
        if sub_html:
            raw_html_store[link] = sub_html
            all_text_chunks.append(clean_text(sub_html))

    # Combine everything
    combined_text = " ".join(all_text_chunks)
    combined_text = " ".join(combined_text.split())

    return {
        "raw_website_html": raw_html_store,
        "extracted_content": combined_text
    }
