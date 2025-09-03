import json
from pathlib import Path
import pandas as pd

# Project root and directories
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "output"
CHART_DIR = OUT_DIR / "charts"


def ensure_dirs():
    """
    Ensure required directories exist (data, output, charts).
    """
    for d in [DATA_DIR, OUT_DIR, CHART_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def save_csv(df: pd.DataFrame, name: str):
    """
    Save a DataFrame to CSV inside data folder.

    Args:
        df: DataFrame to save.
        name: Filename without extension.
    """
    if df is None or df.empty:
        print(f"[WARN] Tried to save empty DataFrame: {name}.csv (skipped)")
        return
    p = DATA_DIR / f"{name}.csv"
    try:
        df.to_csv(p, index=False)
        print(f"[INFO] Saved CSV -> {p}")
    except Exception as e:
        print(f"[ERROR] Could not save CSV {p}: {e}")


def save_json(obj, name: str):
    """
    Save Python object (dict/list) as JSON inside data folder.

    Args:
        obj: Object to save (must be JSON serializable).
        name: Filename without extension.
    """
    p = DATA_DIR / f"{name}.json"
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Saved JSON -> {p}")
    except Exception as e:
        print(f"[ERROR] Could not save JSON {p}: {e}")


def load_config() -> dict:
    """
    Load project config (config.json or config.example.json).

    Returns:
        dict with configuration settings.
        If missing or invalid, returns empty dict {}.
    """
    cfg_paths = [ROOT / "config.json", ROOT / "config.example.json"]
    for p in cfg_paths:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"[ERROR] Failed to load config {p}: {e}")
                return {}
    print("[WARN] No config.json found, using empty config {}")
    return {}
