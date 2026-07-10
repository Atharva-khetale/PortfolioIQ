"""
Market data acquisition layer.

Primary source: Yahoo Finance (via yfinance) — free, no key, good coverage
for NSE/BSE (.NS/.BO suffixes) and US tickers.
Fallback sources: Alpha Vantage, Financial Modeling Prep (used when yfinance
fails or for fundamentals not exposed by yfinance).

This is the ONLY module in the codebase allowed to call yfinance / AV / FMP
directly — everything else consumes clean pandas DataFrames from here.
"""
import time
import requests
import pandas as pd
import yfinance as yf
from app.core.config import settings


class MarketDataProvider:

    # ---------------------------------------------------------
    # Price history
    # ---------------------------------------------------------
    @staticmethod
    def get_price_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """Return OHLCV DataFrame indexed by date."""
        try:
            df = yf.Ticker(ticker).history(period=period, interval=interval)
            if df.empty:
                raise ValueError("empty response")
            df = df.rename(columns={
                "Open": "open", "High": "high", "Low": "low",
                "Close": "close", "Volume": "volume"
            })
            df.index.name = "date"
            return df[["open", "high", "low", "close", "volume"]]
        except Exception as e:
            return MarketDataProvider._alpha_vantage_history(ticker)

    @staticmethod
    def _alpha_vantage_history(ticker: str) -> pd.DataFrame:
        if not settings.ALPHA_VANTAGE_API_KEY:
            return pd.DataFrame()
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": ticker,
            "outputsize": "compact",
            "apikey": settings.ALPHA_VANTAGE_API_KEY,
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json().get("Time Series (Daily)", {})
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data).T
        df.columns = ["open", "high", "low", "close", "adj_close", "volume",
                      "div", "split"][:len(df.columns)]
        df.index = pd.to_datetime(df.index)
        df = df.astype(float)
        return df.sort_index()

    # ---------------------------------------------------------
    # Company / fundamentals info
    # ---------------------------------------------------------
    @staticmethod
    def get_company_info(ticker: str) -> dict:
        try:
            info = yf.Ticker(ticker).info
            return {
                "ticker": ticker,
                "company_name": info.get("longName") or info.get("shortName") or ticker,
                "sector": info.get("sector", "Other"),
                "industry": info.get("industry", "Other"),
                "country": info.get("country", "Unknown"),
                "exchange": info.get("exchange", "Unknown"),
                "currency": info.get("currency", "USD"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "website": info.get("website"),
                "business_summary": info.get("longBusinessSummary", ""),
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "asset_class": MarketDataProvider._infer_asset_class(info),
            }
        except Exception:
            return MarketDataProvider._fmp_company_info(ticker)

    @staticmethod
    def _infer_asset_class(info: dict) -> str:
        quote_type = (info.get("quoteType") or "").upper()
        if quote_type == "ETF":
            return "ETF"
        if quote_type == "MUTUALFUND":
            return "MUTUAL_FUND"
        if quote_type == "CRYPTOCURRENCY":
            return "CRYPTO"
        return "EQUITY"

    @staticmethod
    def _fmp_company_info(ticker: str) -> dict:
        if not settings.FMP_API_KEY:
            return {"ticker": ticker, "company_name": ticker, "sector": "Other",
                    "industry": "Other", "country": "Unknown", "exchange": "Unknown",
                    "currency": "USD", "asset_class": "EQUITY"}
        url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}"
        r = requests.get(url, params={"apikey": settings.FMP_API_KEY}, timeout=15)
        data = r.json()
        if not data:
            return {"ticker": ticker, "company_name": ticker, "sector": "Other",
                     "industry": "Other", "country": "Unknown", "exchange": "Unknown",
                     "currency": "USD", "asset_class": "EQUITY"}
        d = data[0]
        return {
            "ticker": ticker, "company_name": d.get("companyName", ticker),
            "sector": d.get("sector", "Other"), "industry": d.get("industry", "Other"),
            "country": d.get("country", "Unknown"), "exchange": d.get("exchangeShortName", "Unknown"),
            "currency": d.get("currency", "USD"), "website": d.get("website"),
            "current_price": d.get("price"), "beta": d.get("beta"),
            "business_summary": d.get("description", ""), "asset_class": "EQUITY",
        }

    # ---------------------------------------------------------
    # Batch adjusted-close matrix for a list of tickers
    # ---------------------------------------------------------
    @staticmethod
    def get_price_matrix(tickers: list, period: str = "1y") -> pd.DataFrame:
        """Returns a DataFrame of close prices, columns=tickers, index=date."""
        data = {}
        for t in tickers:
            hist = MarketDataProvider.get_price_history(t, period=period)
            if not hist.empty:
                data[t] = hist["close"]
            time.sleep(0.1)  # be polite to the API
        return pd.DataFrame(data).dropna(how="all")

    @staticmethod
    def resolve_ticker(query: str) -> str:
        """
        Best-effort resolution of a free-text company name to a ticker,
        using Yahoo's search endpoint. Falls back to the raw query
        (assumed to already be a ticker) if nothing is found.
        """
        try:
            url = "https://query2.finance.yahoo.com/v1/finance/search"
            r = requests.get(url, params={"q": query}, timeout=10,
                              headers={"User-Agent": "Mozilla/5.0"})
            quotes = r.json().get("quotes", [])
            if quotes:
                return quotes[0]["symbol"]
        except Exception:
            pass
        return query
