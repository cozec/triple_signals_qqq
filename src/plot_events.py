"""Two focused case-study plots of recent signal events:
  A) 2022-2023 bear -> latest BUY trigger (minor bottom 2023-05)
  B) March-April 2026 ~16% correction (no trigger; resumed normal buying)

Each plot = QQQ price (log) + CAPE percentile + drawdown/25d + VIX, with the
signal thresholds drawn so you can read exactly which signals fired.
"""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from data_prep import load_dataset
from strategies import build_signals
import strategies as S

PLOTS = os.path.join(os.path.dirname(__file__), "..", "plots")


def plot_window(df, start, end, title, outfile, vlines=None, annotate=None):
    w = df.loc[start:end, ["qqq", "dd", "dd25", "vix", "vix_s", "cape_pct"]]
    fig, ax = plt.subplots(4, 1, figsize=(11, 10), sharex=True,
                           gridspec_kw={"height_ratios": [3, 2, 2, 2]})
    vlines = vlines or []

    def marks(a):
        for d, c in vlines:
            a.axvline(pd.Timestamp(d), color=c, lw=1.6, ls="--", zorder=5)

    ax[0].plot(w.index, w["qqq"], color="#1f77b4", lw=1.5)
    ax[0].set_yscale("log"); ax[0].set_ylabel("QQQ price (log)")
    ax[0].set_title(title, fontsize=12); marks(ax[0]); ax[0].grid(True, which="both", alpha=0.25)
    if annotate:
        d, txt, xy_off = annotate
        ax[0].annotate(txt, xy=(pd.Timestamp(d), w["qqq"].asof(pd.Timestamp(d))),
                       xytext=xy_off, textcoords="axes fraction", fontsize=9, color="#166534",
                       arrowprops=dict(arrowstyle="->", color="#166534"))

    ax[1].plot(w.index, w["cape_pct"], color="#7c3aed", lw=1.4)
    for y, lbl, c in [(.20, "cheap <20%", "#16a34a"), (.70, "high >70%", "#f59e0b"),
                      (.85, "bubble >85%", "#dc2626")]:
        ax[1].axhline(y, color=c, lw=1, ls=":"); ax[1].text(w.index[1], y + 0.015, lbl, fontsize=8, color=c)
    ax[1].set_ylabel("CAPE pct\n(trailing 10y)"); ax[1].set_ylim(0, 1.08); marks(ax[1]); ax[1].grid(True, alpha=0.25)

    ax[2].plot(w.index, w["dd"] * 100, color="#1f77b4", lw=1.4, label="DD from peak")
    ax[2].plot(w.index, w["dd25"] * 100, color="#94a3b8", lw=1.0, label="25-day return")
    ax[2].axhline(-20, color="#16a34a", lw=1, ls=":"); ax[2].text(w.index[1], -19, "deep −20%", fontsize=8, color="#16a34a")
    ax[2].axhline(-12, color="#dc2626", lw=1, ls=":"); ax[2].text(w.index[1], -11, "crash −12% (25d)", fontsize=8, color="#dc2626")
    ax[2].set_ylabel("drawdown (%)"); ax[2].legend(loc="lower left", fontsize=8); marks(ax[2]); ax[2].grid(True, alpha=0.25)

    ax[3].plot(w.index, w["vix_s"], color="#ea580c", lw=1.4)
    ax[3].axhline(40, color="#dc2626", lw=1, ls=":"); ax[3].text(w.index[1], 41, "panic >40", fontsize=8, color="#dc2626")
    ax[3].axhline(12, color="#2563eb", lw=1, ls=":"); ax[3].text(w.index[1], 12.4, "calm <12", fontsize=8, color="#2563eb")
    ax[3].set_ylabel("VIX (5d avg)"); marks(ax[3]); ax[3].grid(True, alpha=0.25)
    ax[3].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax[3].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(ax[3].get_xticklabels(), rotation=0, fontsize=8)

    fig.tight_layout()
    p = os.path.join(PLOTS, outfile)
    fig.savefig(p, dpi=115)
    print("saved", p)


def main():
    df = build_signals(load_dataset())
    plot_window(
        df, "2021-06-01", "2024-06-30",
        "A) 2022–23 bear → latest BUY trigger (minor bottom, 2023-05)",
        "event_2023_bottom.png",
        vlines=[("2023-05-01", "#16a34a")],
        annotate=("2023-05-01", "2023-05: last month DD still < −20%\n(tail of the 2022–23\nminor-bottom run, 1 LOW signal)",
                  (0.40, 0.16)),
    )
    plot_window(
        df, "2025-09-01", "2026-06-26",
        "B) March–April 2026 correction (~−16%, no trigger)",
        "event_2026_correction.png",
        vlines=[("2026-03-30", "#dc2626")],
        annotate=("2026-03-30", "raw −16% dip (smoothed DD −9%)\nVIX <40, CAPE not cheap\n→ 0 LOW signals, resume normal buys",
                  (0.26, 0.10)),
    )


if __name__ == "__main__":
    main()
