"""Streamlit app for Trend-Guarded Growth.

Run locally:  pip install -r requirements.txt  then  streamlit run app.py
Owner: Cedric (with Julia).

How it works
------------
All numbers come from strategy.py, which holds the SAME functions as the
notebook (sections 2-6). While those functions still raise NotImplementedError,
the app falls back to clearly labelled DUMMY data so the layout can be tested
and deployed. Once strategy.py is filled in (step C4), the app switches to the
real backtest automatically: nothing below needs to change, except possibly
the few lines inside `run_real_backtest` if a function signature differs.
"""
import numpy as np
import pandas as pd
import streamlit as st

import strategy as s

REPO_URL = "https://github.com/CedricLaffineur/trend-guarded-growth-app"

st.set_page_config(page_title="Trend-Guarded Growth", layout="wide")


# ---------------------------------------------------------------------------
# 1. Controls (defaults = base case in the prospectus: 10 months, 10 bps, BIL)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Assumptions")
    window = st.slider("Moving-average window (months)", 6, 12, s.MA_WINDOW,
                       help="An ETF is held while its month-end price is above "
                            "its average over this many months.")
    cost_bps = st.slider("Transaction cost (bps per trade)", 0, 50,
                         int(round(s.COST * 10_000)),
                         help="Charged on the value traded at each monthly reset.")
    safe = st.selectbox("Safe asset", ["BIL", "IEF"], index=0,
                        help="Where a 25% slice goes when its ETF is below trend. "
                             "BIL = 1-3 month T-bills; IEF = 7-10 year Treasuries.")
    is_default = (window == s.MA_WINDOW
                  and cost_bps == int(round(s.COST * 10_000))
                  and safe == s.SAFE)
    if is_default:
        st.success("Base case: reproduces the prospectus numbers.")
    else:
        st.info("Changed from the base case in the prospectus.")


# ---------------------------------------------------------------------------
# 2. Real backtest: calls strategy.py only (same code as the notebook)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Downloading data from Yahoo Finance…")
def load_data():
    tickers = s.RISKY + ["BIL", "IEF"]
    prices_adj = s.download_prices(tickers, s.START, s.END, adjusted=True)
    prices_sig = (prices_adj if s.SIGNAL_ADJUSTED
                  else s.download_prices(tickers, s.START, s.END, adjusted=False))
    returns = s.monthly_returns(prices_adj)
    rf = s.risk_free(returns)
    return prices_sig, returns, rf


@st.cache_data(show_spinner="Running backtest…")
def run_real_backtest(window, cost, safe):
    """Return (strategy returns, benchmark returns, rf, metrics table)."""
    prices_sig, returns, rf = load_data()
    signal = s.trend_signal(prices_sig[s.RISKY], window)
    port = s.run_backtest(returns, signal, s.RISKY, safe, cost)
    if isinstance(port, tuple):          # e.g. (returns, weights, turnover)
        port = port[0]
    bench = s.benchmark_returns(returns, s.RISKY, rebalance=True)

    # Same sample as the prospectus: BACKTEST_START to END
    data = pd.concat({"Strategy": port, "Benchmark": bench, "rf": rf}, axis=1, sort=True)
    data = data.loc[s.BACKTEST_START:s.END].dropna()
    table = s.performance_table(data["Strategy"], data["Benchmark"], data["rf"])
    return data["Strategy"], data["Benchmark"], data["rf"], table


# ---------------------------------------------------------------------------
# 3. Dummy backtest: ONLY used while strategy.py is unfinished (layout test)
# ---------------------------------------------------------------------------
def _dummy_metrics(p, b, rf):
    """Rough metrics for the dummy preview. NOT used for real results."""
    ep, eb, act = p - rf, b - rf, p - b
    beta = np.cov(ep, eb)[0, 1] / np.var(eb, ddof=1)
    alpha = 12 * (ep.mean() - beta * eb.mean())

    def mdd(r):
        idx = (1 + r).cumprod()
        return (idx / idx.cummax() - 1).min()

    def col(r, is_port):
        row = {
            "Annualised average return": 12 * r.mean(),
            "Volatility (annualised)": np.sqrt(12) * r.std(),
            "Sharpe ratio": (12 * (r - rf).mean()) / (np.sqrt(12) * (r - rf).std()),
            "Alpha (annualised)": alpha if is_port else 0.0,
            "Beta (monthly, not annualised)": beta if is_port else 1.0,
            "Information ratio": ((12 * act.mean()) / (np.sqrt(12) * act.std())
                                  if is_port else np.nan),
            "Maximum drawdown": mdd(r),
        }
        return pd.Series(row)

    return pd.DataFrame({"Strategy": col(p, True), "Benchmark": col(b, False)})


def run_dummy_backtest(window, cost, safe):
    """Synthetic monthly returns with the same shape as the real output."""
    idx = pd.date_range(s.BACKTEST_START, s.END, freq="ME")
    rng = np.random.default_rng(42)
    rf = pd.Series(0.0012, index=idx)
    bench = pd.Series(rng.normal(0.0065, 0.05, len(idx)), index=idx)
    # Toy rule so the controls visibly change the output
    trend = (bench.rolling(window, min_periods=1).mean().shift(1) > 0).astype(float)
    safe_ret = rf if safe == "BIL" else pd.Series(rng.normal(0.003, 0.018, len(idx)), index=idx)
    port = 0.5 * bench + 0.5 * (trend * bench + (1 - trend) * safe_ret) - cost * 0.3
    return port, bench, rf, _dummy_metrics(port, bench, rf)


# ---------------------------------------------------------------------------
# 4. Pick real or dummy
# ---------------------------------------------------------------------------
is_dummy = False
try:
    port, bench, rf, table = run_real_backtest(window, cost_bps / 10_000, safe)
except NotImplementedError as e:
    is_dummy = True
    port, bench, rf, table = run_dummy_backtest(window, cost_bps / 10_000, safe)
    missing = str(e)
except Exception as e:  # real bug or data problem: show it, don't hide it
    st.error(f"The backtest failed: {type(e).__name__}: {e}")
    st.stop()


# ---------------------------------------------------------------------------
# 5. Page
# ---------------------------------------------------------------------------
st.title("Trend-Guarded Growth")
st.caption("Monthly trend-following on SPY, EFA, EEM and VNQ (25% each), each slice "
           "moved to a safe asset when below its moving average. Benchmark: the "
           "same four ETFs at 25% each, reset monthly. Results in USD.")

if is_dummy:
    st.warning(f"**DUMMY DATA. Layout preview only, not real results.** "
               f"The backtest functions in strategy.py are not added yet ({missing}).")

start_lbl = port.index[0].strftime("%b %Y")
end_lbl = port.index[-1].strftime("%b %Y")

# Headline tiles: strategy, with the difference from the benchmark.
# They need these row labels in performance_table's output (columns "Strategy", "Benchmark").
TILE_ROWS = ["Annualised average return", "Volatility (annualised)",
             "Sharpe ratio", "Maximum drawdown"]
t = table
if not set(TILE_ROWS) <= set(t.index):
    st.info("Headline tiles hidden: performance_table uses different row labels. "
            "The full table below is still correct.")
    c1 = c2 = c3 = c4 = None
else:
    c1, c2, c3, c4 = st.columns(4)
if c1 is not None:
    c1.metric("Annualised return", f"{t.loc['Annualised average return', 'Strategy']:.2%}",
              f"{t.loc['Annualised average return', 'Strategy'] - t.loc['Annualised average return', 'Benchmark']:+.2%} vs benchmark")
    c2.metric("Volatility", f"{t.loc['Volatility (annualised)', 'Strategy']:.2%}",
              f"{t.loc['Volatility (annualised)', 'Strategy'] - t.loc['Volatility (annualised)', 'Benchmark']:+.2%} vs benchmark",
              delta_color="inverse")
    c3.metric("Sharpe ratio", f"{t.loc['Sharpe ratio', 'Strategy']:.2f}",
              f"{t.loc['Sharpe ratio', 'Strategy'] - t.loc['Sharpe ratio', 'Benchmark']:+.2f} vs benchmark")
    c4.metric("Maximum drawdown", f"{t.loc['Maximum drawdown', 'Strategy']:.1%}",
              f"{t.loc['Maximum drawdown', 'Strategy'] - t.loc['Maximum drawdown', 'Benchmark']:+.1%} vs benchmark")

# Cumulative performance, both series start at 1
st.subheader(f"Cumulative performance, {start_lbl} – {end_lbl} (both start at 1)")
cum = (1 + pd.concat({"Strategy": port, "Benchmark": bench}, axis=1)).cumprod()
start_row = pd.DataFrame({"Strategy": [1.0], "Benchmark": [1.0]},
                         index=[port.index[0] - pd.offsets.MonthEnd(1)])
cum = pd.concat([start_row, cum])
st.line_chart(cum, x_label="Date", y_label="Value of 1 USD invested",
              color=["#1f6feb", "#9aa5b1"])  # Strategy blue, Benchmark grey (column order)

# Drawdowns: the risk the client actually feels
with st.expander("Drawdowns (fall from previous peak)"):
    dd = cum / cum.cummax() - 1
    st.area_chart(dd, x_label="Date", y_label="Drawdown",
                  color=["#1f6feb", "#9aa5b1"])

# Full metrics table
st.subheader("Performance measures")
pct_rows = ["Annualised average return", "Volatility (annualised)",
            "Alpha (annualised)", "Maximum drawdown"]
shown = table.copy().astype(object)
for r in shown.index:
    for c in shown.columns:
        v = table.loc[r, c]
        if pd.isna(v):
            shown.loc[r, c] = "–"
        elif r in pct_rows:
            shown.loc[r, c] = f"{v:.2%}"
        else:
            shown.loc[r, c] = f"{v:.2f}"
st.table(shown)

st.caption(
    "Monthly returns. Annualised return = mean monthly return × 12; volatility = "
    "monthly standard deviation × √12. Sharpe ratio uses excess returns over the "
    "risk-free rate (BIL's monthly return). Alpha and beta come from an OLS regression "
    "of strategy excess returns on benchmark excess returns; alpha = intercept × 12, "
    "beta is not annualised. Information ratio = annualised mean active return ÷ "
    "annualised tracking error. Signals at month-end t set holdings for month t+1."
)

st.divider()
st.caption(f"Data: Yahoo Finance via yfinance. Source code: [{REPO_URL}]({REPO_URL}). "
           "Same functions as the group's Colab notebook. Past performance does not "
           "guarantee future results.")
