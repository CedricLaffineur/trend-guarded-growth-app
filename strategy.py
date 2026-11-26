"""Backtest logic for Trend-Guarded Growth.

Keep these functions IDENTICAL to notebook sections 2-6, so the app and the
prospectus show the same numbers. Owners: Pascal (data), Constantin (backtest),
Kaja (performance measures). Copy the finished versions in from the notebook.
"""

# Defaults: must match the notebook parameters cell (section 1)
START = "2006-01-01"
BACKTEST_START = "2007-06-30"
END = "2025-12-31"
RISKY = ["SPY", "EFA", "EEM", "VNQ"]
SAFE = "BIL"
RF_TICKER = "BIL"  # risk-free rate = BIL monthly return
MA_WINDOW = 10
SIGNAL_ADJUSTED = True
COST = 0.0010


def download_prices(tickers, start, end, adjusted=True):
    """Month-end closing prices, one column per ticker."""
    raise NotImplementedError("Copy from notebook section 2")


def risk_free(returns):
    """Monthly risk-free rate = BIL's monthly return."""
    raise NotImplementedError("Copy from notebook section 2")


def monthly_returns(prices):
    raise NotImplementedError("Copy from notebook section 3")


def trend_signal(prices, window):
    raise NotImplementedError("Copy from notebook section 3")


def target_weights(signal, risky, safe):
    raise NotImplementedError("Copy from notebook section 4")


def run_backtest(returns, signal, risky, safe, cost):
    raise NotImplementedError("Copy from notebook section 5")


def benchmark_returns(returns, risky, rebalance=True):
    raise NotImplementedError("Copy from notebook section 5")


def performance_table(port, bench, rf):
    raise NotImplementedError("Copy from notebook section 6")
