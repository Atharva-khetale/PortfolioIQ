# PortfolioIQ — Resume Bullet Points

Use/adapt the bullets below depending on the role you're targeting (Quant Dev,
Data Engineer, FinTech Full-Stack, Analytics/PM).

## Quant / Risk-focused
- Designed and built **PortfolioIQ**, a full-stack investment analytics platform computing institutional-grade risk metrics (Sharpe, Sortino, Beta, VaR, Expected Shortfall, Maximum Drawdown, correlation matrices) across multi-asset portfolios using Python, Pandas, and NumPy.
- Implemented a composite **Risk Scoring Engine** and **Diversification Scoring Engine** using Herfindahl-Hirschman concentration indices and portfolio-variance-based risk contribution decomposition, surfacing which holdings drive the majority of portfolio risk.
- Built a historical & parametric **Value-at-Risk / Expected Shortfall** module validated against 250+ trading-day price histories pulled from live market data APIs (Yahoo Finance, Alpha Vantage, Financial Modeling Prep).

## Data Engineering-focused
- Architected a layered data pipeline separating market-data acquisition, risk analytics, NLP, and persistence, enabling independent testing and swap-in of data providers (Yahoo Finance primary, Alpha Vantage/FMP fallback) without touching downstream logic.
- Designed a normalized **MySQL schema** (9 tables: users, portfolios, securities, holdings, price_history, risk_metrics, sentiment_records, ai_insights, reports) supporting historical price caching, auditable risk snapshots, and report generation lineage.
- Built a repository-pattern data access layer over SQLAlchemy, eliminating raw SQL from UI/business logic and enabling connection pooling for concurrent multi-user analytics sessions.

## Full-Stack FinTech-focused
- Shipped **PortfolioIQ**, an end-to-end Streamlit application supporting manual portfolio entry, Excel bulk upload, and free-text company/ticker lookup, backed by a MySQL persistence layer and a Python analytics/NLP backend.
- Built an **Executive Dashboard** with Plotly-powered correlation heatmaps, sector/geographic allocation charts, and risk-contribution visualizations, plus a one-click **PDF report generator** (ReportLab) producing client-ready investment reports.
- Implemented a **Company Website Intelligence** module performing robots.txt-compliant crawling of public company pages to extract growth/risk/ESG/innovation signals, combined with FinBERT-based sentiment scoring of financial news headlines.

## AI/ML-focused
- Integrated **FinBERT** (domain-tuned financial sentiment transformer) with a VADER lexicon-based fallback for robust, always-available sentiment scoring of news and earnings coverage across portfolio holdings.
- Built a rule-based **AI Insight Engine** that synthesizes risk, concentration, and sentiment signals into plain-English investment recommendations (e.g., concentration warnings, rebalancing suggestions), with scikit-learn KMeans clustering for holding-behavior grouping.
- Designed the insight-generation layer with a structured input/output contract so the rule-based narrative logic can be swapped for an LLM-backed generator without changing any upstream analytics code.

## Metrics-style bullets (quantify if you can, adjust numbers to your actual build/testing)
- Reduced portfolio risk-analysis turnaround from a manual multi-spreadsheet process to a **single-click analysis pipeline** producing 10+ risk metrics and a PDF report in under a minute.
- Covered core analytics logic with a **pytest suite** validating statistical correctness of Sharpe/Sortino/VaR/drawdown calculations against synthetic and historical data.
