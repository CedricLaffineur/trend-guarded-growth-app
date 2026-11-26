"""Streamlit app for Trend-Guarded Growth.

Run locally:  pip install -r requirements.txt  then  streamlit run app.py
Owner: Cedric (with Julia). Until strategy.py is filled in, the app runs as a
placeholder, which is enough to test deployment on Streamlit Community Cloud.
"""
import streamlit as st

import strategy as s

st.set_page_config(page_title="Trend-Guarded Growth", layout="wide")
st.title("Trend-Guarded Growth")
st.caption("Monthly trend-following on SPY, EFA, EEM and VNQ, with a cash safe asset. "
           "Backtest June 2007 – December 2025, results in USD.")

with st.sidebar:
    st.header("Assumptions")
    window = st.slider("Moving-average window (months)", 6, 12, s.MA_WINDOW)
    cost_bps = st.slider("Transaction cost (bps per trade)", 0, 50, int(s.COST * 10_000))
    safe = st.selectbox("Safe asset", ["BIL", "IEF"], index=0)
    st.caption("Defaults reproduce the prospectus numbers.")


@st.cache_data(show_spinner="Downloading data…")
def load_data():
    prices_adj = s.download_prices(s.RISKY + ["BIL", "IEF"], s.START, s.END, adjusted=True)
    rf = s.risk_free(s.monthly_returns(prices_adj))
    return prices_adj, rf


try:
    prices, rf = load_data()
    # TODO (Cedric): returns -> signal -> run_backtest -> benchmark -> performance_table,
    # using window, cost_bps / 10_000 and safe; then plot cumulative performance (both start at 1)
    st.info("Data loaded. Backtest wiring still to do.")
except NotImplementedError as e:
    st.warning(f"Placeholder app: backtest functions not added yet ({e}).")
    st.write({"window": window, "cost (bps)": cost_bps, "safe asset": safe})
