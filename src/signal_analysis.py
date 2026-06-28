"""Analyze the three signals: how often each fires, what drives the bottoms,
and an ablation of each signal's marginal contribution. Produces a chart and
returns the numbers for the HTML report.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import strategies as S
from data_prep import load_dataset
from strategies import build_signals, month_starts, END

PLOTS = os.path.join(os.path.dirname(__file__), "..", "plots")


def trigger_stats(df):
    ms = month_starts(df.index, pd.Timestamp("2000-01-01"), END)
    r = df.loc[ms]
    cheap = r["cape_pct"] < S.CAPE_CHEAP
    deep = r["dd"] < S.DD_DEEP
    panic = r["vix_s"] > S.VIX_PANIC
    low = cheap.astype(int) + deep.astype(int) + panic.astype(int)
    stats = {
        "N": len(r),
        "cheap": (int(cheap.sum()), cheap.mean()),
        "deep": (int(deep.sum()), deep.mean()),
        "panic": (int(panic.sum()), panic.mean()),
        "crash": (int((r["dd25"] < S.DD_CRASH).sum()), (r["dd25"] < S.DD_CRASH).mean()),
        "high": (int((r["cape_pct"] > S.CAPE_HIGH).sum()), (r["cape_pct"] > S.CAPE_HIGH).mean()),
        "bubble": (int((r["cape_pct"] > S.CAPE_BUBBLE).sum()), (r["cape_pct"] > S.CAPE_BUBBLE).mean()),
        "calm": (int((r["vix_s"] < S.VIX_CALM).sum()), (r["vix_s"] < S.VIX_CALM).mean()),
        "major": (int((low >= 2).sum()), (low >= 2).mean()),
        # of the major-bottom months, how many had each signal on
        "major_cape": int((cheap & (low >= 2)).sum()),
        "major_vix_unique": int((panic & (low < 2)).sum()),  # VIX-only bottoms it created alone
    }
    return stats


def trigger_counts():
    """Count, over the monthly decision dates, how many MONTHS each signal/action
    was on and how many distinct EPISODES (consecutive runs) it formed.
    """
    df = build_signals(load_dataset())
    ms = month_starts(df.index, pd.Timestamp("2000-01-01"), END)
    r = df.loc[ms]

    def episodes(mask):
        v = mask.astype(int).to_numpy()
        prev = np.concatenate([[0], v[:-1]])
        return int(((v == 1) & (prev == 0)).sum())

    cheap = r["cape_pct"] < S.CAPE_CHEAP
    deep = r["dd"] < S.DD_DEEP
    panic = r["vix_s"] > S.VIX_PANIC
    crash = r["dd25"] < S.DD_CRASH
    high = r["cape_pct"] > S.CAPE_HIGH
    bubble = r["cape_pct"] > S.CAPE_BUBBLE
    calm = r["vix_s"] < S.VIX_CALM
    low = cheap.astype(int) + deep.astype(int) + panic.astype(int)
    major = low >= 2
    minor = low == 1
    near = r["near_high"].astype(bool)
    nochase = (~major) & (~minor) & (~crash) & high & near

    items = [
        ("cheap", "CAPE cheap (<20%)", cheap),
        ("high", "CAPE high (>70%)", high),
        ("bubble", "CAPE bubble (>85%)", bubble),
        ("deep", "DD deep (<-20%)", deep),
        ("crash", "25-day crash (<-12%)", crash),
        ("panic", "VIX panic (>40)", panic),
        ("calm", "VIX calm (<12)", calm),
        ("major", "BUY: major bottom (>=2 LOW)", major),
        ("minor", "BUY: minor bottom (1 LOW)", minor),
        ("nochase", "de-risk: no-chase trim", nochase),
    ]
    rows = {k: (int(mask.sum()), episodes(mask)) for k, lbl, mask in items}
    labels = {k: lbl for k, lbl, _ in items}
    last_major = pd.Timestamp(r.index[major][-1]).year if major.any() else None
    return dict(N=len(r), rows=rows, labels=labels, last_major=last_major)


def ablation():
    base = dict(CAPE_CHEAP=S.CAPE_CHEAP, CAPE_HIGH=S.CAPE_HIGH, CAPE_BUBBLE=S.CAPE_BUBBLE,
                DD_DEEP=S.DD_DEEP, DD_CRASH=S.DD_CRASH, VIX_PANIC=S.VIX_PANIC, VIX_CALM=S.VIX_CALM)

    def restore():
        for k, v in base.items():
            setattr(S, k, v)

    def avg():
        df = build_signals(load_dataset())
        irr, mdd = [], []
        for st in S.START_POINTS:
            m = S.metrics(S.simulate(df, st, S.decide_three_signal))
            irr.append(m["irr"]); mdd.append(m["mdd"])
        return np.mean(irr), np.mean(mdd)

    out = {}
    restore(); out["all"] = avg()
    restore(); S.CAPE_CHEAP = -1; S.CAPE_HIGH = 2; S.CAPE_BUBBLE = 2; out["no_cape"] = avg()
    restore(); S.DD_DEEP = -10; S.DD_CRASH = -10; out["no_dd"] = avg()
    restore(); S.VIX_PANIC = 9999; S.VIX_CALM = -1; out["no_vix"] = avg()
    restore()
    return out


def make_chart(stats, abl):
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))

    # (a) fire frequency
    labels = ["DD deep\n(>20% off peak)", "CAPE cheap\n(<20% pct)", "VIX panic\n(>40)",
              "25d crash\n(<-12%)", "CAPE bubble\n(>85%)", "VIX calm\n(<12)"]
    keys = ["deep", "cheap", "panic", "crash", "bubble", "calm"]
    rates = [stats[k][1] for k in keys]
    cols = ["#2ca02c", "#1f77b4", "#d62728", "#9467bd", "#ff7f0e", "#8c8c8c"]
    bars = ax[0].bar(labels, rates, color=cols)
    ax[0].set_ylabel("share of monthly decisions")
    ax[0].set_title("How often each signal fires (2000–2026, 318 months)")
    ax[0].set_ylim(0, max(rates) * 1.2)
    for b, v in zip(bars, rates):
        ax[0].text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.0%}",
                   ha="center", fontsize=9)
    ax[0].tick_params(axis="x", labelsize=8)
    ax[0].grid(True, axis="y", alpha=0.3)

    # (b) ablation
    names = ["all 3", "no CAPE", "no DD", "no VIX"]
    irr = [abl["all"][0], abl["no_cape"][0], abl["no_dd"][0], abl["no_vix"][0]]
    mdd = [abl["all"][1], abl["no_cape"][1], abl["no_dd"][1], abl["no_vix"][1]]
    x = np.arange(len(names))
    ax2 = ax[1]
    b1 = ax2.bar(x - 0.2, irr, 0.4, label="avg IRR", color="#2563eb")
    b2 = ax2.bar(x + 0.2, [abs(v) for v in mdd], 0.4, label="avg |MDD|", color="#ef4444", alpha=0.8)
    ax2.set_xticks(x); ax2.set_xticklabels(names)
    ax2.set_title("Ablation — remove one signal at a time")
    ax2.set_ylabel("rate")
    ax2.legend(fontsize=9)
    ax2.grid(True, axis="y", alpha=0.3)
    for b, v in zip(b1, irr):
        ax2.text(b.get_x() + b.get_width() / 2, v + 0.005, f"{v:.0%}", ha="center", fontsize=8)
    for b, v in zip(b2, mdd):
        ax2.text(b.get_x() + b.get_width() / 2, abs(v) + 0.005, f"{v:.0%}", ha="center", fontsize=8)

    fig.tight_layout()
    p = os.path.join(PLOTS, "signal_analysis.png")
    fig.savefig(p, dpi=110)
    return p


def run():
    df = build_signals(load_dataset())
    stats = trigger_stats(df)
    abl = ablation()
    make_chart(stats, abl)
    return stats, abl


if __name__ == "__main__":
    stats, abl = run()
    print("fire rates:", {k: f"{v[1]:.0%}" for k, v in stats.items() if isinstance(v, tuple)})
    print("major bottoms all CAPE-gated:", stats["major"][0] == stats["major_cape"])
    print("VIX-unique bottoms:", stats["major_vix_unique"])
    print("ablation:", {k: (f"{a:.1%}", f"{b:.1%}") for k, (a, b) in abl.items()})
    print("saved plots/signal_analysis.png")
