"""
Repository layer — all raw SQL lives here, never in UI/analytics code.
Uses plain SQL via SQLAlchemy `text()` for transparency (no heavy ORM models
needed for a project of this scope, but easy to swap for ORM classes later).
"""
from sqlalchemy import text
from app.db.connection import get_engine

engine = get_engine()


class PortfolioRepository:

    @staticmethod
    def create_user(full_name: str, email: str, role: str = "CLIENT") -> int:
        with engine.begin() as conn:
            result = conn.execute(
                text("""INSERT INTO users (full_name, email, role)
                        VALUES (:name, :email, :role)
                        ON DUPLICATE KEY UPDATE full_name = :name"""),
                {"name": full_name, "email": email, "role": role},
            )
            row = conn.execute(text("SELECT user_id FROM users WHERE email=:e"),
                                {"e": email}).fetchone()
            return row[0]

    @staticmethod
    def create_portfolio(user_id: int, name: str, source: str = "MANUAL",
                          currency: str = "INR") -> int:
        with engine.begin() as conn:
            result = conn.execute(
                text("""INSERT INTO portfolios (user_id, portfolio_name, source, base_currency)
                        VALUES (:u, :n, :s, :c)"""),
                {"u": user_id, "n": name, "s": source, "c": currency},
            )
            return result.lastrowid

    @staticmethod
    def upsert_security(ticker: str, company_name: str, sector: str,
                         industry: str, country: str, exchange: str,
                         currency: str, asset_class: str = "EQUITY",
                         website: str = None) -> int:
        with engine.begin() as conn:
            conn.execute(
                text("""INSERT INTO securities
                            (ticker, company_name, sector, industry, country,
                             exchange, currency, asset_class, website)
                        VALUES (:t,:cn,:s,:i,:co,:ex,:cur,:ac,:w)
                        ON DUPLICATE KEY UPDATE
                            company_name=:cn, sector=:s, industry=:i,
                            country=:co, exchange=:ex, currency=:cur,
                            asset_class=:ac, website=:w"""),
                {"t": ticker, "cn": company_name, "s": sector, "i": industry,
                 "co": country, "ex": exchange, "cur": currency,
                 "ac": asset_class, "w": website},
            )
            row = conn.execute(text("SELECT security_id FROM securities WHERE ticker=:t"),
                                {"t": ticker}).fetchone()
            return row[0]

    @staticmethod
    def add_holding(portfolio_id: int, security_id: int, quantity: float,
                     purchase_price: float, purchase_date=None):
        with engine.begin() as conn:
            conn.execute(
                text("""INSERT INTO holdings
                            (portfolio_id, security_id, quantity, purchase_price, purchase_date)
                        VALUES (:p, :s, :q, :pp, :pd)"""),
                {"p": portfolio_id, "s": security_id, "q": quantity,
                 "pp": purchase_price, "pd": purchase_date},
            )

    @staticmethod
    def save_risk_metrics(portfolio_id: int, metrics: dict):
        with engine.begin() as conn:
            conn.execute(
                text("""INSERT INTO risk_metrics
                    (portfolio_id, total_value, daily_return, annual_return,
                     volatility, sharpe_ratio, sortino_ratio, beta, max_drawdown,
                     var_95, expected_shortfall_95, diversification_score, risk_score)
                    VALUES
                    (:pid, :tv, :dr, :ar, :vol, :sharpe, :sortino, :beta, :mdd,
                     :var, :es, :div, :risk)"""),
                {
                    "pid": portfolio_id,
                    "tv": metrics.get("total_value"),
                    "dr": metrics.get("daily_return"),
                    "ar": metrics.get("annual_return"),
                    "vol": metrics.get("volatility"),
                    "sharpe": metrics.get("sharpe_ratio"),
                    "sortino": metrics.get("sortino_ratio"),
                    "beta": metrics.get("beta"),
                    "mdd": metrics.get("max_drawdown"),
                    "var": metrics.get("var_95"),
                    "es": metrics.get("expected_shortfall_95"),
                    "div": metrics.get("diversification_score"),
                    "risk": metrics.get("risk_score"),
                },
            )

    @staticmethod
    def save_insight(portfolio_id: int, insight_type: str, text_: str,
                      severity: str = "INFO"):
        with engine.begin() as conn:
            conn.execute(
                text("""INSERT INTO ai_insights (portfolio_id, insight_type, insight_text, severity)
                        VALUES (:p, :t, :txt, :sev)"""),
                {"p": portfolio_id, "t": insight_type, "txt": text_, "sev": severity},
            )

    @staticmethod
    def save_sentiment(security_id: int, headline: str, source: str, url: str,
                        published_at, label: str, score: float):
        with engine.begin() as conn:
            conn.execute(
                text("""INSERT INTO sentiment_records
                        (security_id, headline, source, url, published_at,
                         sentiment_label, sentiment_score)
                        VALUES (:s,:h,:src,:u,:pub,:lbl,:sc)"""),
                {"s": security_id, "h": headline, "src": source, "u": url,
                 "pub": published_at, "lbl": label, "sc": score},
            )

    @staticmethod
    def get_portfolio_holdings(portfolio_id: int):
        with engine.connect() as conn:
            rows = conn.execute(
                text("""SELECT h.holding_id, s.ticker, s.company_name, s.sector,
                               h.quantity, h.purchase_price
                        FROM holdings h
                        JOIN securities s ON h.security_id = s.security_id
                        WHERE h.portfolio_id = :p"""),
                {"p": portfolio_id},
            ).fetchall()
            return [dict(r._mapping) for r in rows]
