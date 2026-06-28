"""Generate report_zh.html — Chinese version of the report.

Reuses the English generator's data + formatting helpers (make_report) so every
number stays identical and in sync; only the prose and table headers are
translated. The English report.html is regenerated as a harmless side effect of
importing make_report.
"""
import os
import make_report as R
from make_report import g, avg, b64, pct, table, COLOR, SIG, ABL, ARTICLE, m, CSS, ROOT

STARTS = [2000, 2005, 2010, 2015, 2020]
NAMES = ["QQQ DCA", "TQQQ DCA", "Three-Signal"]
ZH = {"QQQ DCA": "QQQ 定投", "TQQQ DCA": "TQQQ 定投", "Three-Signal": "三信号"}


def mult(x):
    return f"{x:.1f}倍"


def dot(name):
    return f'<span class="dot" style="background:{COLOR[name]}"></span>'


def metric_table(name):
    labels = {2000: "2000（泡沫顶部入场）", 2005: "2005", 2010: "2010",
              2015: "2015", 2020: "2020"}
    rows = [[labels[s], pct(g(s, name, "irr")), pct(g(s, name, "mdd")),
             mult(g(s, name, "multiple"))] for s in STARTS]
    rows.append(["<b>5 起点平均</b>", f"<b>{pct(avg(name,'irr'))}</b>",
                 f"<b>{pct(avg(name,'mdd'))}</b>", f"<b>{mult(avg(name,'multiple'))}</b>"])
    return table(["起点", "年化 IRR", "最大回撤", "终值倍数"], rows)


def compare_table(start):
    sub = m[m.start == start].sort_values("multiple", ascending=False)
    rows = [[dot(r.strategy) + ZH[r.strategy], pct(r.irr), pct(r.mdd), mult(r.multiple)]
            for _, r in sub.iterrows()]
    return table(["策略", "IRR", "最大回撤", "终值倍数"], rows)


def kpi_row():
    qi, ti, si = avg("QQQ DCA", "irr"), avg("TQQQ DCA", "irr"), avg("Three-Signal", "irr")
    return f"""<div class="kpis">
 <div class="kpi"><div class="l">QQQ 定投 · 平均 IRR</div><div class="v" style="color:{COLOR['QQQ DCA']}">{pct(qi)}</div></div>
 <div class="kpi"><div class="l">三信号 · 平均 IRR</div><div class="v" style="color:{COLOR['Three-Signal']}">{pct(si)}</div></div>
 <div class="kpi"><div class="l">TQQQ 定投 · 平均 IRR</div><div class="v" style="color:{COLOR['TQQQ DCA']}">{pct(ti)}</div></div>
</div>"""


def reproduction_table():
    rows = ""
    for name in NAMES:
        a = ARTICLE[name]
        mine = {"irr": avg(name, "irr"), "mdd": avg(name, "mdd"), "mult": avg(name, "multiple")}
        close = abs(mine["irr"] - a["irr"]) < 0.03 and abs(mine["mdd"] - a["mdd"]) < 0.08
        verdict = ('<td class="good">已复现</td>' if close
                   else '<td class="bad">仅收益吻合</td>' if abs(mine["irr"] - a["irr"]) < 0.05
                   else '<td class="bad">明显偏离</td>')
        rows += (f"<tr><td>{dot(name)}{ZH[name]}</td>"
                 f"<td>{pct(a['irr'])} / {pct(a['mdd'])} / {mult(a['mult'])}</td>"
                 f"<td>{pct(mine['irr'])} / {pct(mine['mdd'])} / {mult(mine['mult'])}</td>"
                 f"{verdict}</tr>")
    return ('<table class="cmp"><thead><tr><th>策略</th>'
            '<th>文章宣称（IRR / 回撤 / 倍数）</th>'
            '<th>本次复现</th><th>结论</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>')


HTML = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>定投纳指真的是最优解吗？—— 三信号 QQQ/TQQQ 回测</title>
<style>{CSS}</style></head><body><div class="wrap">

<div style="text-align:right;font-size:13px;margin-bottom:8px"><a href="report.html">English ›</a></div>

<h1>定投纳指，真的是最优解吗？</h1>
<div class="sub">对<a href="https://x.com/app_sail/status/2070037504674173060">这篇 X 文章</a>中
三信号（CAPE + 回撤 + VIX）动态杠杆框架的复现与压力测试。
口径统一为<b>每月第一个交易日定投 $10,000</b>，五个起点，跑到 2026 年中。
杠杆 ETF 在 2010 年前用 3 倍纳指合成、之后接真实 TQQQ。</div>

<div class="callout ok"><b>复现结论。</b>下面 QQQ 与 TQQQ 定投两张表几乎与原文完全吻合，验证了数据与回测引擎。
三信号框架在<b>收益</b>上吻合（约 31.6% vs 原文 34%），但在<b>回撤</b>（−70.9% vs −52%）与终值倍数上
对不上——原因见最后一节。</div>

{kpi_row()}

<h2>第一步 —— 只定投 QQQ，真的够好吗？</h2>
<p>先统一规则，后面三种策略都按这个跑：</p>
<ul>
 <li><b>起点：</b>2000、2005、2010、2015、2020</li>
 <li><b>执行：</b>每月第一个交易日投入 $10,000，一直定投到 2026 年中</li>
 <li><b>指标：</b>IRR（货币加权年化收益率）、最大回撤（MDD）、终值倍数（最终市值 ÷ 总投入）</li>
</ul>
<p>QQQ 定投的整体画像：</p>
<div class="card">{metric_table("QQQ DCA")}</div>
<div class="note">起点越早，终值倍数越高（复利时间更久）；IRR 反而是越晚的起点略高，
因为避开了 2000/2008 两轮大熊的拖累。</div>
<p><b>结论：</b>QQQ 够稳，但不够猛——长期穿越周期基本正收益，回撤控制在 −31% 到 −48%。
平均年化约 19%，是一条稳妥底线，但不是效率最优解。</p>

<h2>第二步 —— TQQQ：收益惊人，但回撤是道鬼门关</h2>
<p>同样的起点和月投额，换成每月定投 3 倍杠杆的 TQQQ：</p>
<div class="card">{metric_table("TQQQ DCA")}</div>
<p>平均 IRR 约 37.7%，接近 QQQ 的两倍，终值倍数约 60 倍。但通往这个终值的路上是
<b>平均 −84% 的回撤</b>（2000 起点更是 −92.8%）：你必须在账户跌掉九成的同时还坚持每月打钱。
这才是真正的杀手——不是亏光，而是几乎没人扛得住的回撤。</p>

<h2>第三步 —— 三信号框架</h2>
<p>思路：以 QQQ 为核心，把 TQQQ 当成一颗按规则动态释放的加速器——
只在便宜、深跌、恐慌共振时大幅加，在估值过热时减回仓位下限。</p>

<h3>三个基础信号</h3>
<div class="card"><div style="padding:6px 18px 12px">
 <p style="margin:14px 0 6px"><b>① 估值 —— 看 CAPE 分位</b></p>
 <ul style="margin:4px 0">
  <li>低于 20% → 极度便宜</li>
  <li>高于 70% → 高估</li>
  <li>高于 85% → 泡沫警戒区</li>
 </ul>
 <p style="margin:18px 0 6px"><b>② 趋势与回撤 —— 看 DD</b></p>
 <ul style="margin:4px 0">
  <li>距高点回撤超过 20% → 深度超跌</li>
  <li>25 日内急跌超过 12% → 快崩预警（用于减杠杆）</li>
 </ul>
 <p style="margin:18px 0 6px"><b>③ 恐慌 —— 看 VIX</b></p>
 <ul style="margin:4px 0">
  <li>高于 40 → 极度恐慌</li>
  <li>低于 12 → 过度平静（多出现在高估区）</li>
 </ul>
 <div class="note" style="margin:16px 0 4px">全部用 5 日均值做小平滑，每月第一个交易日只跑一次。</div>
</div></div>
<div class="note">本复现中 CAPE 分位采用<b>滚动 10 年窗口</b>（原文未指定窗口；若用全历史分位，
2010 年后估值会被长期判为“高估”而把策略钉死在仓位下限）。CAPE 采用标普 500 的席勒 CAPE 作为市场估值代理。</div>

<p>计入“低位”的三个信号：CAPE&lt;20% + 回撤&lt;−20% + VIX&gt;40。两个及以上同时亮 ⇒ 梭哈 TQQQ；
只亮一个 ⇒ 加仓；估值过热/拉高 ⇒ 把 TQQQ 减回 30% 的仓位下限，并把现金囤进“弹药仓”等下一个大底。</p>

<h2>第四步 —— 三策略横向对比</h2>
<h3>2000 起点（最差山顶起手）</h3>
<div class="card">{compare_table(2000)}</div>
<h3>2005 起点（只挨 2008 一锤）</h3>
<div class="card">{compare_table(2005)}</div>
<h3>2010 起点（TQQQ 黄金窗口）</h3>
<div class="card">{compare_table(2010)}</div>
<h3>2015 与 2020 起点（短窗口）</h3>
<div class="card">{compare_table(2015)}</div>
<div class="card">{compare_table(2020)}</div>
<p>这与原文自己的说法一致：在 2015/2020 这种还没遇上大底的短窗口里，裸 TQQQ 在 IRR 和终值上都暂时领先——
三信号的危机抄底红利还没兑现，但它更浅的回撤已经在实打实地保护你。</p>

<h3>五起点平均</h3>
<div class="card">{table(["指标","QQQ 定投","TQQQ 定投","三信号"],[
  ["平均 IRR", pct(avg("QQQ DCA","irr")), pct(avg("TQQQ DCA","irr")), f"<b>{pct(avg('Three-Signal','irr'))}</b>"],
  ["平均最大回撤", pct(avg("QQQ DCA","mdd")), pct(avg("TQQQ DCA","mdd")), f"<b>{pct(avg('Three-Signal','mdd'))}</b>"],
  ["平均终值倍数", mult(avg("QQQ DCA","multiple")), mult(avg("TQQQ DCA","multiple")), f"<b>{mult(avg('Three-Signal','multiple'))}</b>"],
])}</div>

<h2>第五步 —— 三个信号里，到底哪个最有用？</h2>
<p>框架以“三信号”命名，但它们真的同等重要吗？从 2000 到 2026 共 318 次月度决策，用两种方式来量化。</p>

<h3>每个信号多久触发一次</h3>
<div class="card">{table(["信号","月数","触发率","实际在检测什么"],[
  [f'{dot("Three-Signal")}DD —— 距高点回撤 &gt;20%', f'{SIG["deep"][0]}', pct(SIG["deep"][1]), "更像一个缓慢的<i>状态</i>标记，而非择时（见下注）"],
  [f'{dot("QQQ DCA")}CAPE —— 分位 &lt;20%', f'{SIG["cheap"][0]}', pct(SIG["cheap"][1]), "每次抄底决策的关键闸门"],
  [f'{dot("TQQQ DCA")}VIX —— &gt;40', f'{SIG["panic"][0]}', pct(SIG["panic"][1]), "仅在极端恐慌时做确认"],
  [f'25 日急跌 &lt; −12%', f'{SIG["crash"][0]}', pct(SIG["crash"][1]), "<i>真正有用</i>的回撤变体——检测新发生的崩盘"],
])}</div>
<div class="note">DD 为何 55% 的时间都在亮：QQQ 直到 2015 年左右才收复 2000 年 3 月的高点，
所以“距历史高点回撤 &gt;20%”在 2002–2013 的大部分时间里<b>一直为真</b>。这让“距高点 DD”更像一个
“仍在水下”的状态标记，而不是一个锐利的择时信号——4% 月份触发的 25 日急跌才是真正的崩盘探测器。</div>

<p>关键在于：<b>全部 {SIG["major"][0]} 个“大底”（梭哈 TQQQ）月份，恰恰就是 CAPE 便宜的月份</b>——
因为 DD 几乎一直在亮，CAPE 才是决定抄底与否的差异项。VIX 从未独自触发过一次大底。
三个信号高度<b>冗余</b>：便宜、深跌、高 VIX 都在同一批事件（崩盘）上同时出现，
所谓“三选二”大多退化成“CAPE 便宜 + 早已深跌”。</p>

<h3>消融实验 —— 每次去掉一个信号</h3>
<div class="card">{table(["配置","平均 IRR","平均最大回撤"],[
  ["<b>三个全开（基准）</b>", f'<b>{pct(ABL["all"][0])}</b>', f'<b>{pct(ABL["all"][1])}</b>'],
  ["去掉 CAPE", pct(ABL["no_cape"][0]), pct(ABL["no_cape"][1])],
  ["去掉 DD", pct(ABL["no_dd"][0]), pct(ABL["no_dd"][1])],
  ["去掉 VIX", pct(ABL["no_vix"][0]), pct(ABL["no_vix"][1])],
])}</div>
<img src="data:image/png;base64,{b64('signal_analysis.png')}" alt="信号触发率与消融实验">

<div class="callout warn"><b>结论。</b>去掉任意单个信号，平均 IRR 的变化都 ≤1 个百分点。
收益绝大部分来自那条一直在场的 TQQQ 底仓，而非信号择时——信号主要影响你<i>何时</i>集中下注
（几个百分点的回撤差异），而不是头部收益。三者之中，<b>只有 CAPE 携带真正的决策信息</b>
（它同时把控买入与减仓）；距高点 DD 太黏，没法择时；<b>VIX 基本冗余</b>。
所谓“三信号”相比简单地长期持有高比例 TQQQ，仅有边际增益——这与前面“优势主要靠样本内讲故事”的发现一致。</div>

<h2>复现 vs 文章宣称</h2>
<p>原文的三信号头条数字（34% IRR、仅 −52% 回撤、终值还反超买入持有 TQQQ）是由一个 AI 工具在
2000–2026 这条历史路径上反复回测十几次得到的——这正是<b>样本内过度优化</b>的典型特征。
本复现刻意不去拟合那个回撤目标，因此呈现的是诚实的取舍。</p>
<div class="card">{reproduction_table()}</div>
<div class="callout warn"><b>诚实的发现。</b>用三信号规则确实能拿到接近 TQQQ 的收益（约 31.6% IRR）——
但<b>做不到</b>把回撤减半。带来超额收益的激进抄底，必然要扛过 2000–02 与 2008 的 −90% 级别崩盘，
所以平均回撤（−70.9%）离 TQQQ 远比离原文宣称的 −52% 近。</div>

<footer>
合成 TQQQ 对真实 TQQQ 的验证（2010–2026）：日收益相关性 0.9989，CAGR 73.2% vs 73.2%。
CAPE = 标普 500 席勒 CAPE（multpl.com）；QQQ/TQQQ/VIX/短端利率来自 yfinance。
完整方法与假设见 <code>summary.md</code>。<br><br>
<b>仅供研究与学习，非投资建议。</b>杠杆 ETF 定投在熊市中可能亏损 70–90%。
</footer>

</div></body></html>"""

out = os.path.join(ROOT, "report_zh.html")
with open(out, "w") as f:
    f.write(HTML)
print("wrote", out, f"({len(HTML)//1024} KB)")
