"""Download all data needed for the three-signal QQQ/TQQQ backtest.

Outputs (all CSV, Date-indexed) into ../data:
  - qqq.csv   : QQQ daily OHLCV (from 1999)
  - tqqq.csv  : TQQQ daily OHLCV (real, from 2010-02-11)
  - vix.csv   : ^VIX daily close
  - irx.csv   : ^IRX 13-week T-bill yield (for leverage financing cost)
  - cape.csv  : Shiller S&P 500 CAPE (monthly) -> forward-filled daily later

Shiller CAPE is the S&P 500 cyclically-adjusted PE. The Nasdaq has no standard
public CAPE series, so we use the S&P 500 CAPE as a broad market-valuation
regime proxy (documented assumption).
"""
import io
import os
import sys
import pandas as pd
import requests
import yfinance as yf

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA, exist_ok=True)


def _flatten(df):
    """yfinance sometimes returns MultiIndex columns; flatten to OHLCV."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def dl(ticker, start, fname, cols=("Open", "High", "Low", "Close", "Volume")):
    df = yf.download(ticker, start=start, auto_adjust=False, progress=False)
    df = _flatten(df)
    df = df[[c for c in cols if c in df.columns]].copy()
    df.index.name = "Date"
    df = df.dropna(how="all")
    df.to_csv(os.path.join(DATA, fname))
    print(f"{ticker:6s} -> {fname:10s} rows={len(df)} "
          f"[{df.index.min().date()} .. {df.index.max().date()}]")
    return df


def shiller_cape():
    """Download Shiller's monthly CAPE from his Yale data file (ie_data.xls)."""
    url = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    xls = pd.ExcelFile(io.BytesIO(r.content))
    raw = pd.read_excel(xls, sheet_name="Data", header=7)
    # Column 'Date' is like 2020.01 (Jan) ... 2020.10 (Oct, NOT October as .1).
    # CAPE column is typically named 'CAPE' (sometimes 'P/E10' style).
    cape_col = None
    for c in raw.columns:
        if str(c).strip().upper() in ("CAPE", "P/E10", "PE10"):
            cape_col = c
            break
    if cape_col is None:
        # CAPE is historically the 13th column block; fall back by position.
        cape_col = raw.columns[12]
    out = raw[["Date", cape_col]].copy()
    out.columns = ["Date", "CAPE"]
    out = out.dropna(subset=["Date"])
    # Convert fractional year (YYYY.MM) -> month timestamp.
    def to_ts(v):
        s = f"{float(v):.2f}"
        yr, mo = s.split(".")
        mo = int(mo)
        if mo == 0:
            mo = 10  # .1 stored as .10 -> October edge; guard
        return pd.Timestamp(year=int(yr), month=mo, day=1)
    out["Date"] = out["Date"].apply(to_ts)
    out["CAPE"] = pd.to_numeric(out["CAPE"], errors="coerce")
    out = out.dropna(subset=["CAPE"]).set_index("Date").sort_index()
    out.to_csv(os.path.join(DATA, "cape.csv"))
    print(f"CAPE   -> cape.csv   rows={len(out)} "
          f"[{out.index.min().date()} .. {out.index.max().date()}] "
          f"last={out['CAPE'].iloc[-1]:.1f}")
    return out


if __name__ == "__main__":
    dl("QQQ", "1999-01-01", "qqq.csv")
    dl("TQQQ", "2010-01-01", "tqqq.csv")
    vix = yf.download("^VIX", start="1990-01-01", auto_adjust=False, progress=False)
    vix = _flatten(vix)[["Close"]].rename(columns={"Close": "VIX"})
    vix.index.name = "Date"
    vix.to_csv(os.path.join(DATA, "vix.csv"))
    print(f"^VIX   -> vix.csv    rows={len(vix)}")
    irx = yf.download("^IRX", start="1999-01-01", auto_adjust=False, progress=False)
    irx = _flatten(irx)[["Close"]].rename(columns={"Close": "IRX"})
    irx.index.name = "Date"
    irx.to_csv(os.path.join(DATA, "irx.csv"))
    print(f"^IRX   -> irx.csv    rows={len(irx)}")
    try:
        shiller_cape()
    except Exception as e:
        print(f"!! Shiller CAPE download failed: {e}", file=sys.stderr)
        sys.exit(2)
