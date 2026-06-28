# Summary — Triple-Signal QQQ/TQQQ DCA Backtest

**Source strategy:** [app_sail X article](https://x.com/app_sail/status/2070037504674173060)
("定投纳指，真的是最优解吗？" — *Is DCA-ing the Nasdaq really optimal?*). Full
text in [`artical_from_x.txt`](artical_from_x.txt).

**Method:** DCA **$10,000 on the first trading day of every month** into each
strategy, over five start points (2000, 2005, 2010, 2015, 2020) to 2026-06-26.
Leverage ETF = **synthetic 3×-Nasdaq before 2010-02-11, real TQQQ after**.
All figures from `src/strategies.py` on 2026-06 data.

---

## 1. Bottom line

| Strategy | Avg IRR | Avg Max DD | Avg multiple | Avg Sharpe | Avg Beta |
|---|---:|---:|---:|---:|---:|
| QQQ DCA | 19.4% | −35.7% | 6.8× | 0.79 | 1.00 |
| **Three-Signal** | **31.6%** | **−70.9%** | **30.3×** | 0.73 | 2.01 |
| TQQQ DCA | 37.7% | −83.7% | 59.9× | 0.70 | 2.96 |

- **QQQ DCA and TQQQ DCA reproduce the article almost exactly** (article: QQQ
  ~19% IRR / −36% / 6.7×; TQQQ ~37.3% / −84% / 58.7×). This validates the data
  pipeline, the TQQQ synthesis, and the DCA engine.
- **The three-signal framework matches the article on return (31.5% vs claimed
  34%) but NOT on drawdown (−71% vs claimed −52%) or terminal multiple
  (30.3× vs claimed 119×).** The article's risk numbers appear to be
  in-sample-optimized (see §5). The *qualitative* thesis holds: the framework
  earns close to TQQQ's return with less than full TQQQ exposure, and it beats
  plain QQQ on return — but it does **not** deliver TQQQ-like returns at half
  the drawdown in this reconstruction.

---

## 2. Per-start results

Strategies ordered by final equity within each start.

#### Start 2000  (invested $3.18M over 318 months)
| Strategy | Final equity | Mult | IRR | Max DD | Sharpe | Alpha | Beta |
|---|---:|---:|---:|---:|---:|---:|---:|
| TQQQ DCA | $370.5M | 116.5× | 28.6% | −92.8% | 0.37 | −6.0% | 2.98 |
| Three-Signal | $184.0M | 57.9× | 24.6% | −92.0% | 0.33 | −5.7% | 2.24 |
| QQQ DCA | $38.5M | 12.1× | 15.8% | −48.0% | 0.44 | +0.0% | 1.00 |

#### Start 2005  (invested $2.58M over 258 months)
| Strategy | Final equity | Mult | IRR | Max DD | Sharpe | Alpha | Beta |
|---|---:|---:|---:|---:|---:|---:|---:|
| TQQQ DCA | $283.0M | 109.7× | 35.9% | −90.9% | 0.68 | −5.4% | 2.97 |
| Three-Signal | $139.0M | 53.9× | 30.7% | −89.9% | 0.65 | −4.8% | 2.27 |
| QQQ DCA | $25.1M | 9.7× | 18.2% | −43.1% | 0.77 | +0.0% | 1.00 |

#### Start 2010  (invested $1.98M over 198 months)
| Strategy | Final equity | Mult | IRR | Max DD | Sharpe | Alpha | Beta |
|---|---:|---:|---:|---:|---:|---:|---:|
| TQQQ DCA | $113.7M | 57.4× | 42.4% | −81.6% | 0.87 | −4.6% | 2.96 |
| Three-Signal | $58.0M | 29.3× | 35.5% | −65.3% | 0.91 | −0.3% | 2.00 |
| QQQ DCA | $12.6M | 6.4× | 20.0% | −33.8% | 0.95 | −0.0% | 1.00 |

#### Start 2015  (invested $1.38M over 138 months)
| Strategy | Final equity | Mult | IRR | Max DD | Sharpe | Alpha | Beta |
|---|---:|---:|---:|---:|---:|---:|---:|
| TQQQ DCA | $16.5M | 11.9× | 40.0% | −80.9% | 0.82 | −6.1% | 2.96 |
| Three-Signal | $10.6M | 7.7× | 33.0% | −63.4% | 0.91 | +1.3% | 1.74 |
| QQQ DCA | $5.0M | 3.6× | 21.0% | −31.4% | 0.91 | +0.0% | 1.00 |

#### Start 2020  (invested $0.78M over 78 months)
| Strategy | Final equity | Mult | IRR | Max DD | Sharpe | Alpha | Beta |
|---|---:|---:|---:|---:|---:|---:|---:|
| TQQQ DCA | $2.9M | 3.8× | 41.8% | −72.1% | 0.78 | −7.8% | 2.96 |
| Three-Signal | $2.3M | 3.0× | 34.1% | −44.0% | 0.84 | −0.2% | 1.79 |
| QQQ DCA | $1.6M | 2.0× | 22.0% | −22.4% | 0.88 | +0.0% | 1.00 |

**Reading the table.** Drawdown control *does* work for later starts — 2020
three-signal cuts TQQQ's −72% to −44%, 2010 cuts −82% to −65%. But for 2000/2005
starts the framework buys aggressively into the 2000–02 and 2008 collapses and
suffers ~−90%, nearly as deep as TQQQ. Those deep early drawdowns drag the
5-start average to −71%. The article reports a clean −52% average, which our
faithful reading cannot match without additional, unspecified pre-crash
de-risking.

> Metric notes: **IRR** = money-weighted annualized internal rate of return of
> the monthly −$10k cashflows plus final value (the correct return measure for
> DCA; a simple CAGR/buy-&-hold formula does not apply to a contribution
> stream). **Max DD** = peak-to-trough of the daily account equity (includes
> contributions). **Sharpe / Alpha / Beta** from time-weighted daily returns vs
> QQQ DCA as benchmark (alpha annualized).

---

## 3. Data & TQQQ synthesis

| Series | Source | Span |
|---|---|---|
| QQQ (Adj Close, total return) | yfinance | 1999-03 → 2026-06 |
| TQQQ (Adj Close, real) | yfinance | 2010-02-11 → 2026-06 |
| ^VIX | yfinance | 1990 → 2026-06 |
| ^IRX (13-wk T-bill, financing) | yfinance | 1999 → 2026-06 |
| Shiller S&P-500 CAPE (monthly) | multpl.com | 1871 → 2026-06 |

**Synthetic TQQQ** (pre-2010): `r_tqqq = 3·r_qqq − [2·(rf + spread) + ER]/252`,
with ER = 0.95%/yr, financing spread = 0.80%/yr (calibrated), rf = ^IRX.

**Validation vs real TQQQ (2010–2026 overlap):**
- daily-return correlation **0.9989**
- synthetic CAGR **73.2%** vs real **73.2%** (spread calibrated to match)
- annualized tracking error 2.95%

See `plots/tqqq_synth_validation.png`. The synthesis is accurate; pre-2010
results are trustworthy to within the usual leveraged-ETF modeling error.

**CAPE caveat:** the article says "CAPE" without specifying the index. No
standard public Nasdaq CAPE exists, so we use the **S&P-500 Shiller CAPE** as a
broad valuation-regime proxy. Percentile is computed over a **trailing 10-year
window** (see §4).

---

## 4. The three-signal framework (as implemented)

Signals evaluated on the **first trading day of each month**, 5-day smoothed:

| Signal | Measure | Thresholds |
|---|---|---|
| Valuation | CAPE percentile (trailing 10-yr) | cheap <20% · high >70% · bubble >85% |
| Drawdown | QQQ drop from running peak | deep < −20% |
| Crash | QQQ 25-day return | < −12% |
| Panic | VIX level | panic >40 · calm <12 |

**"LOW" signals** (counted for bottoms): `CAPE<20%` + `DD<−20%` + `VIX>40`.

**Monthly decision** — a tiered *target-TQQQ-weight* engine ("accelerator locked
between a floor and a ceiling"). Cash already holds the month's $10k + interest:

| Regime | Action (target TQQQ weight of risky sleeve) |
|---|---|
| ≥2 LOW (major bottom) | deploy **all** cash, weight → 100% TQQQ, arm 6-mo ramp |
| 1 LOW or ramp window | deploy cash, weight → 75% |
| 25-day crash < −12% | de-risk: halve current TQQQ weight (toward floor), hold cash |
| CAPE >70% & near high | de-risk to floor (30%), hold contribution as ammo |
| Overheated ≥6 mo (VIX<12 or CAPE>85%) | trim 1/12 toward floor, hold cash |
| Normal | invest contribution, hold base weight (55%) |

Floor 30%, base 55%, minor 75%, ceiling 100%. Ammo cash earns the daily T-bill
rate.

### Interpretation choices (the article is prose, not a spec)
1. **Target-weight, not literal decision tree.** The article's literal
   contribution-multiplier tree (default → QQQ, only buy TQQQ at 2-of-3 bottoms)
   produces **QQQ-like returns (~15% IRR)**, because the cheap-CAPE signal almost
   never fires and 2-signal bottoms are rare. The article's ~34% IRR is only
   reachable if TQQQ is held *continuously* between a floor and ceiling — which
   the article also explicitly describes ("TQQQ as accelerator locked between a
   floor and ceiling; QQQ as the hub"). We implemented that design intent.
2. **Trailing-10-yr CAPE percentile.** With a full-history (1871→) percentile,
   today's CAPE sits above the 70th percentile almost always, pinning the
   strategy in permanent "de-risk" mode. A trailing window makes the signal
   adaptive (cheap fires at real selloffs). Window choice swings average IRR
   from 27% (full history) to 31.5% (10-yr).
3. **Floor/base/ceiling weights** were lightly calibrated so average IRR lands
   near the article; they were **not** fit to drawdown. The drawdown gap is real,
   not a tuning artifact.

Unspecified-in-article items we had to choose: exact floor/ceiling levels,
rebalance mechanics (we rebalance the sleeve to target monthly), the "near high"
threshold (within 5% of peak), ammo interest rate (T-bill), and the 6-month ramp
mechanics.

---

## 5. Why the article's exact numbers don't reproduce

| Metric | Article (3-signal) | This repo | Match? |
|---|---:|---:|---|
| Avg IRR | 34% | 31.5% | close |
| Avg Max DD | −52% | −70.9% | **no** |
| Avg multiple | 119× | 30.3× | **no** |
| 2000-start vs QQQ | ~33× | ~4.8× | **no** |

The article was produced by an AI tool ("Apodex") that *iterated a dozen
backtests on this exact 2000–2026 sample*. Its three-signal beats even **buy-hold
TQQQ on terminal value** (119× vs 59×) while halving drawdown — a profile that is
extremely hard to achieve out-of-sample and is the classic signature of
**in-sample over-optimization** (parameters tuned until the one historical path
looks ideal). Our reconstruction deliberately avoids fitting to the drawdown
target, so it reveals the honest trade-off: **you can get most of TQQQ's return,
but not at half its drawdown** — buying aggressively at bottoms (the source of
the excess return) necessarily means riding large drawdowns through 2000–02 and
2008.

The article itself concedes the framework's edge only appears over long windows
that include a major crash, and that from a high-valuation entry like mid-2026
it may *trail* QQQ until the next big drawdown arrives.

---

## 6. Files
- `src/download_data.py` — pull all data
- `src/data_prep.py` — unified dataset + TQQQ synthesis + CAPE percentile
- `src/validate_tqqq.py` — synthetic-vs-real TQQQ validation
- `src/strategies.py` — single-file engine: 3 strategies, metrics, driver
- `src/plots.py` — charts
- `results/backtest_metrics.csv`, `results/avg_by_strategy.csv`
- `plots/equity_curves_by_start.png`, `plots/irr_mdd_by_start.png`, `plots/tqqq_synth_validation.png`

*Research/education only — not investment advice. Leveraged-ETF DCA can lose
70–90% in a bear market.*
