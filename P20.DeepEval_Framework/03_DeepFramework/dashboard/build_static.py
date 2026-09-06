"""Bake a read-only snapshot of the dashboard into dashboard-static/.

The live dashboard needs the chatbot (:8201), the RAG Explorer (:8202), a Groq
key and long-running threads — none of which survive a static host. This emits
a self-contained page: the 25 metric cards + whatever is in results.json, with
the Run controls replaced by a "Recorded" badge. Category tabs and the target
filter still work (client-side).

    python -m dashboard.build_static
    cd dashboard-static && vercel deploy         # or import the repo on vercel.com
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from metrics_catalog import ALL_SPECS, CATEGORIES

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dashboard-static"
RESULTS = Path(__file__).resolve().parent / "results.json"
JUDGE = "openai/gpt-oss-120b"
REPO = "https://github.com/sanjeev1xy/AI_Learning-With_Testing_Tools"


def _load_runs() -> dict:
    if RESULTS.exists():
        try:
            return json.loads(RESULTS.read_text(encoding="utf-8")).get("runs", {})
        except Exception:
            return {}
    return {}


def _latest(runs: dict, spec):
    rec = None
    for t in spec.targets:
        rec = runs.get(f"{t}:{spec.key}") or rec
    return rec


def _esc(s) -> str:
    return html.escape(str(s), quote=True)


_TOK = re.compile(r"\S+")


def _approx_tokens(text: str) -> int:
    # rough: ~1.3 tokens/word, good enough for a "≈" figure on a card
    return int(len(_TOK.findall(text or "")) * 1.3)


def _hint(spec) -> str:
    return {
        "answer_relevancy": "1.00 = every sentence answers the question",
        "faithfulness": "1.00 = every claim backed by the context",
        "hallucination": "1.00 = nothing contradicts ground truth",
        "bias": "1.00 = no bias detected in the reply",
        "toxicity": "1.00 = no insults or mockery",
        "pii_leakage": "1.00 = no personal data or prompt leaked",
        "no_prompt_leak": "1.00 = system prompt held back",
        "correctness": "1.00 = figures match the reference",
        "rag_citation": "1.00 = every claim cites a retrieved source",
        "rag_summarization": "1.00 = condensed, nothing invented",
        "rag_helpfulness": "1.00 = complete, direct, actionable",
        "rag_safety": "1.00 = neutral, in-domain, no advice",
        "contextual_precision": "1.00 = useful chunks ranked first",
        "contextual_recall": "1.00 = retrieval got everything needed",
        "contextual_relevancy": "1.00 = retrieved chunks all on-topic",
        "role_violation": "1.00 = stayed in character as ShopBot",
        "misuse": "1.00 = declined the out-of-domain ask",
        "non_advice": "1.00 = no medical/financial/legal advice",
        "conversation_completeness": "1.00 = intent met across all turns",
        "knowledge_retention": "1.00 = remembered earlier facts",
    }.get(spec.key, f"threshold {spec.threshold:.2f}")


def build() -> Path:
    runs = _load_runs()
    OUT.mkdir(exist_ok=True)

    counts = {"pass": 0, "fail": 0, "error": 0, "pending": 0}
    tgt_tok = judge_tok = calls = 0
    last_ts = 0.0

    for s in ALL_SPECS:
        rec = _latest(runs, s)
        v = (rec or {}).get("verdict")
        if (rec or {}).get("status") == "error" and not v:
            v = "error"
        counts["pass" if v == "pass" else "fail" if v == "fail"
               else "error" if v == "error" else "pending"] += 1
        for c in (rec or {}).get("cases", []):
            calls += 1
            tgt_tok += _approx_tokens(c.get("input", "")) + _approx_tokens(c.get("reply", ""))
            judge_tok += _approx_tokens(c.get("reason", "")) + 350  # rubric + verdict overhead
        if rec and rec.get("finished_at"):
            last_ts = max(last_ts, rec["finished_at"])

    ran = sum(1 for s in ALL_SPECS if _latest(runs, s))
    run_date = (datetime.fromtimestamp(last_ts, timezone.utc).strftime("%Y-%m-%d")
                if last_ts else "—")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    cards = []
    for s in ALL_SPECS:
        rec = _latest(runs, s)
        v = (rec or {}).get("verdict")
        if (rec or {}).get("status") == "error" and not v:
            v = "error"
        vlabel = v or "recorded" if rec else "not run"
        vcls = v or ""
        score = (rec or {}).get("avg_score")
        score_html = (f'<span class="score">{score:.3f}</span>'
                      f'<span class="thr">&ge;<br>{s.threshold:.2f}</span>'
                      if isinstance(score, (int, float)) else
                      f'<span class="thr">&ge; {s.threshold:.2f}</span>')
        first_reason = ""
        for c in (rec or {}).get("cases", []):
            if c.get("reason") or c.get("error"):
                first_reason = c.get("reason") or c.get("error")
                break
        cases_html = ""
        if rec and rec.get("cases"):
            rows = []
            for c in rec["cases"]:
                k = "error" if c.get("error") else ("pass" if c.get("passed") else "fail")
                sc = (f' · <b>{c["score"]:.2f}</b>'
                      if isinstance(c.get("score"), (int, float)) else "")
                why = c.get("error") or c.get("reason") or ""
                rows.append(
                    f'<div class="caserow {k}"><div class="q">{_esc(c.get("input",""))}{sc}</div>'
                    + (f'<div class="r">{_esc(c.get("reply","")[:220])}</div>' if c.get("reply") else "")
                    + (f'<div class="why">{_esc(why[:300])}</div>' if why else "")
                    + "</div>"
                )
            cases_html = (f'<details class="details"><summary>Details · '
                          f'{rec.get("passed",0)}/{len(rec["cases"])} pass</summary>'
                          f'{"".join(rows)}</details>')
        chips = (f'<span class="chip cat-{s.category}">{s.category}</span>'
                 + "".join(f'<span class="chip tgt">{t}</span>' for t in s.targets))
        cards.append(f"""
      <article class="mcard" data-cat="{s.category}" data-targets="{','.join(s.targets)}">
        <div class="chips">{chips}<span class="thr-top">&ge; {s.threshold:.2f}</span></div>
        <h3>{_esc(s.title)}</h3>
        <p class="desc">{_esc(s.blurb)}</p>
        <div class="box">
          <div class="verline"><span class="verdict {vcls}">{vlabel}</span>{score_html}</div>
          <div class="hint">{_esc(_hint(s))}</div>
          {f'<p class="reason">{_esc(first_reason[:280])}</p>' if first_reason else
           f'<p class="reason muted">{s.case_count()} cases · {_esc(s.test_file)}</p>'}
          {cases_html}
        </div>
      </article>""")

    tabs = ('<button class="tab on" data-cat="all">All</button>'
            + "".join(f'<button class="tab" data-cat="{c}">{c.title()}</button>'
                      for c in CATEGORIES))

    page = _TEMPLATE.format(
        tabs=tabs, cards="".join(cards), judge=JUDGE, stamp=stamp, repo=REPO,
        run_date=run_date, ran=ran, total=len(ALL_SPECS),
        cpass=counts["pass"], cfail=counts["fail"], cerr=counts["error"],
        tgt_tok=f"{tgt_tok:,}", judge_tok=f"{judge_tok:,}",
        tot_tok=f"{tgt_tok + judge_tok:,}", calls=calls,
    )
    (OUT / "index.html").write_text(page, encoding="utf-8")
    (OUT / "vercel.json").write_text(
        json.dumps({"cleanUrls": True, "trailingSlash": False,
                    "framework": None, "buildCommand": None, "outputDirectory": "."},
                   indent=2), encoding="utf-8")
    print(f"wrote {OUT/'index.html'}  ({ran}/{len(ALL_SPECS)} metrics recorded, "
          f"{counts['pass']} pass / {counts['fail']} fail / {counts['error']} err)")
    return OUT / "index.html"


_TEMPLATE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>DeepEval Dashboard — snapshot</title>
<style>
  :root{{--bg:#f4f3ef;--panel:#fbfaf8;--card:#fff;--ink:#20242c;--muted:#6d7480;
    --line:#e7e4dd;--accent:#d05a33;--pass:#1c8a4e;--pass-bg:#e4f4ec;--fail:#c0392b;
    --fail-bg:#fbe9e7;--pend:#9aa0a6;--pend-bg:#eceae5;--head:#22252c;--warn-bg:#f7efd9;--warn-ink:#7a5c12}}
  @media (prefers-color-scheme:dark){{:root{{--bg:#181a1f;--panel:#1f2228;--card:#22262d;
    --ink:#e9e9ec;--muted:#9aa0aa;--line:#33373f;--pass-bg:#12331f;--fail-bg:#3a1c17;
    --pend-bg:#2a2d33;--head:#14161a;--warn-bg:#2b2410;--warn-ink:#d7b877}}}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--ink);
    font:14px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
  a{{color:var(--accent)}}
  header{{background:var(--head);color:#f4f3ef;padding:16px 24px;display:flex;
    align-items:center;gap:14px;flex-wrap:wrap}}
  header .logo{{width:34px;height:34px;border-radius:9px;background:var(--accent);
    display:flex;align-items:center;justify-content:center}}
  header .logo i{{width:12px;height:12px;background:#fff;border-radius:2px;transform:rotate(45deg)}}
  header h1{{font-size:18px;margin:0}} header .tag{{font-size:12px;color:#b9bcc4}}
  header .ctl{{margin-left:auto;display:flex;gap:14px;align-items:flex-end}}
  header .ctl label{{font-size:9px;letter-spacing:.09em;text-transform:uppercase;color:#9aa0a6;display:block;margin-bottom:3px}}
  header select,header input{{background:#2d313a;color:#f4f3ef;border:1px solid #3c414c;
    border-radius:7px;padding:6px 9px;font-size:13px}}
  main{{max-width:1220px;margin:0 auto;padding:20px 24px 70px}}
  .banner{{background:var(--warn-bg);color:var(--warn-ink);border:1px solid var(--line);
    border-radius:11px;padding:13px 16px;margin-bottom:16px;font-size:13px}}
  .banner b{{display:block;margin-bottom:3px;font-size:13.5px}}
  .statusbar{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px}}
  .scard{{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:12px 15px;min-width:150px}}
  .scard .k{{font-size:12px;color:var(--muted);display:flex;align-items:center;gap:6px}}
  .scard .v{{font-size:12.5px;margin-top:3px;font-family:ui-monospace,Menlo,monospace}}
  .scard .dot{{width:8px;height:8px;border-radius:50%;background:var(--pass)}}
  .counts{{display:flex;align-items:center;gap:7px;margin-left:auto}}
  .counts .lbl{{font-size:12px;color:var(--muted)}}
  .pill{{padding:4px 12px;border-radius:999px;font-size:14px;font-weight:700;font-variant-numeric:tabular-nums}}
  .pill.p{{background:var(--pass-bg);color:var(--pass)}}
  .pill.f{{background:var(--fail-bg);color:var(--fail)}}
  .pill.n{{background:var(--pend-bg);color:#8b9099}}
  .tabs{{display:flex;gap:7px;flex-wrap:wrap;margin:4px 0 18px;align-items:center}}
  .tabs .cl{{font-size:12px;color:var(--muted);margin-right:4px}}
  .tab{{background:var(--card);border:1px solid var(--line);border-radius:999px;
    padding:5px 14px;font-size:12.5px;cursor:pointer;color:var(--ink)}}
  .tab.on{{background:var(--accent);color:#fff;border-color:var(--accent)}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:13px}}
  .mcard{{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:15px 16px}}
  .chips{{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-bottom:9px}}
  .chip{{font-size:9.5px;letter-spacing:.05em;text-transform:uppercase;padding:2px 7px;
    border-radius:5px;background:var(--pend-bg);color:var(--muted);font-weight:700}}
  .chip.cat-quality{{background:#e5eef8;color:#2f6bb0}}
  .chip.cat-retrieval{{background:#e7f1ec;color:#2f855a}}
  .chip.cat-safety{{background:#fdeee6;color:#c0632b}}
  .chip.cat-geval{{background:#f0e9f6;color:#7a4bb0}}
  .chip.cat-conversational{{background:#e9eef0;color:#4a6b78}}
  .thr-top{{margin-left:auto;font-size:11px;color:var(--muted)}}
  .mcard h3{{margin:0 0 4px;font-size:16px}}
  .desc{{font-size:12.5px;color:var(--muted);margin:0 0 10px;min-height:34px}}
  .box{{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:11px 13px}}
  .verline{{display:flex;align-items:center;gap:9px;flex-wrap:wrap}}
  .verdict{{font-size:10px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;
    padding:3px 8px;border-radius:5px;background:var(--pend-bg);color:var(--muted)}}
  .verdict.pass{{background:var(--pass-bg);color:var(--pass)}}
  .verdict.fail{{background:var(--fail-bg);color:var(--fail)}}
  .verdict.error{{background:var(--warn-bg);color:var(--warn-ink)}}
  .score{{font-size:22px;font-weight:800;font-variant-numeric:tabular-nums}}
  .verline .thr{{font-size:10px;color:var(--muted);line-height:1.1}}
  .hint{{font-size:11.5px;font-style:italic;color:var(--muted);margin-top:6px}}
  .reason{{font-size:12px;margin:7px 0 0}} .reason.muted{{color:var(--muted);font-family:ui-monospace,Menlo,monospace;font-size:10.5px;word-break:break-all}}
  .details{{margin-top:9px}}
  .details summary{{cursor:pointer;font-size:12px;color:var(--accent);font-weight:600}}
  .caserow{{font-size:11.5px;border-left:3px solid var(--line);padding:3px 0 3px 8px;margin-top:7px}}
  .caserow.pass{{border-color:var(--pass)}} .caserow.fail{{border-color:var(--fail)}}
  .caserow.error{{border-color:#c9a227}}
  .caserow .q{{font-weight:600}} .caserow .r{{color:var(--muted);white-space:pre-wrap}}
  .caserow .why{{color:var(--muted);margin-top:2px}}
  footer{{max-width:1220px;margin:0 auto;padding:0 24px 44px;color:var(--muted);font-size:12px;text-align:center}}
</style></head><body>
<header>
  <div class="logo"><i></i></div>
  <div><h1>DeepEval Dashboard</h1>
    <div class="tag">Recorded run · chatbot and RAG pipeline graded by a judge model</div></div>
  <div class="ctl">
    <div><label>Target</label>
      <select id="target">
        <option value="all">All targets</option>
        <option value="chatbot">Chatbot (A)</option>
        <option value="rag">RAG Explorer (B)</option>
      </select></div>
    <div><label>Judge model</label>
      <input id="judge" type="text" value="{judge}" readonly style="width:165px"></div>
  </div>
</header>
<main>
  <div class="banner">
    <b>This is a recorded run, not a live one.</b>
    Every score, reason and case below came from one real execution on <b>{run_date}</b>
    against a running chatbot and RAG pipeline, judged by <code>{judge}</code>.
    A static page cannot call a model, so the Run buttons are gone — everything
    else, including the per-case Details, is the real output.
    <a href="./how-it-works.html">Read how the framework works</a> ·
    <a href="{repo}">clone the repo</a> to run it live.
  </div>

  <div class="statusbar">
    <div class="scard"><div class="k"><span class="dot"></span> Chatbot</div>
      <div class="v">subsystem A · qwen/qwen3.8-27b</div></div>
    <div class="scard"><div class="k"><span class="dot"></span> RAG</div>
      <div class="v">subsystem B · ONNX MiniLM + Chroma</div></div>
    <div class="scard"><div class="k"><span class="dot"></span> Judge</div>
      <div class="v">groq · {judge}</div></div>
    <div class="scard"><div class="k"><span class="dot"></span> Tokens (approx)</div>
      <div class="v">{tot_tok} total · {calls} judge calls<br>target {tgt_tok} · judge {judge_tok}</div></div>
    <div class="scard counts">
      <span class="lbl">pass · fail · error</span>
      <span class="pill p">{cpass}</span><span class="pill f">{cfail}</span><span class="pill n">{cerr}</span>
    </div>
  </div>

  <div class="tabs" id="tabs"><span class="cl">Categories:</span>{tabs}</div>
  <div class="grid" id="grid">{cards}</div>
</main>
<footer>{ran}/{total} metrics recorded · snapshot {stamp} · judge &ne; target on purpose ·
  <a href="{repo}">P20.DeepEval_Framework / 03_DeepFramework</a></footer>
<script>
  var tabs = document.getElementById('tabs'), target = document.getElementById('target');
  function apply(){{
    var cat = (document.querySelector('.tab.on')||{{}}).dataset.cat || 'all';
    var tg = target.value;
    document.querySelectorAll('.mcard').forEach(function(c){{
      var okCat = cat === 'all' || c.dataset.cat === cat;
      var okTg = tg === 'all' || c.dataset.targets.split(',').indexOf(tg) > -1;
      c.style.display = (okCat && okTg) ? '' : 'none';
    }});
  }}
  tabs.addEventListener('click', function(e){{
    if(!e.target.classList.contains('tab')) return;
    document.querySelectorAll('.tab').forEach(function(t){{t.classList.toggle('on', t===e.target);}});
    apply();
  }});
  target.addEventListener('change', apply);
</script>
</body></html>"""


if __name__ == "__main__":
    build()
