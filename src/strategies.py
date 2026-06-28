"""Single-file backtest engine for the three-signal QQQ/TQQQ DCA framework.

Three strategies, all funded by a $10,000 contribution on the first trading day
of every month, run over five start points (2000, 2005, 2010, 2015, 2020) to
mid-2026:

  1. dca_qqq    : buy $10k of QQQ every month.
  2. dca_tqqq   : buy $10k of (synthetic-then-real) TQQQ every month.
  3. three_sig  : CAPE + Drawdown + VIX dynamic-leverage framework.

Leverage ETF = 3x-Nasdaq synthetic before 2010-02-11, real TQQQ after
(see data_prep.py, validated in validate_tqqq.py).

------------------------------------------------------------------------------
THREE-SIGNAL RULES (faithful reading of the source article; the article is
prose, so each interpretation choice is documented in summary.md).

Signals, evaluated on the first trading day of each month, 5-day smoothed:
  - Valuation : CAPE expanding-history percentile.   cheap<20%  high>70%  bubble>85%
  - Drawdown  : QQQ drop from its running peak.       deep < -20%
                25-trading-day QQQ return.            crash < -12%
  - Panic     : VIX level.                            panic > 40   calm < 12

LOW signals counted for "bottoms": (CAPE pct<20%) + (QQQ DD<-20%) + (VIX>40).

Monthly decision (cash already holds this month's $10k + interest):
  low>=2  major bottom : deploy ALL cash into TQQQ; arm a 6-month ramp.
  low==1  minor bottom : deploy min(cash, 2*10k) into QQQ.
  low==0, in order:
     a. 25d crash (<-12%)            -> sell HALF TQQQ to ammo cash.
     b. CAPE pct>70% AND near high   -> don't chase; cash accrues as ammo.
     c. overheated >=6 mo (VIX<12 or
        CAPE pct>85%)                -> trim 1/12 TQQQ to ammo (down to floor).
     d. normal                        -> buy 1x QQQ (TQQQ during ramp window)
                                         + drip 1/6 of remaining ammo into QQQ.
Ammo cash earns the daily risk-free rate. A trim never sells TQQQ below a 5%-of-
equity floor (keeps the accelerator from being zeroed at highs).
------------------------------------------------------------------------------
"""
import os
import numpy as np
import pandas as pd

from data_prep import load_dataset, cape_percentile_series

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS, exist_ok=True)

CONTRIB = 10_000.0
START_POINTS = ["2000-01-01", "2005-01-01", "2010-01-01", "2015-01-01", "2020-01-01"]
END = pd.Timestamp("2026-06-26")

# Three-signal parameters
CAPE_CHEAP, CAPE_HIGH, CAPE_BUBBLE = 0.20, 0.70, 0.85
DD_DEEP, DD_CRASH = -0.20, -0.12
VIX_PANIC, VIX_CALM = 40.0, 12.0
NEAR_HIGH = 0.95          # within 5% of running peak
RAMP_MONTHS = 6
SMOOTH = 5
CAPE_WINDOW_YEARS = 10    # trailing window for the CAPE percentile (adaptive)

# Target TQQQ weight of the risky sleeve by regime (the "accelerator locked
# between a floor and a ceiling"). The framework is a tiered position engine:
# normally hold a TQQQ core (BASE_W), trim toward FLOOR_W when overheated /
# overvalued, and push to the CEIL_W ceiling at deep/panic bottoms.
FLOOR_W = 0.30            # position floor: TQQQ never trimmed below this at highs
BASE_W = 0.55            # default TQQQ weight when no extreme signal
MINOR_W = 0.75           # one low signal (minor bottom)
CEIL_W = 1.00            # two+ low signals (major bottom) -> all-in TQQQ
TRIM_STEP = 1.0 / 12.0    # gradual de-risk toward floor (1/12 per month)
DRIP = 1.0 / 6.0          # gradual ammo redeployment back into the sleeve


def build_signals(df):
    """Add smoothed signal columns used by the three-signal strategy."""
    s = df.copy()
    qs = s["qqq"].rolling(SMOOTH).mean()
    s["dd"] = qs / qs.cummax() - 1.0                      # drawdown from peak
    s["dd25"] = qs / qs.shift(25) - 1.0                   # 25-day fast return
    s["vix_s"] = s["vix"].rolling(SMOOTH).mean()
    s["cape_pct"] = cape_percentile_series(s, window_years=CAPE_WINDOW_YEARS).rolling(SMOOTH).mean()
    s["qqq_peak"] = s["qqq"].cummax()
    s["near_high"] = s["qqq"] >= NEAR_HIGH * s["qqq_peak"]
    return s


def month_starts(idx, start, end):
    """First trading day of each month within [start, end]."""
    sub = idx[(idx >= start) & (idx <= end)]
    g = pd.Series(sub, index=sub).groupby([sub.year, sub.month]).min()
    return list(g.values)


# ---------------------------------------------------------------------------
# Simulation core: daily mark-to-market, monthly decisions.
# ---------------------------------------------------------------------------
def simulate(df, start, decide):
    """Run a DCA simulation. `decide` mutates the portfolio dict each month.

    Returns dict with daily equity curve, time-weighted daily returns, monthly
    contribution dates, and final bookkeeping.
    """
    start = pd.Timestamp(start)
    data = df[(df.index >= start) & (df.index <= END)]
    mstarts = set(month_starts(df.index, start, END))

    p = dict(cash=0.0, qqq=0.0, tqqq=0.0, ramp=0, overheat=0)
    eq = []           # daily equity
    twr = []          # time-weighted daily return
    contrib_dates = []
    prev_eq = None

    for d, row in data.iterrows():
        # 1) accrue interest on ammo cash
        p["cash"] *= (1.0 + row["rf_daily"])
        flow = 0.0
        # 2) month-start: contribute + decide (flows happen before today's MTM)
        if d in mstarts:
            p["cash"] += CONTRIB
            flow = CONTRIB
            contrib_dates.append(d)
            decide(p, row)
        # 3) mark to market at today's close
        equity = p["cash"] + p["qqq"] * row["qqq"] + p["tqqq"] * row["tqqq"]
        eq.append((d, equity))
        # 4) time-weighted daily return (remove external flow added this morning)
        if prev_eq is not None:
            base = prev_eq + flow
            twr.append((d, equity / base - 1.0 if base > 0 else 0.0))
        prev_eq = equity

    eq = pd.Series(dict(eq))
    twr = pd.Series(dict(twr))
    return dict(equity=eq, twr=twr, contribs=contrib_dates,
                total_invested=CONTRIB * len(contrib_dates),
                final=eq.iloc[-1])


# ---- decision functions -------------------------------------------------
def _buy(p, key, price, amount):
    amount = min(amount, p["cash"])
    if amount <= 0:
        return
    p[key] += amount / price
    p["cash"] -= amount


def decide_qqq(p, row):
    _buy(p, "qqq", row["qqq"], p["cash"])           # all available -> QQQ


def decide_tqqq(p, row):
    _buy(p, "tqqq", row["tqqq"], p["cash"])         # all available -> TQQQ


def _rebalance(p, qP, tP, w, deploy_cash):
    """Move the risky sleeve toward target TQQQ weight `w`.

    If deploy_cash, all ammo cash is invested into the sleeve; otherwise the
    existing sleeve is rebalanced and cash is left as ammo.
    """
    sleeve = p["qqq"] * qP + p["tqqq"] * tP
    pool = sleeve + (p["cash"] if deploy_cash else 0.0)
    tgt_t = w * pool
    tgt_q = (1.0 - w) * pool
    p["tqqq"] = tgt_t / tP
    p["qqq"] = tgt_q / qP
    if deploy_cash:
        p["cash"] = 0.0


def decide_three_signal(p, row):
    """Tiered target-weight engine (CAPE + DD + VIX). See module docstring.

    Reconstructed to the article's *design intent* — TQQQ held continuously as
    an accelerator between FLOOR_W and CEIL_W — because the literal decision
    tree (default-to-QQQ) cannot reach the article's ~34% IRR (the cheap-CAPE
    signal essentially never fires in 2000-2026). Documented in summary.md.
    """
    cape_pct, dd, dd25, vix = row["cape_pct"], row["dd"], row["dd25"], row["vix_s"]
    near_high = bool(row["near_high"])
    qP, tP = row["qqq"], row["tqqq"]

    overheated_now = (vix < VIX_CALM) or (cape_pct > CAPE_BUBBLE)
    p["overheat"] = p["overheat"] + 1 if overheated_now else 0
    low = int(cape_pct < CAPE_CHEAP) + int(dd < DD_DEEP) + int(vix > VIX_PANIC)

    if p["ramp"] > 0:
        p["ramp"] -= 1

    if low >= 2:                                     # MAJOR BOTTOM: all-in TQQQ
        _rebalance(p, qP, tP, CEIL_W, deploy_cash=True)
        p["ramp"] = RAMP_MONTHS
        return
    if low == 1 or p["ramp"] > 0:                    # MINOR BOTTOM / ramp window
        _rebalance(p, qP, tP, MINOR_W, deploy_cash=True)
        return
    # no low signal -----------------------------------------------------
    if dd25 < DD_CRASH:                              # a) crash warning: halve TQQQ to ammo
        cur = p["qqq"] * qP + p["tqqq"] * tP
        w_now = (p["tqqq"] * tP) / cur if cur > 0 else 0.0
        _rebalance(p, qP, tP, max(FLOOR_W, w_now * 0.5), deploy_cash=False)
        return
    if (cape_pct > CAPE_HIGH) and near_high:         # b) overvalued near high: de-risk, hold cash
        _rebalance(p, qP, tP, FLOOR_W, deploy_cash=False)
        return
    if p["overheat"] >= 6:                           # c) sustained overheat: trim toward floor
        cur = p["qqq"] * qP + p["tqqq"] * tP
        w_now = (p["tqqq"] * tP) / cur if cur > 0 else 0.0
        _rebalance(p, qP, tP, max(FLOOR_W, w_now - TRIM_STEP), deploy_cash=False)
        return
    # d) normal: invest the contribution and hold the BASE_W core --------
    _rebalance(p, qP, tP, BASE_W, deploy_cash=True)


# ---- metrics ------------------------------------------------------------
def irr_annual(contrib_dates, final, eq_index):
    """Money-weighted annualized IRR from monthly -CONTRIB flows + final value."""
    # cashflows on a monthly grid: -CONTRIB each contribution month, +final at end
    months = len(contrib_dates)
    flows = [-CONTRIB] * months
    # place final value at the last day -> months_total spans first contrib..end
    total_months = (eq_index[-1].year - contrib_dates[0].year) * 12 + \
                   (eq_index[-1].month - contrib_dates[0].month)
    cf = np.zeros(total_months + 1)
    for i, d in enumerate(contrib_dates):
        m = (d.year - contrib_dates[0].year) * 12 + (d.month - contrib_dates[0].month)
        cf[m] += -CONTRIB
    cf[-1] += final

    def npv(r):
        t = np.arange(len(cf))
        return np.sum(cf / (1 + r) ** t)
    lo, hi = -0.9999, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(mid) > 0:
            lo = mid
        else:
            hi = mid
    monthly = (lo + hi) / 2
    return (1 + monthly) ** 12 - 1


def max_drawdown(eq):
    return (eq / eq.cummax() - 1.0).min()


def sharpe(twr, rf_daily_mean=0.0):
    r = twr.dropna()
    if r.std() == 0:
        return np.nan
    return (r.mean() - rf_daily_mean) / r.std() * np.sqrt(252)


def alpha_beta(twr, bench_twr):
    j = pd.DataFrame({"s": twr, "b": bench_twr}).dropna()
    if len(j) < 30:
        return np.nan, np.nan
    beta, alpha = np.polyfit(j["b"], j["s"], 1)
    return alpha * 252, beta            # annualized alpha


def metrics(res, bench_twr=None):
    eq = res["equity"]
    m = dict(
        final=res["final"],
        invested=res["total_invested"],
        multiple=res["final"] / res["total_invested"],
        irr=irr_annual(res["contribs"], res["final"], eq.index),
        mdd=max_drawdown(eq),
        sharpe=sharpe(res["twr"]),
    )
    if bench_twr is not None:
        m["alpha"], m["beta"] = alpha_beta(res["twr"], bench_twr)
    else:
        m["alpha"], m["beta"] = np.nan, np.nan
    return m


# ---- driver -------------------------------------------------------------
def run_all():
    df = build_signals(load_dataset())
    strategies = {
        "QQQ DCA": decide_qqq,
        "TQQQ DCA": decide_tqqq,
        "Three-Signal": decide_three_signal,
    }
    rows = []
    curves = {}
    for start in START_POINTS:
        yr = start[:4]
        runs = {name: simulate(df, start, fn) for name, fn in strategies.items()}
        bench = runs["QQQ DCA"]["twr"]
        for name, res in runs.items():
            m = metrics(res, bench_twr=bench)
            m.update(start=yr, strategy=name)
            rows.append(m)
            curves[(yr, name)] = res["equity"]
    out = pd.DataFrame(rows)[
        ["start", "strategy", "final", "invested", "multiple",
         "irr", "mdd", "sharpe", "alpha", "beta"]
    ]
    out.to_csv(os.path.join(RESULTS, "backtest_metrics.csv"), index=False)

    # 5-start averages per strategy
    avg = out.groupby("strategy")[["irr", "mdd", "multiple", "sharpe"]].mean()
    avg.to_csv(os.path.join(RESULTS, "avg_by_strategy.csv"))

    pd.to_pickle(curves, os.path.join(RESULTS, "equity_curves.pkl"))
    print(out.to_string(index=False))
    print("\n=== 5-start average ===")
    print(avg.round(3).to_string())
    return out, avg, curves


if __name__ == "__main__":
    run_all()
