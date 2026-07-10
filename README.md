# PortfolioIQ
### Investment Risk & Portfolio Analytics Platform

PortfolioIQ is a production-grade investment analytics platform that ingests portfolio
holdings (manual entry, Excel upload, or company/ticker lookup), pulls live market data,
computes institutional-grade risk metrics, runs NLP sentiment analysis on financial news,
generates AI-style insights/recommendations, and produces a polished PDF investment report —
all through a Streamlit dashboard backed by MySQL.

This repo is structured the way a quant/data engineering team would ship it: separated
data/analytics/nlp/reporting layers, a real relational schema, config-driven API keys, and
a deployment guide.

---

## 1. Architecture

```
                         ┌───────────────────────────┐
                         │        Streamlit UI        │
                         │  (app/streamlit_app.py)    │
                         └─────────────┬───────────────┘
                                       │
              ┌────────────────────────┼─────────────────────────┐
              │                        │                         │
      ┌───────▼────────┐     ┌─────────▼─────────┐     ┌─────────▼─────────┐
      │  Data Layer     │     │ Analytics Engine   │     │  NLP / Sentiment   │
      │ (yfinance, AV,  │     │ (risk, VaR, Sharpe,│     │  Engine (FinBERT/  │
      │  FMP, scraping) │     │  Sortino, Beta,    │     │  VADER fallback)   │
      └───────┬─────────┘     │  correlation, DD)  │     └─────────┬─────────┘
              │               └─────────┬──────────┘               │
              │                         │                          │
              └────────────┬────────────┴──────────────┬───────────┘
                            │                           │
                    ┌───────▼────────┐         ┌────────▼────────┐
                    │  MySQL Database │         │  AI Insight &    │
                    │  (schema below) │         │  Report Engine   │
                    └─────────────────┘         │  (PDF generator) │
                                                  └──────────────────┘
```

**Layered design principles**
- `app/data/` — all external I/O (market data providers, news scraping, company crawling). Nothing else talks to the network directly.
- `app/analytics/` — pure functions over pandas DataFrames (no I/O). Fully unit-testable.
- `app/nlp/` — sentiment scoring, isolated so FinBERT can be swapped for any model.
- `app/reports/` — PDF/report rendering only.
- `app/db/` — MySQL connection pool + repository pattern (no raw SQL scattered in UI code).
- `app/core/` — orchestration/services that compose the above layers for the UI.

---

## 2. Folder Structure

```
PortfolioIQ/
├── app/
│   ├── streamlit_app.py          # Main Streamlit entrypoint (multi-page)
│   ├── pages/
│   │   ├── 1_Portfolio_Input.py
│   │   ├── 2_Executive_Dashboard.py
│   │   ├── 3_Company_Intelligence.py
│   │   └── 4_Reports.py
│   ├── core/
│   │   ├── config.py              # env/config loader
│   │   ├── portfolio_service.py   # orchestrates data+analytics+nlp
│   │   └── constants.py
│   ├── data/
│   │   ├── market_data.py         # Yahoo Finance / Alpha Vantage / FMP
│   │   ├── news_crawler.py        # news + earnings scraping
│   │   └── company_crawler.py     # company website intelligence
│   ├── analytics/
│   │   ├── risk_engine.py         # Sharpe/Sortino/Beta/VaR/ES/Drawdown
│   │   ├── portfolio_metrics.py   # returns, weights, allocation
│   │   ├── diversification.py     # HHI, sector concentration, risk score
│   │   └── insight_engine.py      # rule-based + ML-assisted narrative insights
│   ├── nlp/
│   │   └── sentiment_engine.py    # FinBERT primary, VADER fallback
│   ├── reports/
│   │   └── pdf_report.py          # ReportLab-based PDF generator
│   ├── db/
│   │   ├── connection.py
│   │   └── repository.py
│   └── utils/
│       ├── validators.py
│       └── excel_parser.py
├── database/
│   └── schema.sql
├── docs/
│   ├── DEPLOYMENT_GUIDE.md
│   ├── RESUME_BULLETS.md
│   └── INTERVIEW_PREP.md
├── tests/
│   └── test_risk_engine.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## 3. Quick Start

```bash
git clone <repo_url> PortfolioIQ
cd PortfolioIQ
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env        # fill in API keys + MySQL credentials
mysql -u root -p < database/schema.sql

streamlit run app/streamlit_app.py
```

See `docs/DEPLOYMENT_GUIDE.md` for Docker/cloud deployment.

---

## 4. Feature Coverage Map

| Requirement | Module |
|---|---|
| Manual portfolio entry | `pages/1_Portfolio_Input.py` |
| Excel upload | `utils/excel_parser.py` |
| Ticker/company/ETF lookup | `data/market_data.py` |
| Company website intelligence | `data/company_crawler.py` |
| Risk metrics (Sharpe, Sortino, Beta, VaR, ES, Drawdown, Correlation) | `analytics/risk_engine.py` |
| Diversification / concentration / risk score | `analytics/diversification.py` |
| AI insight narratives | `analytics/insight_engine.py` |
| News + earnings sentiment | `data/news_crawler.py`, `nlp/sentiment_engine.py` |
| Executive dashboard | `pages/2_Executive_Dashboard.py` |
| PDF report | `reports/pdf_report.py` |
| Persistence | `db/` + `database/schema.sql` |

