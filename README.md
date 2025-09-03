
# Daily Financial Market Report

One-command script that fetches market data (indices, currencies, commodities, crypto), computes basic TA, pulls Indian business news, draws charts, and generates a polished PDF.

## Quickstart

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

Create a `config.json` at the project root (beside this README), or edit `config.example.json`:

```json
{
  "news_api_key": "89979b0c6ce5491d806d46102c44a9bb"
}
```

Run:

```bash
python -m src.main
```

The PDF appears in `output/`.
CSV/JSON dumps are written to `data/`.
Charts are saved to `output/charts/`.

## Notes

- Uses free Yahoo Finance data via `yfinance`.
- News from NewsAPI (top business headlines for India).
- If NSE constituents download fails, movers/sector tables may be empty; the rest still works.
