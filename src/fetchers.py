# src/fetchers.py
import time
import pandas as pd
import yfinance as yf
import requests
import logging

log = logging.getLogger(__name__)

# --- Static Tickers ---
INDEX_TICKERS = {
    "NIFTY 50": "^NSEI",
    "NIFTY BANK": "^NSEBANK",
    "SENSEX": "^BSESN",
    "S&P 500": "^GSPC",
    "DOW JONES": "^DJI",
    "NASDAQ": "^IXIC",
    "FTSE 100": "^FTSE",
    "DAX": "^GDAXI",
    "NIKKEI 225": "^N225",
    "HANG SENG": "^HSI",
    "SHANGHAI COMP": "000001.SS",
}

CURRENCY_TICKERS = {
    "USD/INR": "USDINR=X",
    "EUR/INR": "EURINR=X",
    "GBP/INR": "GBPINR=X",
    "JPY/INR": "JPYINR=X",
}

COMMODITY_TICKERS = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Crude Oil": "CL=F",
    "Natural Gas": "NG=F",
}

CRYPTO_TICKERS = {
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
}

# --- Helpers ---
def _pct(a, b):
    try:
        if b == 0 or b is None:
            return None
        return (a - b) / b * 100.0
    except Exception:
        return None


def _flatten_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure Yahoo Finance DataFrame has flat column names.
    """
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    return df


def get_snapshots(tickers: dict):
    """
    Returns dict: name -> {Open, Close, Change%, LTP}
    """
    data = {}
    for name, symbol in tickers.items():
        try:
            df = yf.download(
                symbol, period="2d", interval="1d",
                progress=False, threads=False, auto_adjust=False
            )
            if df is None or df.empty:
                continue

            df = _flatten_df(df)
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2] if len(df) > 1 else last_row

            open_price = float(last_row["Open"])
            close_price = float(last_row["Close"])
            prev_close = float(prev_row["Close"])

            data[name] = {
                "Open": open_price,
                "Close": close_price,
                "Change%": _pct(close_price, prev_close),
                "LTP": close_price,
            }
        except Exception as e:
            log.error(f"Error fetching {name} ({symbol}): {e}")
    return data


def get_index_history(symbol: str, period="6mo", interval="1d"):
    """
    Returns a DataFrame with columns Open, High, Low, Close (or empty DataFrame).
    """
    try:
        df = yf.download(
            symbol, period=period, interval=interval,
            progress=False, threads=False, auto_adjust=False
        )
        if df is None or df.empty:
            return pd.DataFrame()

        df = _flatten_df(df)

        expected = ["Open", "High", "Low", "Close"]
        if all(col in df.columns for col in expected):
            return df[expected].copy()
        return df.copy()
    except Exception as e:
        log.error(f"Error fetching history for {symbol}: {e}")
        return pd.DataFrame()


def get_nifty50_constituents():
    url = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"
    try:
        df = pd.read_csv(url)
        if "Symbol" in df.columns:
            df["YahooSymbol"] = df["Symbol"].astype(str).apply(lambda s: f"{s}.NS")
        return df
    except Exception as e:
        log.error(f"Error fetching NIFTY 50 constituents: {e}")
        return pd.DataFrame(columns=["Symbol", "YahooSymbol", "Sector"])


def top_movers_from_universe(universe, n=5):
    gainers, losers = pd.DataFrame(), pd.DataFrame()
    try:
        rows = []
        for _, row in universe.iterrows():
            sym = str(row.get("YahooSymbol", ""))
            base = str(row.get("Symbol", sym))
            if not sym:
                continue

            df = yf.download(
                sym, period="2d", interval="1d",
                progress=False, threads=False, auto_adjust=False
            )
            if df is None or df.empty:
                continue

            df = _flatten_df(df)
            last = float(df.iloc[-1]["Close"])
            prev = float(df.iloc[-2]["Close"]) if len(df) > 1 else last
            change_pct = _pct(last, prev) or 0.0
            rows.append({"Symbol": base, "Close": last, "Change%": change_pct})

        dfm = pd.DataFrame(rows)
        if not dfm.empty:
            dfm_sorted = dfm.sort_values(by="Change%", ascending=False)
            gainers = dfm_sorted.head(n).reset_index(drop=True)
            losers = dfm_sorted.sort_values(by="Change%", ascending=True).head(n).reset_index(drop=True)
    except Exception as e:
        log.error(f"Error fetching movers: {e}")
    return gainers, losers


def sector_performance(universe):
    try:
        if "Sector" not in universe.columns:
            return pd.DataFrame()

        perf = []
        for sector, group in universe.groupby("Sector"):
            changes = []
            for _, row in group.iterrows():
                sym = str(row.get("YahooSymbol", ""))
                if not sym:
                    continue

                df = yf.download(
                    sym, period="2d", interval="1d",
                    progress=False, threads=False, auto_adjust=False
                )
                if df is None or df.empty:
                    continue

                df = _flatten_df(df)
                last = float(df.iloc[-1]["Close"])
                prev = float(df.iloc[-2]["Close"]) if len(df) > 1 else last
                ch = _pct(last, prev)
                if ch is not None:
                    changes.append(ch)

            if changes:
                perf.append({"Sector": sector, "Change%": sum(changes) / len(changes)})

        return pd.DataFrame(perf)
    except Exception as e:
        log.error(f"Error fetching sector performance: {e}")
        return pd.DataFrame()


def fii_dii_cash():
    """
    Placeholder until real API integration.
    """
    return {"FII": {"Buy": 5000, "Sell": 4000}, "DII": {"Buy": 3000, "Sell": 3500}}


def news_top_headlines_india(api_key=""):
    """
    Fetch top business headlines for India from NewsAPI.
    """
    if not api_key:
        return []
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=in&category=business&pageSize=10&apiKey={api_key}"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        articles = r.json().get("articles", [])
        return [
            {
                "title": a.get("title", ""),
                "source": (a.get("source") or {}).get("name", ""),
                "url": a.get("url", ""),
                "publishedAt": a.get("publishedAt", "")
            }
            for a in articles
        ]
    except Exception as e:
        log.error(f"Error fetching news: {e}")
        return []
