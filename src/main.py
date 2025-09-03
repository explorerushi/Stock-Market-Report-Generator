import logging
from datetime import datetime
import pandas as pd

from .utils import ensure_dirs, save_csv, save_json, load_config
from .fetchers import (
    INDEX_TICKERS, CURRENCY_TICKERS, COMMODITY_TICKERS, CRYPTO_TICKERS,
    get_snapshots, get_index_history, get_nifty50_constituents,
    top_movers_from_universe, sector_performance, fii_dii_cash, news_top_headlines_india
)
from .charts import line_chart, candlestick_chart, bar_chart
from .report_pdf import build_pdf
from .ta import ema, macd, trend_direction, support_resistance


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)


def dict_to_rows(dct, first_col="Name"):
    """Convert dict data into a list of rows for PDF tables."""
    rows = [[first_col, "Open", "Close", "Change %", "LTP"]]
    for k, v in dct.items():
        rows.append([
            k,
            f"{v.get('Open', 0):.2f}" if v.get("Open") else "-",
            f"{v.get('Close', 0):.2f}" if v.get("Close") else "-",
            f"{v.get('Change%', 0):.2f}%" if v.get("Change%") else "-",
            f"{v.get('LTP', 0):.2f}" if v.get("LTP") else "-"
        ])
    return rows


def build():
    try:
        logging.info("Ensuring directories...")
        ensure_dirs()

        logging.info("Loading configuration...")
        cfg = load_config()

        # 1) Snapshots
        logging.info("Fetching market snapshots...")
        summary_indices = get_snapshots({
            "NIFTY 50": INDEX_TICKERS["NIFTY 50"],
            "NIFTY BANK": INDEX_TICKERS["NIFTY BANK"],
            "SENSEX": INDEX_TICKERS["SENSEX"],
            "S&P 500": INDEX_TICKERS["S&P 500"],
            "DOW JONES": INDEX_TICKERS["DOW JONES"],
            "NASDAQ": INDEX_TICKERS["NASDAQ"],
        })

        indian_indices = {k: v for k, v in summary_indices.items() if k in ["NIFTY 50", "NIFTY BANK", "SENSEX"]}
        global_indices = {k: v for k, v in summary_indices.items() if k in ["S&P 500", "DOW JONES", "NASDAQ"]}
        global_indices.update(get_snapshots({
            k: v for k, v in INDEX_TICKERS.items()
            if k in ["FTSE 100", "DAX", "NIKKEI 225", "HANG SENG", "SHANGHAI COMP"]
        }))

        currencies = get_snapshots(CURRENCY_TICKERS)
        commodities = get_snapshots(COMMODITY_TICKERS)
        crypto = get_snapshots(CRYPTO_TICKERS)

        # 2) Histories
        logging.info("Fetching historical data...")
        hist_nifty = get_index_history(INDEX_TICKERS["NIFTY 50"], period="3mo", interval="1d")
        hist_bank = get_index_history(INDEX_TICKERS["NIFTY BANK"], period="3mo", interval="1d")

        # 3) Universe
        logging.info("Fetching NIFTY50 universe...")
        universe = get_nifty50_constituents()
        gainers, losers = top_movers_from_universe(universe, n=5)
        sector_perf = sector_performance(universe)

        # 4) Other blocks
        fii = fii_dii_cash()
        news = news_top_headlines_india(api_key=cfg.get("news_api_key", ""))

        # Save CSV/JSON
        logging.info("Saving snapshots and analytics...")
        save_json(summary_indices, "summary_indices")
        if indian_indices:
            save_csv(pd.DataFrame.from_dict(indian_indices, orient="index").reset_index().rename(columns={"index": "Index"}), "indian_indices")
        if global_indices:
            save_csv(pd.DataFrame.from_dict(global_indices, orient="index").reset_index().rename(columns={"index": "Index"}), "global_indices")
        if currencies:
            save_csv(pd.DataFrame.from_dict(currencies, orient="index").reset_index().rename(columns={"index": "Pair"}), "currencies")
        if commodities:
            save_csv(pd.DataFrame.from_dict(commodities, orient="index").reset_index().rename(columns={"index": "Commodity"}), "commodities")
        if crypto:
            save_csv(pd.DataFrame.from_dict(crypto, orient="index").reset_index().rename(columns={"index": "Crypto"}), "crypto")
        if not universe.empty:
            save_csv(universe, "nifty50_universe")
        if not gainers.empty:
            save_csv(gainers, "top_gainers")
        if not losers.empty:
            save_csv(losers, "top_losers")
        if not sector_perf.empty:
            save_csv(sector_perf, "sector_performance")
        if fii:
            save_json(fii, "fii_dii")
        if news:
            save_json(news, "news_india_business")

        # Charts
        logging.info("Building charts...")
        charts = {}
        if not hist_nifty.empty:
            charts["NIFTY 50 - Candlestick"] = candlestick_chart(hist_nifty.tail(60), "NIFTY 50", "nifty_candle.png")
            charts["NIFTY 50 - Close"] = line_chart(hist_nifty["Close"], "NIFTY 50 Close", "nifty_line.png")
        if not hist_bank.empty:
            charts["BANK NIFTY - Candlestick"] = candlestick_chart(hist_bank.tail(60), "BANK NIFTY", "banknifty_candle.png")
            charts["BANK NIFTY - Close"] = line_chart(hist_bank["Close"], "BANK NIFTY Close", "banknifty_line.png")

        if not gainers.empty:
            charts["Top 5 Gainers"] = bar_chart(gainers, "Symbol", "Change%", "Top 5 Gainers", "gainers_bar.png")
        if not losers.empty:
            charts["Top 5 Losers"] = bar_chart(losers, "Symbol", "Change%", "Top 5 Losers", "losers_bar.png")

        # TA
        logging.info("Performing Technical Analysis...")
        ta_sections = []
        for name, hist in [("NIFTY 50", hist_nifty), ("BANK NIFTY", hist_bank)]:
            if hist.empty:
                continue
            closes = hist["Close"].dropna()
            if closes.empty:
                continue
            ema9 = ema(closes, 9)
            ema15 = ema(closes, 15)
            macd_line, signal_line, histo = macd(closes)
            supp, resist = support_resistance(closes, 20)
            trend, slope = trend_direction(closes, 10)
            metrics = {
                "Support (20d min)": f"{supp:.2f}",
                "Resistance (20d max)": f"{resist:.2f}",
                "Trendline Direction": f"{trend} (slope {slope:.4f})",
                "EMA(9) vs EMA(15)": f"{float(ema9.iloc[-1]):.2f} vs {float(ema15.iloc[-1]):.2f}",
                "MACD (last)": f"{float(macd_line.iloc[-1]):.2f}",
                "Signal (last)": f"{float(signal_line.iloc[-1]):.2f}",
                "Histogram (last)": f"{float(histo.iloc[-1]):.2f}",
                "Interpretation": "Bullish" if float(macd_line.iloc[-1]) > float(signal_line.iloc[-1]) else "Bearish",
            }
            ta_sections.append((name, metrics))

        # Tables for PDF
        indian_rows = dict_to_rows(indian_indices, "Index")
        global_rows = dict_to_rows(global_indices, "Index")

        currency_rows = dict_to_rows(currencies, "Pair")
        commodity_rows = dict_to_rows(commodities, "Commodity")

        gain_rows = [["Symbol", "Change %", "Close"]] + (
            [[r["Symbol"], f"{float(r['Change%']):.2f}%", f"{float(r['Close']):.2f}"] for _, r in gainers.iterrows()]
            if not gainers.empty else [["-", "-", "-"]]
        )
        lose_rows = [["Symbol", "Change %", "Close"]] + (
            [[r["Symbol"], f"{float(r['Change%']):.2f}%", f"{float(r['Close']):.2f}"] for _, r in losers.iterrows()]
            if not losers.empty else [["-", "-", "-"]]
        )
        sector_rows = [["Sector", "Avg Change %"]] + (
            [[r["Sector"], f"{float(r['Change%']):.2f}%"] for _, r in sector_perf.iterrows()]
            if not sector_perf.empty else [["-", "-"]]
        )

        # Build context
        context = {
            "summary_indices": summary_indices,
            "indian_indices_table": indian_rows,
            "global_indices_table": global_rows,
            "currency_table": currency_rows,
            "commodity_table": commodity_rows,
            "fii_dii": fii,
            "gainers_table": gain_rows,
            "losers_table": lose_rows,
            "sector_table": sector_rows,
            "charts": charts,
            "ta_sections": ta_sections,
            "news": news,
        }

        logging.info("Building PDF report...")
        pdf_path = build_pdf(context)
        logging.info(f"✅ Report generated: {pdf_path}")
        return pdf_path

    except Exception as e:
        logging.error(f"❌ Report generation failed: {e}")
        return None


if __name__ == "__main__":
    out = build()
    if out:
        print(f"Report generated: {out}")
    else:
        print("Report generation failed. Check logs above.")
