import streamlit as st
from app.data.market_data import MarketDataProvider
from app.data.company_crawler import CompanyCrawler
from app.data.news_crawler import NewsCrawler
from app.nlp import sentiment_engine
from app.utils.validators import is_valid_url

st.set_page_config(page_title="Company Intelligence | PortfolioIQ", layout="wide")
st.title("🌐 Company Intelligence Mode")
st.caption("Enter a company name (or ticker) and its official website to gather "
           "market data, crawl public pages, pull recent news, and run sentiment analysis.")

c1, c2 = st.columns(2)
company_query = c1.text_input("Company Name or Ticker", placeholder="e.g. Tesla or TSLA")
website = c2.text_input("Official Website URL", placeholder="https://www.tesla.com")

if st.button("🔍 Analyze Company", type="primary"):
    if not company_query:
        st.error("Please enter a company name or ticker.")
    else:
        with st.spinner("Resolving ticker and pulling market data..."):
            ticker = MarketDataProvider.resolve_ticker(company_query)
            info = MarketDataProvider.get_company_info(ticker)

        st.subheader(f"{info.get('company_name', ticker)} ({ticker})")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Price", f"{info.get('current_price', 'N/A')}")
        m2.metric("Sector", info.get("sector", "N/A"))
        m3.metric("Beta", info.get("beta", "N/A"))
        m4.metric("P/E Ratio", info.get("pe_ratio", "N/A"))
        st.write(info.get("business_summary", "")[:800])

        # ---- Website crawl ----
        if website and is_valid_url(website):
            with st.spinner("Crawling public pages (robots.txt respected)..."):
                crawl_result = CompanyCrawler.crawl(website)
                signals = CompanyCrawler.extract_signals(crawl_result)
            st.subheader("Website Intelligence")
            st.write(f"Pages crawled: {len(crawl_result['pages_crawled'])}")
            for p in crawl_result["pages_crawled"]:
                st.caption(p)
            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.metric("Growth Signals", "Yes" if signals["mentions_growth"] else "No")
            sc2.metric("Risk Signals", "Yes" if signals["mentions_risk"] else "No")
            sc3.metric("ESG Mentions", "Yes" if signals["mentions_esg"] else "No")
            sc4.metric("Innovation Signals", "Yes" if signals["mentions_innovation"] else "No")
        elif website:
            st.warning("Website URL doesn't look valid — skipping crawl.")

        # ---- News + sentiment ----
        with st.spinner("Gathering recent news and running sentiment analysis..."):
            articles = NewsCrawler.get_all_news(ticker, info.get("company_name"), limit=10)
            sentiment_df = sentiment_engine.analyze_articles(articles) if articles else None
            summary = sentiment_engine.summarize_sentiment(sentiment_df) if sentiment_df is not None else {}

        st.subheader("Recent News & Sentiment")
        if summary:
            s1, s2, s3 = st.columns(3)
            s1.metric("Positive", f"{summary.get('positive_pct', 0):.0f}%")
            s2.metric("Neutral", f"{summary.get('neutral_pct', 0):.0f}%")
            s3.metric("Negative", f"{summary.get('negative_pct', 0):.0f}%")
            st.dataframe(sentiment_df[["headline", "source", "label", "score"]],
                         use_container_width=True)
        else:
            st.info("No recent news found for this company.")

        # ---- Strategic observations ----
        st.subheader("🤖 Strategic Observations")
        obs = []
        if summary.get("negative_pct", 0) >= 40:
            obs.append("🔴 Elevated negative news coverage — monitor for headline risk.")
        if info.get("pe_ratio") and info["pe_ratio"] > 40:
            obs.append("🟠 P/E ratio is elevated relative to historical market averages — "
                       "growth expectations are priced in.")
        if website and is_valid_url(website) and signals.get("mentions_risk"):
            obs.append("🟠 Company website references restructuring/legal/risk-related terms.")
        if not obs:
            obs.append("🟢 No major red flags detected from available public signals.")
        for o in obs:
            st.markdown(o)
