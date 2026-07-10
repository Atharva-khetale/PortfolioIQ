# PortfolioIQ — Interview Preparation Guide

## 1. The 60-Second Pitch
"PortfolioIQ is an investment analytics platform I built that takes a portfolio —
entered manually, uploaded as Excel, or just a company name — and produces
institutional-grade risk analysis: Sharpe/Sortino ratios, Value at Risk, drawdown,
correlation and concentration analysis, plus news sentiment via FinBERT, all
rolled up into an executive dashboard and a downloadable PDF report. It's a
layered Python architecture — data acquisition, pure analytics, NLP, and
persistence are all separated — backed by MySQL, with Streamlit as the front end."

---

## 2. Likely Technical Questions & Model Answers

### Q: Walk me through how you calculate the Sharpe Ratio and why annualize it that way.
A: Sharpe = (mean daily excess return / daily return std dev) × √252. Excess return
subtracts the daily risk-free rate (annual rate / 252) from each day's return.
Multiplying by √252 annualizes it because variance scales linearly with time under
an i.i.d. assumption, so standard deviation scales with the square root of time —
that's why √252, not 252, is used to annualize volatility (and hence Sharpe).

### Q: What's the difference between Sharpe and Sortino, and when would you prefer one?
A: Sharpe penalizes all volatility, upside and downside equally. Sortino only
penalizes downside deviation (returns below a target, here 0/risk-free). Sortino
is more appropriate when returns are skewed or when investors don't mind upside
volatility — e.g., strategies with asymmetric payoffs like options overlays.

### Q: How did you compute VaR — walk me through historical vs parametric.
A: Historical VaR takes the empirical distribution of daily portfolio returns and
reads off the (1-confidence) percentile — e.g., the 5th percentile for 95% VaR —
no distributional assumption, but sensitive to the sample window. Parametric VaR
assumes returns are normally distributed, computing mu + z*sigma where z is the
inverse normal CDF at the confidence level. I implemented both; historical is more
robust to fat tails, parametric is smoother and needs less data.

### Q: What is Expected Shortfall and why is it better than VaR?
A: Expected Shortfall (CVaR) is the average loss *given that* the loss exceeds the
VaR threshold. VaR tells you the loss at the boundary, but says nothing about how
bad things get beyond it — ES captures tail severity, which matters more for
extreme-event risk (this is why Basel III moved from VaR to ES for market risk
capital).

### Q: How do you calculate Beta and what does it represent?
A: Beta = Cov(portfolio returns, benchmark returns) / Var(benchmark returns). It
measures systematic risk — how much the portfolio moves for a 1% move in the
benchmark. Beta > 1 means more volatile than the market; <1 means more defensive.

### Q: How did you measure portfolio concentration/diversification?
A: I used the Herfindahl-Hirschman Index (sum of squared weights) on both
individual holdings and sector weights — HHI near 0 is highly diversified, near 1
is a single-holding portfolio. I combined that with a "risk contribution"
decomposition — using the covariance matrix, RC_i = w_i × (Σw)_i / portfolio
variance — to show which holdings actually drive risk, which can differ sharply
from which holdings are largest by weight (e.g., a small, highly volatile,
uncorrelated position can dominate portfolio variance).

### Q: Why MySQL instead of a NoSQL store?
A: The data is inherently relational — portfolios have holdings, holdings
reference a securities master, risk metrics are time-stamped snapshots tied to a
portfolio. Foreign keys and joins are the natural fit, and I need ACID guarantees
for financial data (no partial writes on a holding update). I designed a normalized
schema (3NF) with a securities master table to avoid duplicating company metadata
across portfolios.

### Q: How would this scale to thousands of concurrent users?
A: Three biggest bottlenecks: (1) market data API rate limits — solved by caching
price history in `price_history` and refreshing on a schedule rather than per-request;
(2) FinBERT inference cost — I'd move sentiment scoring to a dedicated
async worker/queue (Celery + Redis) instead of inline in the request path; (3) MySQL
connection contention — already using SQLAlchemy pooling, but I'd add read replicas
for dashboard queries and keep writes on the primary.

### Q: How do you handle a ticker or API failure gracefully?
A: The data layer has explicit fallback chains — Yahoo Finance first, Alpha
Vantage/FMP as fallback — and every provider call is wrapped in try/except
returning empty structures rather than raising, so a single bad ticker doesn't
crash the whole portfolio analysis. The sentiment engine similarly falls back from
FinBERT to VADER if the transformer model fails to load.

### Q: How would you extend the "AI Insight Engine" to use an actual LLM?
A: The insight engine already takes a structured dict of computed metrics
(risk, diversification, sentiment) and returns structured insight objects — I'd
just swap the rule-based narrative generation function for a call to an LLM with
those same structured inputs in the prompt, keeping the interface identical so
nothing else in the app changes. This is a text-generation substitution, not an
architecture change — this makes the design testable and cheap to run in bulk,
with the option to add LLM polish only where it earns its cost.

### Q: What are the limitations of your risk scoring model?
A: It's a weighted heuristic (volatility, drawdown, concentration, VaR blended
with fixed weights) — transparent and explainable, but not a fitted/backtested
model. A production version would validate the weighting scheme against
realized forward risk (e.g., logistic regression or a scoring model calibrated
against historical drawdown events) rather than fixed coefficients.

---

## 3. System Design Follow-ups to Prepare For
- How would you backtest this portfolio (e.g., rolling Sharpe over time)?
- How would you add multi-currency portfolios (FX conversion, hedged vs unhedged returns)?
- How would you add factor exposure analysis (Fama-French style)?
- How would you productionize the news crawler to respect rate limits and ToS across many sources?
- How would you add authentication/authorization for multi-tenant use (the `users` table's `role` enum is the starting point)?

## 4. Behavioral / Project Story Angles
- **Why this project?** Demonstrates end-to-end ownership: data engineering, quant
  finance, ML/NLP, and product/UI — relevant to both technical and PM-adjacent roles.
- **Biggest technical challenge:** Balancing accuracy vs latency for FinBERT sentiment
  at request time — solved with a VADER fallback and by isolating sentiment as an
  optional, toggleable step in the pipeline.
- **What you'd do differently:** Add a job queue for async data refresh instead of
  synchronous fetch-on-click, and add proper backtesting/walk-forward validation for
  the risk scoring weights.
