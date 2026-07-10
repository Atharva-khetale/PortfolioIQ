import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    FMP_API_KEY = os.getenv("FMP_API_KEY", "")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

    RISK_FREE_RATE = float(os.getenv("RISK_FREE_RATE", 0.07))
    BENCHMARK_TICKER = os.getenv("BENCHMARK_TICKER", "^NSEI")
    DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "INR")

    TRADING_DAYS_PER_YEAR = 252
    VAR_CONFIDENCE = 0.95

settings = Settings()
