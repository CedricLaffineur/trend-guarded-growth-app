# Trend-Guarded Growth — Streamlit app

Interactive companion to our investor prospectus for 2270 Financial Modeling.
The app backtests a monthly trend-following strategy on four equity ETFs (SPY, EFA, EEM, VNQ), each held only while its price is above its 10-month moving average; otherwise its 25% slice moves to a cash ETF (BIL). Results are compared with the same four ETFs held at 25% each.

**Live app:** [Streamlit URL]
**Group:** [Moodle group name] — Julia, Lucie, Pascal, Kaja, Cedric, Constantin

## What you can change
- Moving-average window (6–12 months)
- Transaction cost (0–50 bps per trade)
- Safe asset (BIL or IEF)

With the default settings the app reproduces the numbers in the prospectus and notebook.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Files
- `app.py` — the Streamlit interface
- `strategy.py` — data download, backtest and performance measures; identical to the notebook
- `requirements.txt` — dependencies

## Data
Yahoo Finance via the `yfinance` package, downloaded when the app starts (cached). Sample June 2007 – December 2025, monthly, USD.
