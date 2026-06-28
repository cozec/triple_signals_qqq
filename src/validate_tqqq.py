"""Validate the synthetic-TQQQ model against real TQQQ on the 2010-2026 overlap.

Builds synthetic TQQQ from QQQ over the period where real TQQQ EXISTS, then
compares daily returns and cumulative growth. A good model has high daily-return
correlation and modest cumulative tracking error.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from data_prep import load_dataset, TQQQ_INCEPTION, EXPENSE_RATIO, FIN_SPREAD

PLOTS = os.path.join(os.path.dirname(__file__), "..", "plots")
os.makedirs(PLOTS, exist_ok=True)


def main():
    df = load_dataset()
    ov = df[df.index >= TQQQ_INCEPTION].copy()
    qqq_ret = ov["qqq"].pct_change()
    cost = (2.0 * (ov["rf_daily"] + FIN_SPREAD / 252.0)) + (EXPENSE_RATIO / 252.0)
    syn_ret = 3.0 * qqq_ret - cost
    real_ret = ov["tqqq_real"].pct_change()

    j = pd.DataFrame({"syn": syn_ret, "real": real_ret}).dropna()
    corr = j["syn"].corr(j["real"])
    # cumulative growth from a common $1 base
    syn_cum = (1 + j["syn"]).cumprod()
    real_cum = (1 + j["real"]).cumprod()
    end_ratio = syn_cum.iloc[-1] / real_cum.iloc[-1]

    ann_syn = (1 + j["syn"].mean()) ** 252 - 1
    ann_real = (1 + j["real"].mean()) ** 252 - 1
    te = (j["syn"] - j["real"]).std() * np.sqrt(252)  # annualized tracking error

    print("=== Synthetic vs Real TQQQ (2010-02-11 .. {}) ===".format(ov.index.max().date()))
    print(f"daily return correlation : {corr:.4f}")
    print(f"synthetic CAGR           : {ann_syn:6.2%}")
    print(f"real TQQQ CAGR           : {ann_real:6.2%}")
    print(f"annualized tracking error: {te:6.2%}")
    print(f"end cumulative ratio syn/real: {end_ratio:.3f} "
          f"({'syn ahead' if end_ratio>1 else 'syn behind'} {abs(end_ratio-1):.1%})")

    fig, ax = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    ax[0].plot(real_cum.index, real_cum, label="Real TQQQ", lw=1.3)
    ax[0].plot(syn_cum.index, syn_cum, label="Synthetic 3x", lw=1.0, alpha=0.85)
    ax[0].set_yscale("log")
    ax[0].set_title("Synthetic vs Real TQQQ — growth of $1 (log scale)")
    ax[0].legend(); ax[0].grid(True, alpha=0.3)
    ax[1].scatter(j["real"], j["syn"], s=4, alpha=0.3)
    lim = [j[["real", "syn"]].min().min(), j[["real", "syn"]].max().max()]
    ax[1].plot(lim, lim, "r--", lw=1)
    ax[1].set_xlabel("real daily return"); ax[1].set_ylabel("synthetic daily return")
    ax[1].set_title(f"Daily returns (corr={corr:.4f})"); ax[1].grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "tqqq_synth_validation.png"), dpi=110)
    print("saved plots/tqqq_synth_validation.png")


if __name__ == "__main__":
    main()
