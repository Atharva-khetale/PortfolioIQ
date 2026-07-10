"""
AI Insight Engine.

Generates human-readable narrative insights and recommendations from the
computed risk/diversification/sentiment outputs. This is a rule-based
"expert system" — transparent, auditable, and fast — augmented by
scikit-learn's KMeans for holding-cluster commentary. It's straightforward
to later swap the narrative layer for an LLM call while keeping the same
structured inputs.
"""
import pandas as pd
from sklearn.cluster import KMeans


def generate_insights(portfolio_df: pd.DataFrame, sector_alloc: pd.DataFrame,
                       risk_metrics: dict, div_score: float, r_score: float,
                       risk_contrib: pd.Series, sentiment_summary: dict = None) -> list:
    """
    Returns a list of dicts: {type, text, severity}
    """
    insights = []

    # --- Concentration ---
    if not sector_alloc.empty:
        top = sector_alloc.iloc[0]
        if top["weight_pct"] >= 40:
            insights.append({
                "type": "CONCENTRATION",
                "text": (f"Portfolio is heavily concentrated in {top['sector']} "
                         f"({top['weight_pct']:.1f}% of holdings). Consider trimming "
                         f"exposure to reduce single-sector risk."),
                "severity": "CRITICAL" if top["weight_pct"] >= 60 else "WARNING",
            })
        elif top["weight_pct"] >= 25:
            insights.append({
                "type": "CONCENTRATION",
                "text": (f"{top['sector']} is the largest sector exposure at "
                         f"{top['weight_pct']:.1f}%. This is within a reasonable "
                         f"range but worth monitoring."),
                "severity": "INFO",
            })

    # --- Holding-level risk contribution ---
    if risk_contrib is not None and not risk_contrib.empty:
        top2 = risk_contrib.head(2)
        top2_pct = top2.sum() * 100
        if top2_pct >= 50:
            names = ", ".join(top2.index)
            insights.append({
                "type": "RISK",
                "text": (f"{top2_pct:.0f}% of total portfolio risk originates from just "
                         f"two holdings ({names}). Risk is not evenly distributed across "
                         f"the portfolio."),
                "severity": "CRITICAL" if top2_pct >= 65 else "WARNING",
            })

    # --- Diversification score narrative ---
    if div_score < 40:
        band = "Low"
        sev = "CRITICAL"
    elif div_score < 65:
        band = "Moderate"
        sev = "WARNING"
    else:
        band = "Good"
        sev = "INFO"
    insights.append({
        "type": "DIVERSIFICATION",
        "text": f"Diversification Score: {div_score:.1f}/100 ({band}).",
        "severity": sev,
    })

    # --- Risk score narrative ---
    from app.analytics.diversification import risk_band
    insights.append({
        "type": "RISK",
        "text": f"Composite Risk Score: {r_score:.1f}/100 ({risk_band(r_score)}).",
        "severity": "CRITICAL" if r_score >= 80 else ("WARNING" if r_score >= 60 else "INFO"),
    })

    # --- Sharpe / Sortino commentary ---
    sharpe = risk_metrics.get("sharpe_ratio", 0)
    if sharpe < 0:
        insights.append({
            "type": "RISK",
            "text": ("Sharpe Ratio is negative, indicating the portfolio has "
                      "underperformed the risk-free rate on a risk-adjusted basis."),
            "severity": "WARNING",
        })
    elif sharpe > 1.5:
        insights.append({
            "type": "GENERAL",
            "text": f"Strong risk-adjusted performance — Sharpe Ratio of {sharpe:.2f}.",
            "severity": "INFO",
        })

    # --- Drawdown ---
    mdd = risk_metrics.get("max_drawdown", 0)
    if mdd <= -0.30:
        insights.append({
            "type": "RISK",
            "text": (f"Maximum drawdown of {mdd*100:.1f}% indicates significant historical "
                      f"downside — consider hedging or reducing beta exposure."),
            "severity": "WARNING",
        })

    # --- VaR ---
    var95 = risk_metrics.get("var_95", 0)
    insights.append({
        "type": "RISK",
        "text": (f"At 95% confidence, the portfolio is not expected to lose more than "
                  f"{var95*100:.2f}% in a single day under normal market conditions."),
        "severity": "INFO",
    })

    # --- Sentiment overlay ---
    if sentiment_summary:
        neg_pct = sentiment_summary.get("negative_pct", 0)
        if neg_pct >= 40:
            insights.append({
                "type": "SENTIMENT",
                "text": (f"{neg_pct:.0f}% of recent news coverage across portfolio holdings "
                          f"is negative — elevated headline risk detected."),
                "severity": "WARNING",
            })
        elif sentiment_summary.get("positive_pct", 0) >= 60:
            insights.append({
                "type": "SENTIMENT",
                "text": "Recent news sentiment across holdings is predominantly positive.",
                "severity": "INFO",
            })

    # --- Rebalancing suggestion ---
    insights.append(generate_rebalance_suggestion(portfolio_df, sector_alloc))

    return insights


def generate_rebalance_suggestion(portfolio_df: pd.DataFrame, sector_alloc: pd.DataFrame) -> dict:
    if sector_alloc.empty:
        return {"type": "REBALANCE", "text": "Insufficient data for rebalancing suggestion.",
                "severity": "INFO"}
    top = sector_alloc.iloc[0]
    if top["weight_pct"] >= 35:
        target_trim = top["weight_pct"] - 25
        return {
            "type": "REBALANCE",
            "text": (f"Recommendation: Trim {top['sector']} exposure by approximately "
                      f"{target_trim:.0f} percentage points and reallocate into underweight "
                      f"sectors to bring concentration closer to a 25% ceiling per sector."),
            "severity": "WARNING",
        }
    return {
        "type": "REBALANCE",
        "text": "Current sector allocation is within reasonable concentration limits; no urgent rebalancing required.",
        "severity": "INFO",
    }


def cluster_holdings(portfolio_df: pd.DataFrame, returns_df: pd.DataFrame, n_clusters: int = 3):
    """
    Optional ML augmentation: cluster holdings by return-profile
    (mean return, volatility) using KMeans, for the 'similar-behavior'
    grouping shown on the dashboard.
    """
    if returns_df.shape[1] < n_clusters:
        n_clusters = max(1, returns_df.shape[1])
    stats = pd.DataFrame({
        "mean_return": returns_df.mean(),
        "volatility": returns_df.std(),
    }).dropna()
    if len(stats) < n_clusters:
        stats["cluster"] = 0
        return stats
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    stats["cluster"] = km.fit_predict(stats[["mean_return", "volatility"]])
    return stats
