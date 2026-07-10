"""
Portfolio-level valuation and allocation metrics.
"""
import pandas as pd


def compute_market_values(holdings: list, latest_prices: dict) -> pd.DataFrame:
    """
    holdings: list of dicts with keys ticker, quantity, purchase_price, sector
    latest_prices: {ticker: current_price}
    Returns a DataFrame with market_value, weight, unrealized_pnl, pnl_pct.
    """
    df = pd.DataFrame(holdings)
    df["current_price"] = df["ticker"].map(latest_prices)
    df["market_value"] = df["quantity"] * df["current_price"]
    df["cost_basis"] = df["quantity"] * df["purchase_price"]
    df["unrealized_pnl"] = df["market_value"] - df["cost_basis"]
    df["pnl_pct"] = (df["unrealized_pnl"] / df["cost_basis"]).replace([float("inf"), -float("inf")], 0)

    total_value = df["market_value"].sum()
    df["weight"] = df["market_value"] / total_value if total_value > 0 else 0
    return df


def sector_allocation(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    alloc = portfolio_df.groupby("sector")["market_value"].sum().reset_index()
    alloc["weight_pct"] = alloc["market_value"] / alloc["market_value"].sum() * 100
    return alloc.sort_values("weight_pct", ascending=False)


def geographic_allocation(portfolio_df: pd.DataFrame) -> pd.DataFrame:
    if "country" not in portfolio_df.columns:
        return pd.DataFrame()
    alloc = portfolio_df.groupby("country")["market_value"].sum().reset_index()
    alloc["weight_pct"] = alloc["market_value"] / alloc["market_value"].sum() * 100
    return alloc.sort_values("weight_pct", ascending=False)


def get_weights_dict(portfolio_df: pd.DataFrame) -> dict:
    return dict(zip(portfolio_df["ticker"], portfolio_df["weight"]))


def total_portfolio_value(portfolio_df: pd.DataFrame) -> float:
    return float(portfolio_df["market_value"].sum())
