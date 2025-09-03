import numpy as np
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    """
    Compute Exponential Moving Average (EMA).

    Args:
        series: Price series (pd.Series).
        span: EMA span (period).

    Returns:
        pd.Series of EMA values.
    """
    if series is None or series.empty:
        return pd.Series(dtype=float)
    return series.ewm(span=span, adjust=False).mean()


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Compute MACD indicator.

    Args:
        series: Price series.
        fast: Fast EMA period.
        slow: Slow EMA period.
        signal: Signal line EMA period.

    Returns:
        tuple of (macd_line, signal_line, histogram), each as pd.Series.
    """
    if series is None or series.empty:
        empty = pd.Series(dtype=float)
        return empty, empty, empty

    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def support_resistance(series: pd.Series, window: int = 20):
    """
    Find support (min) and resistance (max) levels over a window.

    Args:
        series: Price series.
        window: Lookback window size.

    Returns:
        (support, resistance) as floats.
    """
    if series is None or series.empty:
        return 0.0, 0.0

    w = series.tail(window).dropna()
    if w.empty:
        return 0.0, 0.0

    return float(w.min()), float(w.max())


def trend_direction(series: pd.Series, window: int = 10, tol: float = 1e-6):
    """
    Detect short-term trend direction using linear regression slope.

    Args:
        series: Price series.
        window: Lookback window size.
        tol: Tolerance for slope ≈ 0.

    Returns:
        (trend, slope) where trend is "Up", "Down", or "Sideways".
    """
    if series is None or series.empty:
        return "Sideways", 0.0

    y = series.tail(window).dropna().values.astype(float)
    if len(y) < 2:
        return "Sideways", 0.0

    x = np.arange(len(y))
    slope = float(np.polyfit(x, y, 1)[0])

    if slope > tol:
        return "Up", slope
    elif slope < -tol:
        return "Down", slope
    return "Sideways", slope
