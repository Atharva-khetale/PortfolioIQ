"""
Risk Analytics Engine — pure functions over pandas/numpy. No I/O here.

Metrics implemented:
  - Daily / Annualized Returns
  - Volatility (annualized std dev)
  - Sharpe Ratio
  - Sortino Ratio
  - Beta (vs benchmark)
  - Correlation Matrix
  - Maximum Drawdown
  - Historical VaR (95%) and Parametric VaR
  - Expected Shortfall (CVaR)
"""
import numpy as np
import pandas as pd
from app.core.config import settings

TRADING_DAYS = settings.TRADING_DAYS_PER_YEAR


def compute_returns(price_df: pd.DataFrame) -> pd.DataFrame:
    """Daily simple returns from a price matrix (columns = tickers)."""
    return price_df.pct_change().dropna(how="all")


def portfolio_daily_returns(returns_df: pd.DataFrame, weights: dict) -> pd.Series:
    """Weighted sum of asset returns -> portfolio return series."""
    aligned_weights = pd.Series({t: weights.get(t, 0) for t in returns_df.columns})
    port_returns = returns_df.fillna(0).dot(aligned_weights)
    return port_returns


def annualized_return(daily_returns: pd.Series) -> float:
    mean_daily = daily_returns.mean()
    return float((1 + mean_daily) ** TRADING_DAYS - 1)


def annualized_volatility(daily_returns: pd.Series) -> float:
    return float(daily_returns.std() * np.sqrt(TRADING_DAYS))


def sharpe_ratio(daily_returns: pd.Series, risk_free_rate: float = None) -> float:
    rf = risk_free_rate if risk_free_rate is not None else settings.RISK_FREE_RATE
    excess_daily = daily_returns - (rf / TRADING_DAYS)
    denom = daily_returns.std()
    if denom == 0 or np.isnan(denom):
        return 0.0
    return float((excess_daily.mean() / denom) * np.sqrt(TRADING_DAYS))


def sortino_ratio(daily_returns: pd.Series, risk_free_rate: float = None) -> float:
    rf = risk_free_rate if risk_free_rate is not None else settings.RISK_FREE_RATE
    excess_daily = daily_returns - (rf / TRADING_DAYS)
    downside = daily_returns[daily_returns < 0]
    downside_std = downside.std()
    if downside_std == 0 or np.isnan(downside_std):
        return 0.0
    return float((excess_daily.mean() / downside_std) * np.sqrt(TRADING_DAYS))


def beta(daily_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    aligned = pd.concat([daily_returns, benchmark_returns], axis=1).dropna()
    if len(aligned) < 2:
        return 0.0
    cov = aligned.iloc[:, 0].cov(aligned.iloc[:, 1])
    var = aligned.iloc[:, 1].var()
    if var == 0:
        return 0.0
    return float(cov / var)


def correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
    return returns_df.corr()


def max_drawdown(daily_returns: pd.Series) -> float:
    cumulative = (1 + daily_returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    return float(drawdown.min())  # negative number, e.g. -0.23 = -23%


def historical_var(daily_returns: pd.Series, confidence: float = None) -> float:
    conf = confidence if confidence is not None else settings.VAR_CONFIDENCE
    if daily_returns.empty:
        return 0.0
    return float(-np.percentile(daily_returns, (1 - conf) * 100))


def parametric_var(daily_returns: pd.Series, confidence: float = None) -> float:
    from scipy.stats import norm
    conf = confidence if confidence is not None else settings.VAR_CONFIDENCE
    mu, sigma = daily_returns.mean(), daily_returns.std()
    z = norm.ppf(1 - conf)
    return float(-(mu + z * sigma))


def expected_shortfall(daily_returns: pd.Series, confidence: float = None) -> float:
    """Conditional VaR — average loss beyond the VaR threshold."""
    conf = confidence if confidence is not None else settings.VAR_CONFIDENCE
    var_threshold = -historical_var(daily_returns, conf)
    tail_losses = daily_returns[daily_returns <= var_threshold]
    if tail_losses.empty:
        return historical_var(daily_returns, conf)
    return float(-tail_losses.mean())


def full_risk_report(price_df: pd.DataFrame, weights: dict,
                      benchmark_returns: pd.Series = None) -> dict:
    """
    Orchestrates all risk metrics into a single dict.
    price_df: DataFrame of close prices, columns = tickers.
    weights: {ticker: weight} summing to 1.
    """
    returns_df = compute_returns(price_df)
    port_returns = portfolio_daily_returns(returns_df, weights)

    report = {
        "daily_return": float(port_returns.mean()),
        "annual_return": annualized_return(port_returns),
        "volatility": annualized_volatility(port_returns),
        "sharpe_ratio": sharpe_ratio(port_returns),
        "sortino_ratio": sortino_ratio(port_returns),
        "max_drawdown": max_drawdown(port_returns),
        "var_95": historical_var(port_returns),
        "parametric_var_95": parametric_var(port_returns),
        "expected_shortfall_95": expected_shortfall(port_returns),
        "correlation_matrix": correlation_matrix(returns_df),
        "portfolio_returns_series": port_returns,
    }

    if benchmark_returns is not None:
        report["beta"] = beta(port_returns, benchmark_returns)
    else:
        report["beta"] = None

    return report
