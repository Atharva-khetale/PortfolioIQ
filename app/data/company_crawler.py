"""
Company Website Intelligence Module.

Given a company's public website URL, crawl a small set of public pages
(home, about, investors) and extract text signals for the AI insight
engine — e.g. mission statements, recent announcements, product focus.

This performs LIGHT, POLITE crawling only:
  - respects robots.txt
  - crawls a handful of top-level pages, not the whole site
  - no login/authenticated content
"""
import requests
import urllib.robotparser as robotparser
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "PortfolioIQ-Research-Bot/1.0 (+https://example.com/bot)"}
CANDIDATE_PATHS = ["", "/about", "/about-us", "/investors", "/investor-relations", "/news"]


class CompanyCrawler:

    @staticmethod
    def _robots_allowed(base_url: str, path: str) -> bool:
        try:
            parsed = urlparse(base_url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            rp = robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch(HEADERS["User-Agent"], urljoin(base_url, path))
        except Exception:
            return True  # fail open, but crawl is still light/limited

    @staticmethod
    def crawl(website_url: str, max_pages: int = 4) -> dict:
        pages_text = {}
        fetched = 0
        for path in CANDIDATE_PATHS:
            if fetched >= max_pages:
                break
            full_url = urljoin(website_url, path)
            if not CompanyCrawler._robots_allowed(website_url, path):
                continue
            try:
                resp = requests.get(full_url, headers=HEADERS, timeout=10)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "lxml")
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                text = " ".join(soup.get_text(separator=" ").split())
                if len(text) > 100:
                    pages_text[full_url] = text[:4000]  # cap per page
                    fetched += 1
            except Exception:
                continue
        return {
            "website": website_url,
            "pages_crawled": list(pages_text.keys()),
            "combined_text": " ".join(pages_text.values())[:12000],
        }

    @staticmethod
    def extract_signals(crawl_result: dict) -> dict:
        """Very lightweight keyword-based signal extraction from crawled text."""
        text = crawl_result.get("combined_text", "").lower()
        signals = {
            "mentions_growth": any(k in text for k in ["growth", "expansion", "record revenue"]),
            "mentions_risk": any(k in text for k in ["restructuring", "layoffs", "lawsuit", "investigation"]),
            "mentions_esg": any(k in text for k in ["sustainability", "esg", "carbon neutral"]),
            "mentions_innovation": any(k in text for k in ["innovation", "r&d", "patent", "ai", "artificial intelligence"]),
        }
        return signals
