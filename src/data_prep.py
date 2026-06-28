"""Build the unified daily dataset and synthesize pre-2010 TQQQ from QQQ.

Synthetic TQQQ daily total return = 3 * QQQ_daily_total_return - daily_cost,
where daily_cost = (2 * rf_annual + expense_ratio) / 252.

  - QQQ total return uses Adj Close (dividends reinvested).
  - rf_annual is the 13-week T-bill yield (^IRX), the financing rate a 3x ETF
    pays on the 2x it borrows.
  - expense_ratio = 0.95%/yr (TQQQ's actual ER).

The continuous 'tqqq' series uses synthetic returns before 2010-02-11 and real
TQQQ Adj Close returns from 2010-02-11 onward, chained into one price index.
"""
import os
import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
TQQQ_INCEPTION = pd.Timestamp("2010-02-11")
EXPENSE_RATIO = 0.0095
# Financing spread over T-bills on the borrowed 2x exposure (swap spread +
# securities-lending / rebalancing friction). Calibrated so synthetic CAGR
# matches real TQQQ over the 2010-2026 overlap (see validate_tqqq.py).
FIN_SPREAD = 0.0080


def _load(fname):
    return pd.read_csv(os.path.join(DATA, fname), index_col=0, parse_dates=True)


def load_dataset():
    """Return a daily DataFrame indexed by trading date with columns:
    qqq, tqqq_real, tqqq (spliced TR index), vix, rf_daily, cape (ffilled).
    """
    qqq = _load("qqq.csv")["Adj Close"].rename("qqq")
    tqqq_real = _load("tqqq.csv")["Adj Close"].rename("tqqq_real")
    vix = _load("vix.csv")["VIX"].rename("vix")
    irx = _load("irx.csv")["IRX"].rename("irx")          # percent, annualized
    cape = _load("cape.csv")["CAPE"].rename("cape")        # monthly

    df = pd.DataFrame(qqq).join(tqqq_real, how="left")
    df = df.dropna(subset=["qqq"])          # drop unfinalized last row (NaN Adj Close)
    # Risk-free: ^IRX in percent -> daily decimal. Forward-fill gaps, floor at 0.
    rf = (irx.reindex(df.index).ffill().clip(lower=0) / 100.0) / 252.0
    df["rf_daily"] = rf.fillna(0.0)
    df["vix"] = vix.reindex(df.index).ffill()

    # CAPE is monthly (month-start). Forward-fill onto trading days.
    df["cape"] = cape.reindex(df.index, method="ffill")

    # --- Synthesize TQQQ total-return index ---
    qqq_ret = df["qqq"].pct_change()
    cost = (2.0 * (df["rf_daily"] + FIN_SPREAD / 252.0)) + (EXPENSE_RATIO / 252.0)
    syn_ret = 3.0 * qqq_ret - cost
    real_ret = df["tqqq_real"].pct_change()
    # Use real returns strictly AFTER inception; on the inception day itself the
    # real series has no prior price, so chain one more synthetic day to keep the
    # spliced index continuous (no gap).
    tqqq_ret = real_ret.where(df.index > TQQQ_INCEPTION, syn_ret)
    tqqq_ret.iloc[0] = 0.0
    df["tqqq"] = 100.0 * (1.0 + tqqq_ret).cumprod()
    df["tqqq_syn_full"] = 100.0 * (1.0 + syn_ret.fillna(0.0)).cumprod()  # for validation
    return df


def cape_percentile_series(df, window_years=15):
    """Trailing-window percentile of CAPE (no look-ahead).

    For each date, ranks the current CAPE against the prior `window_years` of
    monthly CAPE history (data dated <= that day only). A trailing window makes
    the signal adaptive: "cheap" fires after a real selloff and "bubble" fires
    at relative tops, instead of being pinned high by the secular rise in
    valuations. Set window_years=None for full-history (expanding) percentile.
    """
    full = _load("cape.csv")["CAPE"].sort_index()
    vals = full.values
    idx = full.index
    win = None if window_years is None else pd.DateOffset(years=window_years)
    out = pd.Series(index=df.index, dtype=float)
    for d, c in df["cape"].items():
        if np.isnan(c):
            out[d] = np.nan
            continue
        mask = idx <= d
        if win is not None:
            mask &= idx > (d - win)
        hist = vals[mask]
        out[d] = (hist <= c).mean() if len(hist) else np.nan
    return out


if __name__ == "__main__":
    df = load_dataset()
    print(df[["qqq", "tqqq_real", "tqqq", "vix", "cape", "rf_daily"]].describe().round(3))
    print("\nrange:", df.index.min().date(), "..", df.index.max().date())
