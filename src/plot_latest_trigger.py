"""Plot QQQ price + the three signals around the latest trigger events.

Marks the latest BUY trigger (minor bottom, 2023-05) and shades the recent
"overvalued near high -> don't chase" de-risk regime (2025-2026, CAPE pinned at
its trailing-10yr max).
"""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from data_prep import load_dataset
from strategies import build_signals, month_starts, END
import strategies as S

PLOTS = os.path.join(os.path.dirname(__file__), "..", "plots")
WIN_START = pd.Timestamp("2021-01-01")
BUY_TRIGGER = pd.Timestamp("2023-05-01")   # latest minor-bottom (1 LOW signal)


def main():
    df = build_signals(load_dataset())
    w = df[(df.index >= WIN_START) & (df.index <= END)]

    # recompute the monthly branch to shade no-chase months in the window
    ms = [d for d in month_starts(df.index, WIN_START, END)]
    r = df.loc[ms]
    nochase = [d for d in ms if (r["cape_pct"][d] > S.CAPE_HIGH and bool(r["near_high"][d])
               and not (r["cape_pct"][d] < S.CAPE_CHEAP) and not (r["dd"][d] < S.DD_DEEP)
               and not (r["vix_s"][d] > S.VIX_PANIC) and not (r["dd25"][d] < S.DD_CRASH))]

    fig, ax = plt.subplots(4, 1, figsize=(12, 11), sharex=True,
                           gridspec_kw={"height_ratios": [3, 2, 2, 2]})

    def mark(a):
        a.axvline(BUY_TRIGGER, color="#16a34a", lw=1.6, ls="--", zorder=5)
        for d in nochase:
            a.axvspan(d, d + pd.Timedelta(days=31), color="#f59e0b", alpha=0.06, zorder=0)

    # 1) price
    ax[0].plot(w.index, w["qqq"], color="#1f77b4", lw=1.4, label="QQQ (total-return)")
    ax[0].set_yscale("log"); ax[0].set_ylabel("QQQ price (log)")
    ax[0].set_title("QQQ price + three-signal state around the latest triggers (2021–2026)")
    mark(ax[0])
    ax[0].annotate("latest BUY trigger\nminor bottom 2023-05\n(DD hit −20%)",
                   xy=(BUY_TRIGGER, w["qqq"].asof(BUY_TRIGGER)),
                   xytext=(pd.Timestamp("2023-07-01"), w["qqq"].min()*1.05),
                   fontsize=9, color="#166534",
                   arrowprops=dict(arrowstyle="->", color="#166534"))
    ax[0].legend(loc="upper left", fontsize=9); ax[0].grid(True, which="both", alpha=0.25)

    # 2) CAPE percentile
    ax[1].plot(w.index, w["cape_pct"], color="#7c3aed", lw=1.4)
    for y, lbl, c in [(.20, "cheap <20%", "#16a34a"), (.70, "high >70%", "#f59e0b"),
                      (.85, "bubble >85%", "#dc2626")]:
        ax[1].axhline(y, color=c, lw=1, ls=":"); ax[1].text(w.index[2], y+0.01, lbl, fontsize=8, color=c)
    ax[1].set_ylabel("CAPE pct\n(trailing 10y)"); ax[1].set_ylim(0, 1.05); mark(ax[1]); ax[1].grid(True, alpha=0.25)

    # 3) drawdown + 25d return
    ax[2].plot(w.index, w["dd"]*100, color="#1f77b4", lw=1.3, label="DD from peak")
    ax[2].plot(w.index, w["dd25"]*100, color="#94a3b8", lw=1.0, label="25-day return")
    ax[2].axhline(-20, color="#16a34a", lw=1, ls=":"); ax[2].text(w.index[2], -19, "deep −20%", fontsize=8, color="#16a34a")
    ax[2].axhline(-12, color="#dc2626", lw=1, ls=":"); ax[2].text(w.index[2], -11, "crash −12% (25d)", fontsize=8, color="#dc2626")
    ax[2].set_ylabel("drawdown (%)"); ax[2].legend(loc="lower left", fontsize=8); mark(ax[2]); ax[2].grid(True, alpha=0.25)

    # 4) VIX
    ax[3].plot(w.index, w["vix_s"], color="#ea580c", lw=1.3)
    ax[3].axhline(40, color="#dc2626", lw=1, ls=":"); ax[3].text(w.index[2], 41, "panic >40", fontsize=8, color="#dc2626")
    ax[3].axhline(12, color="#2563eb", lw=1, ls=":"); ax[3].text(w.index[2], 12.4, "calm <12", fontsize=8, color="#2563eb")
    ax[3].set_ylabel("VIX (5d avg)"); mark(ax[3]); ax[3].grid(True, alpha=0.25)
    ax[3].xaxis.set_major_locator(mdates.YearLocator())
    ax[3].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # legend note for shading
    ax[0].text(0.985, 0.04, "orange band = 'overvalued near high → no-chase' month",
               transform=ax[0].transAxes, ha="right", fontsize=8, color="#b45309")

    fig.tight_layout()
    p = os.path.join(PLOTS, "latest_trigger.png")
    fig.savefig(p, dpi=115)
    print("saved", p)
    print(f"latest BUY trigger: {BUY_TRIGGER.date()} (minor bottom)")
    print(f"no-chase months in window: {len(nochase)} (latest {pd.Timestamp(nochase[-1]).date()})")


if __name__ == "__main__":
    main()
