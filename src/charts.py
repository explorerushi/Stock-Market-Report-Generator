from pathlib import Path
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd

from .utils import CHART_DIR

# Ensure charts directory exists
CHART_DIR.mkdir(parents=True, exist_ok=True)

def line_chart(series: pd.Series, title: str, filename: str):
    """Create and save a line chart from a Series."""
    p = CHART_DIR / filename
    plt.figure()
    plt.plot(series.index, series.values, color="blue")
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(p)
    plt.close()
    return str(p)

def candlestick_chart(df: pd.DataFrame, title: str, filename: str):
    """Create and save a candlestick chart using OHLC data."""
    p = CHART_DIR / filename
    if not {"Open", "High", "Low", "Close"}.issubset(df.columns):
        raise ValueError("DataFrame must contain Open, High, Low, Close columns for candlestick chart")
    dfc = df.copy()
    dfc.index.name = "Date"
    mpf.plot(dfc, type="candle", title=title, savefig=str(p), style="yahoo")
    return str(p)

def bar_chart(df: pd.DataFrame, xcol: str, ycol: str, title: str, filename: str):
    """Create and save a bar chart from a DataFrame column."""
    p = CHART_DIR / filename
    plt.figure()
    plt.bar(df[xcol].astype(str), df[ycol].astype(float), color="green")
    plt.title(title)
    plt.xlabel(xcol)
    plt.ylabel(ycol)
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(p)
    plt.close()
    return str(p)
