"""Generate comparison plots from the saved equity curves."""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
PLOTS = os.path.join(os.path.dirname(__file__), "..", "plots")
os.makedirs(PLOTS, exist_ok=True)

COLORS = {"QQQ DCA": "#1f77b4", "TQQQ DCA": "#d62728", "Three-Signal": "#2ca02c"}
STARTS = ["2000", "2005", "2010", "2015", "2020"]


def main():
    curves = pd.read_pickle(os.path.join(RESULTS, "equity_curves.pkl"))

    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    axes = axes.ravel()
    for i, yr in enumerate(STARTS):
        ax = axes[i]
        for name in COLORS:
            eq = curves[(yr, name)]
            ax.plot(eq.index, eq.values, label=name, color=COLORS[name], lw=1.2)
        ax.set_yscale("log")
        ax.set_title(f"Start {yr}  (DCA $10k/mo)")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    axes[-1].axis("off")
    fig.suptitle("Account equity (log scale) — QQQ vs TQQQ vs Three-Signal DCA",
                 fontsize=14)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "equity_curves_by_start.png"), dpi=110)
    print("saved plots/equity_curves_by_start.png")

    # Bar chart of IRR and MDD by start
    m = pd.read_csv(os.path.join(RESULTS, "backtest_metrics.csv"))
    fig, ax = plt.subplots(1, 2, figsize=(15, 5))
    piv_irr = m.pivot(index="start", columns="strategy", values="irr")[list(COLORS)]
    piv_mdd = m.pivot(index="start", columns="strategy", values="mdd")[list(COLORS)]
    piv_irr.plot.bar(ax=ax[0], color=[COLORS[c] for c in COLORS])
    ax[0].set_title("Annualized IRR by start point"); ax[0].grid(True, axis="y", alpha=0.3)
    ax[0].set_ylabel("IRR"); ax[0].axhline(0, color="k", lw=0.6)
    piv_mdd.plot.bar(ax=ax[1], color=[COLORS[c] for c in COLORS])
    ax[1].set_title("Max drawdown by start point"); ax[1].grid(True, axis="y", alpha=0.3)
    ax[1].set_ylabel("Max DD")
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS, "irr_mdd_by_start.png"), dpi=110)
    print("saved plots/irr_mdd_by_start.png")


if __name__ == "__main__":
    main()
