import numpy as np
import pandas as pd
import pytest
from app.analytics import risk_engine, diversification


@pytest.fixture
def sample_prices():
    dates = pd.date_range("2024-01-01", periods=100, freq="B")
    rng = np.random.default_rng(42)
    data = {
        "AAA": 100 * (1 + rng.normal(0.0005, 0.01, 100)).cumprod(),
        "BBB": 50 * (1 + rng.normal(0.0003, 0.02, 100)).cumprod(),
    }
    return pd.DataFrame(data, index=dates)


def test_compute_returns_shape(sample_prices):
    returns = risk_engine.compute_returns(sample_prices)
    assert returns.shape[0] == sample_prices.shape[0] - 1


def test_portfolio_returns_weighted(sample_prices):
    returns = risk_engine.compute_returns(sample_prices)
    weights = {"AAA": 0.6, "BBB": 0.4}
    port_returns = risk_engine.portfolio_daily_returns(returns, weights)
    assert len(port_returns) == len(returns)


def test_sharpe_ratio_reasonable(sample_prices):
    returns = risk_engine.compute_returns(sample_prices)
    port_returns = risk_engine.portfolio_daily_returns(returns, {"AAA": 0.6, "BBB": 0.4})
    sharpe = risk_engine.sharpe_ratio(port_returns)
    assert isinstance(sharpe, float)


def test_max_drawdown_is_non_positive(sample_prices):
    returns = risk_engine.compute_returns(sample_prices)
    port_returns = risk_engine.portfolio_daily_returns(returns, {"AAA": 0.6, "BBB": 0.4})
    mdd = risk_engine.max_drawdown(port_returns)
    assert mdd <= 0


def test_historical_var_positive_magnitude(sample_prices):
    returns = risk_engine.compute_returns(sample_prices)
    port_returns = risk_engine.portfolio_daily_returns(returns, {"AAA": 0.6, "BBB": 0.4})
    var95 = risk_engine.historical_var(port_returns)
    assert var95 >= 0


def test_herfindahl_index_bounds():
    weights = pd.Series({"A": 0.5, "B": 0.3, "C": 0.2})
    hhi = diversification.herfindahl_index(weights)
    assert 0 <= hhi <= 1


def test_diversification_score_bounds():
    score = diversification.diversification_score(0.3, 0.2, 5)
    assert 0 <= score <= 100


def test_risk_score_bounds():
    score = diversification.risk_score(0.25, -0.15, 0.2, 0.02)
    assert 0 <= score <= 100
