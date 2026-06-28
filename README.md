# Triple-Signal QQQ / TQQQ Backtest

Reproduction and stress-test of the **CAPE + Drawdown + VIX three-signal
dynamic-leverage DCA framework** described in this X article:
[app_sail · status/2070037504674173060](https://x.com/app_sail/status/2070037504674173060)
(article text saved in [`artical_from_x.txt`](artical_from_x.txt)).

The article's thesis: monthly dollar-cost-averaging (DCA) into plain QQQ is *not*
the optimal way to hold the Nasdaq long-term. A three-signal framework that
holds TQQQ as a dynamically-sized "accelerator" — heavy at crash bottoms, light
at valuation extremes — is claimed to lift average annualized return from ~19%
(QQQ) to ~34% while cutting TQQQ's ~−84% drawdown to ~−52%.

## What this repo does
1. **Downloads** QQQ, TQQQ, ^VIX, ^IRX (yfinance) and Shiller S&P-500 CAPE (multpl.com).
2. **Synthesizes** pre-2010 TQQQ from QQQ daily returns (`3× − financing − fees`),
   **validated** against real TQQQ on the 2010–2026 overlap (daily-return
   correlation **0.9989**, CAGR 73.2% vs 73.2%).
3. **Backtests** three strategies — QQQ DCA, TQQQ DCA, and the three-signal
   framework — over five start points (2000, 2005, 2010, 2015, 2020) to mid-2026,
   DCA $10,000 on the first trading day of every month.

## Headline result (5-start average)
| Strategy | IRR | Max DD | Terminal multiple |
|---|---:|---:|---:|
| QQQ DCA | 19.4% | −35.7% | 6.8× |
| **Three-Signal** | **31.6%** | **−70.9%** | **30.3×** |
| TQQQ DCA | 37.7% | −83.7% | 59.9× |

QQQ DCA and TQQQ DCA reproduce the article's numbers almost exactly. The
three-signal reconstruction matches the article on **return** (~31% vs claimed
34%) but **not on drawdown** (−71% vs claimed −52%). See
[`summary.md`](summary.md) for the full analysis, every modeling assumption, and
why the article's exact figures appear to be in-sample-optimized.

## Layout
```
src/   download_data.py   data_prep.py   validate_tqqq.py   strategies.py   plots.py
data/  qqq.csv tqqq.csv vix.csv irx.csv cape.csv          (gitignored)
       tqqq_synthetic_full.csv      <- continuous TQQQ TR index (synthetic pre-2010 + real after)
       tqqq_synthetic_pre2010.csv   <- the synthesized "missing" pre-2010 TQQQ only
results/ backtest_metrics.csv avg_by_strategy.csv equity_curves.pkl  (gitignored)
plots/   tqqq_synth_validation.png  equity_curves_by_start.png  irr_mdd_by_start.png
```

## Reproduce
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install yfinance pandas numpy matplotlib requests openpyxl xlrd lxml beautifulsoup4 scipy
python src/download_data.py        # QQQ/TQQQ/VIX/IRX  (CAPE: see download_data.py note)
python src/validate_tqqq.py        # synthetic-vs-real TQQQ check
python src/strategies.py           # run all backtests -> results/
python src/plots.py                # charts -> plots/
```

> **Disclaimer:** research/education only, not investment advice. TQQQ and
> leveraged DCA can lose 70–90% in a bear market.
