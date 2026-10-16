# -*- coding: utf-8 -*-
"""Answer questions about the BP/BM app data from the command line — same numbers as the app.

Reads the live config.json from Google Drive (read-only) and runs
app.py's own calculation helpers (extracted by tests/smoke_test.py), so nothing is re-implemented
here and nothing is written anywhere.

    python bp_ask.py summary [2026Q3] [--buyer EcoPro] [--product BP]
    python bp_ask.py todo
    python bp_ask.py ar [--buyer POSCO]
    python bp_ask.py ship TGLHUS26090002
    python bp_ask.py ships [--buyer EcoPro] [--status provisional]
    python bp_ask.py pnl [--by month|quarter|buyer|hbl|processor|scrap] [--year 2026] [--buyer ...] [--product ...]
    python bp_ask.py stock
"""
import argparse, contextlib, io, json, os, sys, warnings
from collections import defaultdict

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "tests"))
import logging; logging.disable(logging.CRITICAL)
import regression_live as R     # load_live() + app helpers in R.F

F = R.F


# ── formatting ──────────────────────────────────────────────────────────────
def usd(v):
    return "—" if v is None else f"${v:,.0f}"

def pct(v):
    return "—" if v is None else f"{v:.1f}%"

def table(rows, cols):
    """Plain-text table: rows = list of dicts, cols = [(header, key or fn)]."""
    if not rows:
        print("  (없음)"); return
    cells = [[str(c(r) if callable(c) else r.get(c, "")) for _, c in cols] for r in rows]
    heads = [h for h, _ in cols]
    w = [max(len(h), *(len(x[i]) for x in cells)) for i, h in enumerate(heads)]
    print("  " + " | ".join(h.ljust(w[i]) for i, h in enumerate(heads)))
    print("  " + "-+-".join("-" * x for x in w))
    for x in cells:
        print("  " + " | ".join(v.rjust(w[i]) if v[:1] in "$-0123456789" else v.ljust(w[i]) for i, v in enumerate(x)))


# ── lookups ─────────────────────────────────────────────────────────────────
def find_buyer(cfg, text):
    """Buyer id from a loose name ('ecopro', 'posco bm'); None when text is empty."""
    if not text:
        return None
    t = text.lower().replace(" ", "")
    hits = [b for b in cfg["buyers"] if t in f"{b['name']}{b.get('product','')}".lower().replace(" ", "")]
    if len(hits) != 1:
        names = ", ".join(f"{b['name']} ({b.get('product')})" for b in (hits or cfg["buyers"]))
        sys.exit(f"매입사 '{text}'를 하나로 특정할 수 없습니다. 후보: {names}")
    return hits[0]["id"]

def norm_q(q):
    """'2026q3' / '2026 Q3' → '2026 Q3'."""
    q = q.upper().replace(" ", "")
    return f"{q[:4]} {q[4:]}"


# ── commands ────────────────────────────────────────────────────────────────
def cmd_summary(cfg, a):
    rows = F["_batch_pnl_rows"](cfg, F["_pnl_context"](cfg))
    f_rows, f_ships = F["_filtered_pnl"](cfg, find_buyer(cfg, a.buyer), a.product, rows=rows)
    qs = sorted({F["_qtr"](s["loading_date"]) for s in f_ships})
    q = norm_q(a.quarter) if a.quarter else (max(x for x in qs if x <= F["_qtr"](F["_today"]().isoformat())) if qs else None)
    if not q:
        print("선적 실적이 없습니다."); return
    cur, prev = F["_quarter_stats"](f_rows, f_ships, q), F["_quarter_stats"](f_rows, f_ships, F["_qtr_prev"](q))
    def chg(k):
        return "—" if not prev[k] or cur[k] is None else f"{(cur[k] - prev[k]) / abs(prev[k]) * 100:+.1f}%"
    price = "—" if cur["price"] is None else f"${cur['price']:.2f}/kg"
    print(f"[{q} 요약 · 직전 {F['_qtr_prev'](q)} 대비]" + (f" 매입사={a.buyer}" if a.buyer else "") + (f" 제품={a.product}" if a.product else ""))
    print(f"  매출 {usd(cur['rev'])} ({chg('rev')}) · 선적 {cur['cnt']}건 ({chg('cnt')}) · "
          f"평균 단가 {price} ({chg('price')}) · 판매 {cur['out']/1000:,.1f} MT ({chg('out')})")
    mg_d = "—" if cur["margin"] is None or prev["margin"] is None else f"{cur['margin'] - prev['margin']:+.1f}%p"
    print(f"  실질 손익 {usd(cur['real'])} · 실질 마진율 {pct(cur['margin'])} ({mg_d}) — 판관비 제외")
    if cur["nobatch"]:
        print(f"  주의: 배치 없는 선적 {len(cur['nobatch'])}건은 매출에 빠짐: " + ", ".join(s.get("hbl") or "—" for s in cur["nobatch"]))
    for title, key, val, fmt in (("매입사별 매출", "buyer_lbl", "bp", usd), ("스크랩 유형별 매출", "sc_nm", "bp", usd),
                                 ("임가공사별 생산", "proc_nm", "out", lambda v: f"{v/1000:,.1f} MT")):
        agg = F["_pnl_agg"](cur["rows"], lambda x, k=key: x[k])
        tot = sum(v[val] for v in agg.values()) or 1
        print(f"\n  {title}")
        table(sorted(({"k": k, "v": v[val]} for k, v in agg.items()), key=lambda r: -r["v"]),
              [("구분", "k"), ("값", lambda r: fmt(r["v"])), ("비중", lambda r: f"{r['v']/tot*100:.0f}%")])
    st = defaultdict(int)
    for s in cur["ships"]:
        st[{"provisional": "가정산", "final": "확정산", "paid": "입금완료"}.get(s.get("status"), s.get("status"))] += 1
    print("\n  정산 상태: " + ", ".join(f"{k} {v}건" for k, v in st.items()))

def cmd_todo(cfg, a):
    items = F["_todo_items"](cfg)
    print(f"[할 일 {len(items)}개]")
    for dot, title, detail, loc in items:
        print(f"  - {title}: {detail}  (처리: {loc})")

def cmd_ar(cfg, a):
    rows = F["_receivable_rows"](cfg, F["_latest_index"](cfg))
    if a.buyer:   # rows carry the buyer name only (BP/BM together), so match on the name
        rows = [r for r in rows if a.buyer.lower().replace(" ", "") in r["매입사"].lower().replace(" ", "")]
    now = sum(r["확정산 잔액"] for r in rows if r["구분"] == "청구 가능")
    wait = sum(r["확정산 잔액"] for r in rows if r["구분"] != "청구 가능")
    print(f"[미수 확정산 잔액] 합계 {usd(now + wait)} = 청구 가능 {usd(now)} + INDEX 대기(추정) {usd(wait)}")
    table(sorted(rows, key=lambda r: r["예상 입금일"]),
          [("HBL", "HBL"), ("매입사", "매입사"), ("상태", "상태"), ("Final월", "Final월"), ("기준", "기준"),
           ("확정산 잔액", lambda r: usd(r["확정산 잔액"])), ("예상 입금일", "예상 입금일"), ("구분", "구분")])

def _ship_by_hbl(cfg, hbl):
    exact = [s for s in cfg["shipments"] if (s.get("hbl") or "").strip().upper() == hbl.strip().upper()]
    hits = exact or [s for s in cfg["shipments"] if hbl.upper() in (s.get("hbl") or "").upper()]
    if len(hits) != 1:
        sys.exit(f"HBL '{hbl}' 일치 {len(hits)}건: " + ", ".join(s.get("hbl") or "—" for s in hits[:10]))
    return hits[0]

def cmd_ship(cfg, a):
    s = _ship_by_hbl(cfg, a.hbl)
    b = next((x for x in cfg["buyers"] if x["id"] == s.get("buyer_id")), {})
    calc = F["_recompute_final_settlement"](cfg, s)
    print(f"[{s.get('hbl')}] {b.get('name')} ({b.get('product')}) · 상태 {s.get('status')} · 선적 {s.get('loading_date')} · ETA {s.get('eta') or '—'}")
    print(f"  중량 {float(s.get('weight_kg') or 0):,.0f} kg · Invoice {usd(float(s.get('invoice_usd') or 0))} · "
          f"Prov월 {s.get('prov_month')} · Final월 {s.get('final_month')}")
    print(f"  확정액(저장) {usd(s.get('final_amount_usd'))} · 확정산 계산값 {usd(calc)} · 기타 조정 {usd(float(s.get('other_adj_usd') or 0))}")
    print(f"  가정산 입금 {s.get('prov_paid_date') or '—'} {usd(s.get('prov_paid_usd'))} · "
          f"확정산 입금 {s.get('final_paid_date') or '—'} {usd(s.get('final_paid_usd'))} · 수출비 {usd(s.get('export_cost_usd'))}")
    mm = F["_inv_mismatch"](cfg, s)
    if mm:
        print(f"  Invoice 점검: {F['_inv_hint_text'](cfg, s)}")
    rows = [x for x in F["_batch_pnl_rows"](cfg, F["_pnl_context"](cfg)) if x["sid"] == s["id"]]
    print("\n  배치 손익")
    table(rows, [("임가공사", "proc_nm"), ("스크랩", "sc_nm"), ("투입kg", lambda x: f"{x['inp']:,.0f}"),
                 ("생산kg", lambda x: f"{x['out']:,.0f}"), ("매출", lambda x: usd(x["bp"])), ("원료비", lambda x: usd(x["raw"])),
                 ("임가공비", lambda x: usd(x["pf"])), ("수출비", lambda x: usd(x["eu"])), ("보관비", lambda x: usd(x["stor"])),
                 ("실질손익", lambda x: usd(x["bp"] - x["raw"] - x["pf"] - x["eu"] - x["stor"]))])

def cmd_ships(cfg, a):
    bid = find_buyer(cfg, a.buyer)
    bm = {b["id"]: b for b in cfg["buyers"]}
    rows = [s for s in cfg["shipments"] if (not bid or s.get("buyer_id") == bid) and (not a.status or s.get("status") == a.status)]
    table(sorted(rows, key=lambda s: s.get("loading_date") or ""),
          [("HBL", "hbl"), ("선적일", "loading_date"), ("매입사", lambda s: f"{bm.get(s.get('buyer_id'),{}).get('name')} ({bm.get(s.get('buyer_id'),{}).get('product')})"),
           ("중량kg", lambda s: f"{float(s.get('weight_kg') or 0):,.0f}"), ("Invoice", lambda s: usd(float(s.get("invoice_usd") or 0))),
           ("확정액", lambda s: usd(s.get("final_amount_usd"))), ("상태", "status"), ("Final월", "final_month")])

def cmd_pnl(cfg, a):
    rows = F["_batch_pnl_rows"](cfg, F["_pnl_context"](cfg))
    f_rows, _ = F["_filtered_pnl"](cfg, find_buyer(cfg, a.buyer), a.product, rows=rows)
    if a.year:
        f_rows = [x for x in f_rows if x["month"][:4] == str(a.year)]
    key = {"month": lambda x: x["month"], "quarter": lambda x: F["_qtr"](x["month"]), "buyer": lambda x: x["buyer_lbl"],
           "hbl": lambda x: x["hbl"], "processor": lambda x: x["proc_nm"], "scrap": lambda x: x["sc_nm"]}[a.by]
    agg = F["_pnl_agg"](f_rows, key)
    out = []
    for k, v in sorted(agg.items()):
        real = v["bp"] - v["raw"] - v["pf"] - v["eu"] - v["stor"]
        out.append({"k": k, **v, "real": real, "mg": real / v["bp"] * 100 if v["bp"] else None})
    tot = {c: sum(r[c] for r in out) for c in ("bp", "raw", "pf", "eu", "stor", "out", "real")}
    out.append({"k": "합계", **tot, "mg": tot["real"] / tot["bp"] * 100 if tot["bp"] else None})
    print(f"[손익 · {a.by}별] 판관비 제외, 원료비 FIFO 우선 — 손익 탭과 같은 엔진")
    table(out, [(a.by, "k"), ("생산MT", lambda r: f"{r['out']/1000:,.1f}"), ("매출", lambda r: usd(r["bp"])),
                ("원료비", lambda r: usd(r["raw"])), ("임가공비", lambda r: usd(r["pf"])), ("수출비", lambda r: usd(r["eu"])),
                ("보관비", lambda r: usd(r["stor"])), ("실질손익", lambda r: usd(r["real"])), ("마진율", lambda r: pct(r["mg"]))])

def cmd_stock(cfg, a):
    print("[재고 추정]")
    rows = []
    for sc in cfg["scrap_types"]:
        _, _, rem = F["_fifo_lot_trace"](cfg, sc["id"])
        rows.append({"스크랩": sc["name"], "제품": F["_sc_product"](sc),
                     "창고 원료": sum(l.get("remain", 0) for l in rem),
                     "임가공사 보유 원료": F["_at_processor_raw_kg"](cfg, sc["id"]),
                     "완제품": F["_finished_goods_kg"](cfg, sc["id"])})
    kg = lambda k: (lambda r: f"{r[k]:,.0f}")
    table(rows, [("스크랩", "스크랩"), ("제품", "제품"), ("창고 원료kg", kg("창고 원료")),
                 ("임가공사 보유kg", kg("임가공사 보유 원료")), ("완제품kg", kg("완제품"))])
    print("\n[생산·재고 대사] (임가공사 생산 보고 기준)")
    table(F["_production_recon"](cfg), [("임가공사", "임가공사"), ("스크랩", "스크랩"), ("기준월", "자료 기준월"),
          ("입고", lambda r: f"{r['임가공사 입고']:,}"), ("투입", lambda r: f"{r['투입']:,}"), ("생산", lambda r: f"{r['생산']:,}"),
          ("회수율", lambda r: pct(r["회수율(%)"])), ("선적", lambda r: f"{r['선적(배치)']:,}"),
          ("완제품 재고", lambda r: f"{r['완제품 재고(생산−선적)']:,}")])


def build_parser():
    p = argparse.ArgumentParser(prog="bp_ask", description="BP/BM 앱 데이터 질의 (읽기 전용)", exit_on_error=False)
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("summary"); s.add_argument("quarter", nargs="?"); s.add_argument("--buyer"); s.add_argument("--product", choices=["BP", "BM"])
    sp.add_parser("todo")
    s = sp.add_parser("ar"); s.add_argument("--buyer")
    s = sp.add_parser("ship"); s.add_argument("hbl")
    s = sp.add_parser("ships"); s.add_argument("--buyer"); s.add_argument("--status", choices=["provisional", "final", "paid"])
    s = sp.add_parser("pnl"); s.add_argument("--by", default="month", choices=["month", "quarter", "buyer", "hbl", "processor", "scrap"])
    s.add_argument("--year", type=int); s.add_argument("--buyer"); s.add_argument("--product", choices=["BP", "BM"])
    sp.add_parser("stock")
    return p


def load_cfg():
    """Live config.json from Drive, read-only. Local: the service-account key file next to app.py.
    Cloud Run: the service account attached to the service (Application Default Credentials)."""
    if os.path.exists(R.CREDS):
        return R.load_live()
    import google.auth
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/drive.readonly"])
    svc = build("drive", "v3", credentials=creds, cache_discovery=False)
    fid = os.environ.get("DRIVE_CONFIG_FILE_ID") or svc.files().list(
        q="name='config.json' and trashed=false", fields="files(id)").execute()["files"][0]["id"]
    buf = io.BytesIO(); dl = MediaIoBaseDownload(buf, svc.files().get_media(fileId=fid)); done = False
    while not done:
        _, done = dl.next_chunk()
    return json.loads(buf.getvalue().decode("utf-8"))


def ask(argv, cfg):
    """Run one query (argv like ["ar", "--buyer", "posco"]) on cfg and return the printed answer as text."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        try:
            a = build_parser().parse_args(argv)
            m = cfg.get("_meta") or {}
            print(f"(데이터: Drive config rev {m.get('rev')} · 저장 {m.get('saved_at')})")
            print()
            globals()["cmd_" + a.cmd](cfg, a)
        except SystemExit as e:          # lookup failures exit with a message (sys.exit("..."))
            if e.code not in (None, 0):
                print(e.code)
        except argparse.ArgumentError as e:
            print(f"입력 오류: {e}")
    return out.getvalue()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    argv = sys.argv[1:]
    try:
        build_parser().parse_args(argv)          # show usage errors before downloading
    except argparse.ArgumentError as e:
        sys.exit(f"입력 오류: {e}")
    print(ask(argv, load_cfg()), end="")


if __name__ == "__main__":
    main()
