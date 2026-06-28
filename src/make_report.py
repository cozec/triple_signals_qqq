"""Generate report.html — an article-styled report of the backtest results.

Mirrors the visual structure of the source X article (stepwise sections with
card tables), but populated with THIS repo's reproduced numbers, plus an honest
side-by-side against the article's claims. Plots are embedded as base64 so the
file is fully self-contained and portable.
"""
import base64
import os
import pandas as pd
import signal_analysis as SA

SIG, ABL = SA.run()   # signal fire-rate stats + ablation, also writes the chart

ROOT = os.path.join(os.path.dirname(__file__), "..")
RESULTS = os.path.join(ROOT, "results")
PLOTS = os.path.join(ROOT, "plots")

m = pd.read_csv(os.path.join(RESULTS, "backtest_metrics.csv"))
STARTS = [2000, 2005, 2010, 2015, 2020]
NAMES = ["QQQ DCA", "TQQQ DCA", "Three-Signal"]
COLOR = {"QQQ DCA": "#1f77b4", "TQQQ DCA": "#d62728", "Three-Signal": "#2ca02c"}

# Article's own claimed figures (from the screenshots) for the honesty panel.
ARTICLE = {
    "QQQ DCA":      {"irr": .192, "mdd": -.357, "mult": 6.7},
    "TQQQ DCA":     {"irr": .373, "mdd": -.837, "mult": 58.7},
    "Three-Signal": {"irr": .340, "mdd": -.522, "mult": 119.4},
}


def g(start, name, col):
    return m[(m.start == start) & (m.strategy == name)][col].iloc[0]


def avg(name, col):
    return m[m.strategy == name][col].mean()


def b64(fname):
    with open(os.path.join(PLOTS, fname), "rb") as f:
        return base64.b64encode(f.read()).decode()


def pct(x):
    return f"{x*100:.1f}%"


def mult(x):
    return f"{x:.1f}×"


def table(headers, rows, highlight_col=None):
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = ""
    for r in rows:
        tds = "".join(f"<td>{c}</td>" for c in r)
        trs += f"<tr>{tds}</tr>"
    return f'<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'


def metric_table(name):
    rows = []
    labels = {2000: "2000 (bubble-top entry)", 2005: "2005", 2010: "2010",
              2015: "2015", 2020: "2020"}
    for s in STARTS:
        rows.append([labels[s], pct(g(s, name, "irr")),
                     pct(g(s, name, "mdd")), mult(g(s, name, "multiple"))])
    rows.append([f"<b>5-start avg</b>", f"<b>{pct(avg(name,'irr'))}</b>",
                 f"<b>{pct(avg(name,'mdd'))}</b>", f"<b>{mult(avg(name,'multiple'))}</b>"])
    return table(["Start", "IRR (ann.)", "Max DD", "Terminal mult."], rows)


def compare_table(start):
    rows = []
    # order by terminal multiple desc within the start
    sub = m[m.start == start].sort_values("multiple", ascending=False)
    for _, r in sub.iterrows():
        dot = f'<span class="dot" style="background:{COLOR[r.strategy]}"></span>'
        rows.append([dot + r.strategy, pct(r.irr), pct(r.mdd), mult(r.multiple)])
    return table(["Strategy", "IRR", "Max DD", "Terminal mult."], rows)


CSS = """
:root{--ink:#1a1f26;--muted:#5c6773;--line:#e7ebf0;--bg:#f6f8fa;--card:#fff;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
 line-height:1.65;font-size:16px;}
.wrap{max-width:820px;margin:0 auto;padding:48px 22px 90px;}
h1{font-size:30px;line-height:1.3;margin:0 0 6px;letter-spacing:-.3px;}
.sub{color:var(--muted);font-size:15px;margin-bottom:30px;}
h2{font-size:22px;margin:46px 0 14px;padding-left:12px;border-left:4px solid #3b82f6;}
h3{font-size:17px;margin:26px 0 10px;color:#2b3138;}
p{margin:12px 0;color:#27313b;}
ul{margin:12px 0;padding-left:22px;}li{margin:5px 0;}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;
 padding:6px 4px;margin:18px 0;box-shadow:0 1px 2px rgba(16,24,40,.04);overflow:hidden;}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;}
thead th{background:#f0f3f7;color:#3a444f;font-weight:600;font-size:13px;
 text-align:right;padding:12px 16px;border-bottom:1px solid var(--line);}
thead th:first-child{text-align:left;}
tbody td{padding:11px 16px;text-align:right;border-bottom:1px solid #f0f2f5;font-size:14.5px;}
tbody td:first-child{text-align:left;color:#2b3138;}
tbody tr:last-child td{border-bottom:none;background:#fafbfc;}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:8px;vertical-align:middle;}
.note{background:#f4f6f8;border:1px solid var(--line);border-radius:10px;
 padding:12px 16px;color:var(--muted);font-size:14px;margin:14px 0;}
.callout{border-radius:12px;padding:16px 20px;margin:20px 0;font-size:15px;}
.callout.warn{background:#fff7ed;border:1px solid #fed7aa;color:#7c2d12;}
.callout.ok{background:#ecfdf5;border:1px solid #a7f3d0;color:#065f46;}
.callout b{color:inherit;}
.kpis{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;}
.kpi{flex:1;min-width:150px;background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 16px;}
.kpi .l{font-size:12.5px;color:var(--muted);}
.kpi .v{font-size:22px;font-weight:700;margin-top:3px;}
img{width:100%;border:1px solid var(--line);border-radius:12px;margin:14px 0;background:#fff;}
.cmp td.good{color:#047857;font-weight:600;}
.cmp td.bad{color:#b91c1c;font-weight:600;}
footer{margin-top:50px;padding-top:18px;border-top:1px solid var(--line);
 color:var(--muted);font-size:13px;}
a{color:#2563eb;text-decoration:none;}
"""


def kpi_row():
    qi, ti, si = avg("QQQ DCA", "irr"), avg("TQQQ DCA", "irr"), avg("Three-Signal", "irr")
    return f"""<div class="kpis">
 <div class="kpi"><div class="l">QQQ DCA — avg IRR</div><div class="v" style="color:{COLOR['QQQ DCA']}">{pct(qi)}</div></div>
 <div class="kpi"><div class="l">Three-Signal — avg IRR</div><div class="v" style="color:{COLOR['Three-Signal']}">{pct(si)}</div></div>
 <div class="kpi"><div class="l">TQQQ DCA — avg IRR</div><div class="v" style="color:{COLOR['TQQQ DCA']}">{pct(ti)}</div></div>
</div>"""


def reproduction_table():
    rows = []
    for name in NAMES:
        a = ARTICLE[name]
        mine = {"irr": avg(name, "irr"), "mdd": avg(name, "mdd"), "mult": avg(name, "multiple")}
        # match flag on IRR (within 3pts) for color
        close = abs(mine["irr"] - a["irr"]) < 0.03 and abs(mine["mdd"] - a["mdd"]) < 0.08
        verdict = ('<td class="good">reproduced</td>' if close
                   else '<td class="bad">return only</td>' if abs(mine["irr"]-a["irr"]) < 0.05
                   else '<td class="bad">diverges</td>')
        dot = f'<span class="dot" style="background:{COLOR[name]}"></span>'
        rows.append(
            f"<tr><td>{dot}{name}</td>"
            f"<td>{pct(a['irr'])} / {pct(a['mdd'])} / {mult(a['mult'])}</td>"
            f"<td>{pct(mine['irr'])} / {pct(mine['mdd'])} / {mult(mine['mult'])}</td>"
            f"{verdict}</tr>")
    body = "".join(rows)
    return ('<table class="cmp"><thead><tr><th>Strategy</th>'
            '<th>Article claim (IRR / MDD / mult)</th>'
            '<th>This reproduction</th><th>Verdict</th></tr></thead>'
            f'<tbody>{body}</tbody></table>')


HTML = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Is DCA-ing the Nasdaq Optimal? — Three-Signal QQQ/TQQQ Backtest</title>
<style>{CSS}</style></head><body><div class="wrap">

<h1>Is dollar-cost-averaging the Nasdaq really optimal?</h1>
<div class="sub">A reproduction &amp; stress-test of the three-signal (CAPE + Drawdown + VIX)
dynamic-leverage framework from
<a href="https://x.com/app_sail/status/2070037504674173060">this X article</a>.
DCA <b>$10,000 on the first trading day of every month</b>, five start points → mid-2026.
Leverage ETF = synthetic 3×-Nasdaq before 2010, real TQQQ after.</div>

<div class="callout ok"><b>Reproduction status.</b> The QQQ and TQQQ DCA tables below
match the article almost exactly, validating the data and engine. The three-signal
framework matches the article on <b>return</b> (~31.6% vs claimed 34%) but <b>not</b>
on drawdown (−70.9% vs −52%) or terminal multiple — see the final section for why.</div>

{kpi_row()}

<h2>Step 1 — Is DCA-ing only QQQ good enough?</h2>
<p>One ruleset, applied to every strategy that follows:</p>
<ul>
 <li><b>Start points:</b> 2000, 2005, 2010, 2015, 2020</li>
 <li><b>Execution:</b> invest $10,000 on the first trading day of each month, through mid-2026</li>
 <li><b>Metrics:</b> IRR (money-weighted annualized return), Max Drawdown (MDD), terminal multiple (final value ÷ total invested)</li>
</ul>
<p>The QQQ DCA profile:</p>
<div class="card">{metric_table("QQQ DCA")}</div>
<div class="note">Earlier starts show higher terminal multiples (more years of compounding);
IRR is actually slightly <i>higher</i> for later starts, which dodge the 2000/2008 bear drag.</div>
<p><b>Verdict:</b> QQQ is steady but not aggressive — broadly positive through cycles,
drawdowns contained in the −31% to −48% range, ~19% average IRR. A respectable floor,
but, as the next line shows, not the efficiency frontier.</p>

<h2>Step 2 — TQQQ: stunning returns, brutal drawdowns</h2>
<p>Same starts and monthly amount, into the 3× leveraged TQQQ instead:</p>
<div class="card">{metric_table("TQQQ DCA")}</div>
<p>Average IRR ~37.7% — roughly double QQQ — and a ~60× average terminal multiple.
But the path runs through a <b>−84% average drawdown</b> (−92.8% from the 2000 start):
to reach that terminal value you must keep contributing while the account falls ~90%.
That is the real killer — not ruin, but a drawdown almost no one holds through.</p>

<h2>Step 3 — The three-signal framework</h2>
<p>The idea: hold QQQ as the core, deploy TQQQ as a dynamically-sized accelerator —
heavy only when the market is cheap, deeply fallen, and panicked; trimmed toward a floor
when valuations are stretched.</p>

<h3>The three base signals</h3>
<div class="card"><div style="padding:6px 18px 12px">
 <p style="margin:14px 0 6px"><b>① Valuation — CAPE percentile</b></p>
 <ul style="margin:4px 0">
  <li>below 20% → extremely cheap</li>
  <li>above 70% → overvalued</li>
  <li>above 85% → bubble-warning zone</li>
 </ul>
 <p style="margin:18px 0 6px"><b>② Trend &amp; drawdown — DD</b></p>
 <ul style="margin:4px 0">
  <li>drawdown from the high &gt; 20% → deeply oversold</li>
  <li>a fall &gt; 12% within 25 days → crash warning (used to cut leverage)</li>
 </ul>
 <p style="margin:18px 0 6px"><b>③ Panic — VIX</b></p>
 <ul style="margin:4px 0">
  <li>above 40 → extreme panic</li>
  <li>below 12 → excessive calm (usually appears in overvalued zones)</li>
 </ul>
 <div class="note" style="margin:16px 0 4px">All signals are lightly smoothed with a
  5-day average, and evaluated only once — on the first trading day of each month.</div>
</div></div>
<div class="note">In this reproduction, CAPE percentile uses a trailing 10-year window
(the article doesn't specify one; a full-history percentile pins valuations permanently
“expensive” after 2010). CAPE = S&amp;P-500 Shiller CAPE as a market-valuation proxy.</div>

<p>“LOW” signals counted for bottoms: CAPE&lt;20% + drawdown&lt;−20% + VIX&gt;40. Two or more
firing ⇒ all-in TQQQ; one ⇒ tilt up; stretched/overheated ⇒ trim the TQQQ sleeve toward a
30% floor and stockpile cash (“ammo”) for the next bottom.</p>

<h2>Step 4 — Head-to-head results</h2>
<h3>2000 start (worst-case bubble top)</h3>
<div class="card">{compare_table(2000)}</div>
<h3>2005 start (only the 2008 hit)</h3>
<div class="card">{compare_table(2005)}</div>
<h3>2010 start (TQQQ's golden window)</h3>
<div class="card">{compare_table(2010)}</div>
<h3>2015 &amp; 2020 starts (short windows)</h3>
<div class="card">{compare_table(2015)}</div>
<div class="card">{compare_table(2020)}</div>
<p>Consistent with the article's own caveat: over <i>short</i> windows that haven't yet met a
major bottom (2015/2020), raw TQQQ leads on both IRR and terminal value — the three-signal's
crisis-buying edge hasn't been paid out yet, though its shallower drawdown already protects you.</p>

<h3>Five-start average</h3>
<div class="card">{table(["Metric","QQQ DCA","TQQQ DCA","Three-Signal"],[
  ["Avg IRR", pct(avg("QQQ DCA","irr")), pct(avg("TQQQ DCA","irr")), f"<b>{pct(avg('Three-Signal','irr'))}</b>"],
  ["Avg Max DD", pct(avg("QQQ DCA","mdd")), pct(avg("TQQQ DCA","mdd")), f"<b>{pct(avg('Three-Signal','mdd'))}</b>"],
  ["Avg terminal mult.", mult(avg("QQQ DCA","multiple")), mult(avg("TQQQ DCA","multiple")), f"<b>{mult(avg('Three-Signal','multiple'))}</b>"],
])}</div>

<h2>Reproduction vs the article's claims</h2>
<p>The article's three-signal headline (34% IRR at only −52% drawdown, beating even
buy-and-hold TQQQ on terminal value) was produced by an AI tool that iterated a dozen
backtests on this exact 2000–2026 path — the classic signature of <b>in-sample
over-optimization</b>. This reproduction deliberately does not fit to the drawdown target,
so it shows the honest trade-off.</p>
<div class="card">{reproduction_table()}</div>
<div class="callout warn"><b>The honest finding.</b> You can capture most of TQQQ's
return with the three-signal rules (~31.6% IRR) — but <b>not</b> at half the drawdown.
The aggressive bottom-buying that drives the excess return necessarily rides the −90%
collapses of 2000–02 and 2008, so the average drawdown (−70.9%) lands much closer to
TQQQ than to the article's −52% claim.</div>

<h2>Step 5 — Which of the three signals actually matters?</h2>
<p>The framework is named for three signals, but do they pull equal weight? Measured
two ways over the 318 monthly decisions from 2000 to 2026.</p>

<h3>How often each fires</h3>
<div class="card">{table(["Signal","Months","Fire rate","What it's really detecting"],[
  [f'<span class="dot" style="background:#2ca02c"></span>DD — drawdown &gt;20% off peak', f'{SIG["deep"][0]}', pct(SIG["deep"][1]), "a slow <i>regime</i> flag, not a crash timer (see note)"],
  [f'<span class="dot" style="background:#1f77b4"></span>CAPE — percentile &lt;20%', f'{SIG["cheap"][0]}', pct(SIG["cheap"][1]), "the binding gate on every buy decision"],
  [f'<span class="dot" style="background:#d62728"></span>VIX — &gt;40', f'{SIG["panic"][0]}', pct(SIG["panic"][1]), "rare capitulation confirmation only"],
  [f'25-day crash &lt; −12%', f'{SIG["crash"][0]}', pct(SIG["crash"][1]), "the <i>useful</i> drawdown variant — fresh crashes"],
])}</div>
<div class="note">Why DD fires 55% of the time: QQQ did not reclaim its March-2000 peak
until ~2015, so “drawdown &gt;20% from the all-time high” was <b>continuously true</b> for
most of 2002–2013. That makes from-peak DD a sticky “still underwater” flag rather than a
sharp timing signal — the 25-day fast-drop (4% of months) is the real crash detector.</div>

<p>Crucially, <b>all {SIG["major"][0]} “major bottom” (all-in TQQQ) months are exactly the
CAPE-cheap months</b> — because DD is almost always on, CAPE is the differentiator that
gates the buy. VIX never triggered a major bottom on its own. The three signals are highly
<b>redundant</b>: cheap valuation, deep drawdown and high VIX all coincide at the same
events (crashes), so “2 of 3” mostly reduces to “CAPE-cheap + already-deep.”</p>

<h3>Ablation — remove one signal at a time</h3>
<div class="card">{table(["Configuration","Avg IRR","Avg Max DD"],[
  ["<b>All three (baseline)</b>", f'<b>{pct(ABL["all"][0])}</b>', f'<b>{pct(ABL["all"][1])}</b>'],
  ["remove CAPE", pct(ABL["no_cape"][0]), pct(ABL["no_cape"][1])],
  ["remove DD", pct(ABL["no_dd"][0]), pct(ABL["no_dd"][1])],
  ["remove VIX", pct(ABL["no_vix"][0]), pct(ABL["no_vix"][1])],
])}</div>
<img src="data:image/png;base64,{b64('signal_analysis.png')}" alt="Signal fire rates and ablation">

<div class="callout warn"><b>The verdict.</b> Removing <i>any</i> single signal moves average IRR
by ≤1 point. The returns come overwhelmingly from the always-on TQQQ core weight, not the
signal timing — the signals mainly nudge <i>when</i> you concentrate (a few points of
drawdown), not the headline return. Of the three, <b>CAPE carries the only real
decision information</b> (it gates both buying and trimming); from-peak DD is too sticky to
time anything; <b>VIX is largely redundant</b>. The “three-signal” trio adds only marginally
over simply holding a high-TQQQ core — consistent with the earlier finding that the edge is
mostly in-sample story-telling.</div>

<footer>
Synthetic TQQQ validated vs real (2010–2026): daily-return correlation 0.9989, CAGR 73.2% vs 73.2%.
CAPE = S&P-500 Shiller CAPE (multpl.com); QQQ/TQQQ/VIX/T-bill via yfinance. Full methodology
&amp; assumptions in <code>summary.md</code>.<br><br>
<b>Research / education only — not investment advice.</b> Leveraged-ETF DCA can lose 70–90% in a bear market.
</footer>

</div></body></html>"""

out = os.path.join(ROOT, "report.html")
with open(out, "w") as f:
    f.write(HTML)
print("wrote", out, f"({len(HTML)//1024} KB)")
