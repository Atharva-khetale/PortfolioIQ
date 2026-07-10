"""
Portfolio Service — the orchestration layer consumed by the Streamlit UI.
Composes data acquisition, analytics, NLP, and DB persistence so pages
stay thin and declarative.
"""
import pandas as pd
from app.data.market_data import MarketDataProvider
from app.data.news_crawler import NewsCrawler
from app.analytics import risk_engine, portfolio_metrics, diversification, insight_engine
from app.nlp import sentiment_engine
from app.core.config import settings


class PortfolioAnalysisResult:
    """Simple container for a full analysis run, passed to dashboard/report."""
    def __init__(self):
        self.portfolio_df = None
        self.sector_alloc = None
        self.geo_alloc = None
        self.price_matrix = None
        self.returns_df = None
        self.risk_metrics = None
        self.risk_contrib = None
        self.div_score = None
        self.r_score = None
        self.insights = None
        self.sentiment_df = None
        self.sentiment_summary = None
        self.total_value = None
        self.weights = None


def enrich_holdings_with_metadata(holdings: list) -> list:
    """holdings: [{ticker, quantity, purchase_price, purchase_date}]"""
    enriched = []
    for h in holdings:
        info = MarketDataProvider.get_company_info(h["ticker"])
        enriched.append({**h, **info})
    return enriched


def run_full_analysis(holdings: list, benchmark_ticker: str = None,
                       period: str = "1y", include_sentiment: bool = True) -> PortfolioAnalysisResult:
    """
    Main pipeline: holdings -> enriched metadata -> prices -> risk -> insights -> sentiment.
    """
    result = PortfolioAnalysisResult()
    benchmark_ticker = benchmark_ticker or settings.BENCHMARK_TICKER

    # 1. Enrich holdings with company/sector/country metadata
    enriched = enrich_holdings_with_metadata(holdings)
    tickers = [h["ticker"] for h in enriched]

    # 2. Pull price history for all tickers + benchmark
    price_matrix = MarketDataProvider.get_price_matrix(tickers, period=period)
    latest_prices = price_matrix.iloc[-1].to_dict() if not price_matrix.empty else {}

    # 3. Compute market values / weights / allocations
    portfolio_df = portfolio_metrics.compute_market_values(enriched, latest_prices)
    sector_alloc = portfolio_metrics.sector_allocation(portfolio_df)
    geo_alloc = portfolio_metrics.geographic_allocation(portfolio_df)
    weights = portfolio_metrics.get_weights_dict(portfolio_df)
    total_value = portfolio_metrics.total_portfolio_value(portfolio_df)

    # 4. Benchmark returns for beta
    benchmark_returns = None
    bench_hist = MarketDataProvider.get_price_history(benchmark_ticker, period=period)
    if not bench_hist.empty:
        benchmark_returns = bench_hist["close"].pct_change().dropna()

    # 5. Risk metrics
    risk_report = risk_engine.full_risk_report(price_matrix, weights, benchmark_returns)
    returns_df = risk_engine.compute_returns(price_matrix)

    # 6. Diversification + risk scoring
    weight_series = pd.Series(weights)
    holding_hhi = diversification.herfindahl_index(weight_series)
    sec_conc = diversification.sector_concentration(sector_alloc)
    div_score = diversification.diversification_score(
        holding_hhi, sec_conc["sector_hhi"], len(portfolio_df))
    r_score = diversification.risk_score(
        risk_report["volatility"], risk_report["max_drawdown"],
        holding_hhi, risk_report["var_95"])

    cov_matrix = returns_df.cov() * risk_engine.TRADING_DAYS
    risk_contrib = diversification.risk_contribution(weight_series, cov_matrix)

    # 7. Sentiment (optional — can be slow due to model + network calls)
    sentiment_df = pd.DataFrame()
    sentiment_summary = {}
    if include_sentiment:
        all_articles = []
        for h in enriched:
            articles = NewsCrawler.get_all_news(h["ticker"], h.get("company_name"), limit=5)
            for a in articles:
                a["ticker"] = h["ticker"]
            all_articles.extend(articles)
        if all_articles:
            sentiment_df = sentiment_engine.analyze_articles(all_articles)
            sentiment_summary = sentiment_engine.summarize_sentiment(sentiment_df)

    # 8. AI insights
    insights = insight_engine.generate_insights(
        portfolio_df, sector_alloc, risk_report, div_score, r_score,
        risk_contrib, sentiment_summary)

    # Populate result container
    result.portfolio_df = portfolio_df
    result.sector_alloc = sector_alloc
    result.geo_alloc = geo_alloc
    result.price_matrix = price_matrix
    result.returns_df = returns_df
    result.risk_metrics = risk_report
    result.risk_contrib = risk_contrib
    result.div_score = div_score
    result.r_score = r_score
    result.insights = insights
    result.sentiment_df = sentiment_df
    result.sentiment_summary = sentiment_summary
    result.total_value = total_value
    result.weights = weights

    return result
