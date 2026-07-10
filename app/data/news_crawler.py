"""
News / earnings intelligence layer.

Sources:
  1. Yahoo Finance RSS (no key required, decent coverage)
  2. NewsAPI.org (optional, requires NEWS_API_KEY) for broader coverage
"""
import requests
import feedparser
from datetime import datetime
from app.core.config import settings


class NewsCrawler:

    @staticmethod
    def get_yahoo_news(ticker: str, limit: int = 10) -> list:
        """Pull recent headlines from Yahoo Finance RSS feed."""
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        try:
            feed = feedparser.parse(url)
            articles = []
            for entry in feed.entries[:limit]:
                articles.append({
                    "headline": entry.get("title", ""),
                    "source": "Yahoo Finance",
                    "url": entry.get("link", ""),
                    "published_at": NewsCrawler._safe_date(entry),
                    "summary": entry.get("summary", ""),
                })
            return articles
        except Exception:
            return []

    @staticmethod
    def get_newsapi_articles(query: str, limit: int = 10) -> list:
        if not settings.NEWS_API_KEY:
            return []
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query, "sortBy": "publishedAt", "language": "en",
                "pageSize": limit, "apiKey": settings.NEWS_API_KEY,
            }
            r = requests.get(url, params=params, timeout=15)
            data = r.json().get("articles", [])
            return [{
                "headline": a.get("title", ""),
                "source": a.get("source", {}).get("name", "NewsAPI"),
                "url": a.get("url", ""),
                "published_at": a.get("publishedAt", ""),
                "summary": a.get("description", "") or "",
            } for a in data]
        except Exception:
            return []

    @staticmethod
    def get_all_news(ticker: str, company_name: str = None, limit: int = 10) -> list:
        news = NewsCrawler.get_yahoo_news(ticker, limit)
        if len(news) < limit and company_name:
            news += NewsCrawler.get_newsapi_articles(company_name, limit - len(news))
        return news

    @staticmethod
    def _safe_date(entry):
        try:
            return datetime(*entry.published_parsed[:6]).isoformat()
        except Exception:
            return datetime.utcnow().isoformat()
