"""
Diversification & Portfolio Health Scoring Engine.

Uses Herfindahl-Hirschman Index (HHI) for concentration, combined with
volatility, correlation, and drawdown to produce a composite Risk Score
(0-100, higher = riskier) and Diversification Score (0-100, higher = better).
"""
import numpy as np
import pandas as pd


def herfindahl_index(weights: pd.Series) -> float:
    """HHI on holding weights. Ranges 0 (perfectly diversified) to 1 (single holding)."""
    return float((weights ** 2).sum())


def sector_concentration(sector_alloc_df: pd.DataFrame) -> dict:
    """Returns top sector weight and HHI on sector weights."""
    if sector_alloc_df.empty:
        return {"top_sector": None, "top_sector_weight": 0, "sector_hhi": 0}
    weights = sector_alloc_df["weight_pct"] / 100
    return {
        "top_sector": sector_alloc_df.iloc[0]["sector"],
        "top_sector_weight": float(sector_alloc_df.iloc[0]["weight_pct"]),
        "sector_hhi": herfindahl_index(weights),
    }


def risk_contribution(weights: pd.Series, cov_matrix: pd.DataFrame) -> pd.Series:
    """
    Marginal risk contribution of each holding to total portfolio variance.
    RC_i = w_i * (Cov * w)_i / portfolio_variance
    """
    w = weights.reindex(cov_matrix.columns).fillna(0).values
    port_var = w @ cov_matrix.values @ w.T
    if port_var == 0:
        return pd.Series(0, index=cov_matrix.columns)
    marginal = cov_matrix.values @ w
    contrib = w * marginal / port_var
    return pd.Series(contrib, index=cov_matrix.columns).sort_values(ascending=False)


def diversification_score(holding_hhi: float, sector_hhi: float, num_holdings: int) -> float:
    """
    Composite 0-100 score. Lower HHI and more holdings => higher score.
    Weighted blend: 50% holding concentration, 30% sector concentration,
    20% breadth (number of holdings, capped at 20 for full credit).
    """
    holding_component = (1 - holding_hhi) * 50
    sector_component = (1 - sector_hhi) * 30
    breadth_component = min(num_holdings / 20, 1) * 20
    score = holding_component + sector_component + breadth_component
    return float(round(max(0, min(100, score)), 2))


def risk_score(volatility: float, max_dd: float, holding_hhi: float,
                var_95: float) -> float:
    """
    Composite 0-100 risk score (higher = riskier), blending:
      - Annualized volatility (normalized against 60% as "very high")
      - Max drawdown magnitude (normalized against 50% as "very high")
      - Concentration (HHI)
      - VaR magnitude (normalized against 10% daily as "very high")
    """
    vol_component = min(volatility / 0.60, 1) * 35
    dd_component = min(abs(max_dd) / 0.50, 1) * 25
    conc_component = min(holding_hhi / 0.30, 1) * 25   # HHI>0.3 already very concentrated
    var_component = min(abs(var_95) / 0.10, 1) * 15
    score = vol_component + dd_component + conc_component + var_component
    return float(round(max(0, min(100, score)), 2))


def risk_band(score: float) -> str:
    if score < 30:
        return "Low Risk"
    elif score < 60:
        return "Moderate Risk"
    elif score < 80:
        return "High Risk"
    return "Very High Risk"
