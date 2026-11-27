"""Mail attachments -> bp_calculator_sync sheet. Dry run by default; --write applies the in/out and production rows.

    py -V:3.12 tools\\ingest.py all              # dry run of all four kinds (nothing written)
    py -V:3.12 tools\\ingest.py inout --write    # append new purchase / dispatch rows to 입고 / 출고
    py -V:3.12 tools\\ingest.py tolling --write  # overwrite 생산 rows (month, Sungeel, scrap) from the tolling file
    py -V:3.12 tools\\ingest.py tgl              # report: TGL report vs 선적 tab (HBL for TBD keys, ETD/ETA) — never writes
    py -V:3.12 tools\\ingest.py szamla           # report: HBLs with a TGL szamla mail but no export cost in 선적 — never writes

Rules follow the agreed manual procedures (memory: inout-mail-to-sheet, sungeel-production-update,
export-shipment-mail-to-sheet):
- 입출고: only CF (양극) and JR (젤리롤) sheets; a source row is new when neither (scrap, date, kg) nor its SZ Form /
  document number is already in the tab; rows dated before the tab's first row are ignored (opening stock covers them),
  ledger adjustment rows ('+') are not purchases.
  Purchase price: tools/prices.json (prices the user gives each month) -> the tab's price for the same scrap, origin and
  month -> the latest earlier price marked "임시 단가" (an empty price would make the raw-material cost 0).
  Dispatch type/processor are learned from rows already in the tab (same 출고처); unknown 출고처 are reported, not written.
- 생산: totals row after '합계(月 기준)' of each '양극 극판 26년 N월' / 'Dry JR 26년 N월' sheet, cross-checked with the sum of
  daily Output rows (weekly '소   계' rows excluded). Rows whose note was written by hand (not "성일 생산내역 …", or
  mentioning "상세 합계") are protected and only reported.
- TGL / szamla: report only (HBL key changes touch three tabs and MSC dates win over TGL — the user decides).
"""
import argparse, io, json, os, re, sys
from collections import defaultdict
from datetime import datetime, date
import openpyxl, gspread

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import mail_ingest as MI

SA_FILE = os.path.join(os.path.dirname(_HERE), "bp-calculator-498206-4308cbd64cba.json")
SHEET = "bp_calculator_sync"
SCRAP = {"CF": "양극", "JR": "젤리롤"}
_PRICES_FILE = os.path.join(_HERE, "prices.json")
PRICES = ({k: v for k, v in json.load(open(_PRICES_FILE, encoding="utf-8")).items() if not k.startswith("_")}
          if os.path.exists(_PRICES_FILE) else {})


# ── helpers ────────────────────────────────────────────────────────────────
def _num(v):
    if v in (None, ""):
        return None
    try:
        return float(str(v).replace(",", "").strip())
    except ValueError:
        return None

def _day(v):
    if isinstance(v, datetime):
        return v.date().isoformat()
    if isinstance(v, date):
        return v.isoformat()
    s = str(v or "").strip()
    m = re.match(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", s)
    return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}" if m else ""

def _norm_doc(s):
    """'HEL-SZ 966239' / 'HEL-SZ-966239' / 'hel sz966239' -> 'HELSZ966239' for matching."""
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())

def _table(ws, key):
    """(header list, data rows) of a sheet whose header row contains `key` (title rows above are skipped)."""
    rows = list(ws.iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows) if any(isinstance(v, str) and key in v for v in r))
    hdr = [re.sub(r"\s+", " ", str(v)).strip() if v is not None else "" for v in rows[hi]]
    return hdr, [r for r in rows[hi + 1:] if any(v not in (None, "") for v in r)]

def _col(hdr, *names):
    for n in names:
        for i, h in enumerate(hdr):
            if h == n or (n.endswith("*") and h.startswith(n[:-1])):
                return i
    raise KeyError(f"열 없음: {names} in {hdr}")

def _latest_mail(m, kind, days=45):
    rx = MI.KINDS[kind]
    for uid, d, frm, subj, _ in MI.recent(m, days):
        if rx.search(subj) and not re.match(r"\s*(re|fw|fwd)\s*:", subj, re.I):
            return uid, d, frm, subj
    return None

def _xlsx(m, uid):
    for fn, blob in MI.attachments(m, uid):
        if fn.lower().endswith((".xlsx", ".xlsm")):
            return fn, openpyxl.load_workbook(io.BytesIO(blob), read_only=True, data_only=True)
    return None, None

def _sheet():
    return gspread.service_account(filename=SA_FILE).open(SHEET)


# ── 입출고 ──────────────────────────────────────────────────────────────────
def parse_inout(wb):
    """{'in': [...], 'out': [...], 'incomplete': [...]} from the logistics workbook (CF/JR only)."""
    res = {"in": [], "out": [], "incomplete": []}
    for code, scrap in SCRAP.items():
        hdr, rows = _table(wb[f"{code} 입고"], "하역일")
        c_org, c_kg, c_tb, c_sz, c_day = (_col(hdr, "출발지"), _col(hdr, "SK 기준 중량 (kg)", "중량(kg) SK기준", "중량*"),
                                          _col(hdr, "Ton Bag", "Pallets"), _col(hdr, "SZ Form No."), _col(hdr, "하역일"))
        for r in rows:
            d, kg = _day(r[c_day]), _num(r[c_kg])
            if not d or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]+", str(r[c_org] or "").strip()):
                continue      # ledger adjustment ('+') and year-separator rows are not purchases
            item = {"scrap": scrap, "date": d, "kg": kg, "bags": _num(r[c_tb]), "doc": str(r[c_sz] or "").strip(),
                    "origin": str(r[c_org] or "").strip()}
            (res["in"] if kg and kg > 0 else res["incomplete"]).append(item)
        hdr, rows = _table(wb[f"{code} 출고"], "출고일")
        c_to, c_day, c_kg, c_tb = _col(hdr, "출고처"), _col(hdr, "출고일"), _col(hdr, "중량_net(kg)"), _col(hdr, "Ton Bag", "Pallets")
        c_pr = _col(hdr, "단가 (USD)", "단가")
        c_sz = _col(hdr, "SZ Form") if "SZ Form" in hdr else _col(hdr, "서류번호")
        c_doc2 = _col(hdr, "서류번호") if "SZ Form" in hdr and "서류번호" in hdr else None
        for r in rows:
            d, kg, to = _day(r[c_day]), _num(r[c_kg]), str(r[c_to] or "").strip()
            if not d or not to or to == "None" or re.fullmatch(r"[\d+]+", to):
                continue      # 재고조정 / subtotal rows of the ledger
            docs = [str(r[c_sz] or "").strip()] + ([str(r[c_doc2] or "").strip()] if c_doc2 is not None else [])
            item = {"scrap": scrap, "date": d, "kg": kg, "bags": _num(r[c_tb]), "to": to, "price": _num(r[c_pr]),
                    "doc": " / ".join(x for x in docs if x and x != "None")}
            (res["out"] if kg and kg > 0 else res["incomplete"]).append(item)
    return res

def plan_inout(src, sh):
    ws_in, ws_out = sh.worksheet("입고"), sh.worksheet("출고")
    v_in, v_out = ws_in.get_all_values(), ws_out.get_all_values()
    in_keys, in_docs, first_in, price = set(), set(), {}, defaultdict(dict)   # price[(scrap, origin)][YYYY-MM] = p
    for r in v_in[1:]:
        r = r + [""] * 7
        sc, d, kg, p, note, org = r[0], _day(r[1]), _num(r[2]), _num(r[4]), r[5], r[6].strip()
        if not sc or not d:
            continue
        in_keys.add((sc, d, round(kg or 0)))
        in_docs.update(_norm_doc(x) for x in re.findall(r"[A-Z]{2,4}-?SZ[- ]?\d{4,7}", note.upper()))
        first_in[sc] = min(first_in.get(sc, d), d)
        if p:
            price[(sc, org)][d[:7]] = p
    out_keys, out_docs, first_out, learned = set(), set(), {}, {}
    for r in v_out[1:]:
        r = r + [""] * 8
        typ, d, sc, kg, note = r[0], _day(r[1]), r[2], _num(r[4]), r[6]
        if not sc or not d:
            continue
        out_keys.add((sc, d, round(kg or 0)))
        out_docs.update(_norm_doc(x) for x in re.findall(r"[A-Z]{2,4}-?SZ[- ]?\d{4,8}|A\d{11}", note.upper()))
        if typ != "재고조정":
            first_out[sc] = min(first_out.get(sc, d), d)
    # learn 출발지 -> origin label and 출고처 -> (type, processor) from rows that already match
    org_map = {}
    for it in src["in"]:
        for r in v_in[1:]:
            r = r + [""] * 7
            if (r[0], _day(r[1]), round(_num(r[2]) or 0)) == (it["scrap"], it["date"], round(it["kg"])) and r[6].strip():
                org_map.setdefault(it["origin"].upper(), r[6].strip())
    for it in src["out"]:
        for r in v_out[1:]:
            r = r + [""] * 8
            if (r[2], _day(r[1]), round(_num(r[4]) or 0)) == (it["scrap"], it["date"], round(it["kg"])):
                learned.setdefault(it["to"].upper(), (r[0], r[3]))
    new_in, new_out, unknown = [], [], []
    for it in src["in"]:
        if it["date"] < first_in.get(it["scrap"], "9999"):
            continue
        if (it["scrap"], it["date"], round(it["kg"])) in in_keys or (it["doc"] and _norm_doc(it["doc"]) in in_docs):
            continue
        org = org_map.get(it["origin"].upper(), it["origin"])
        hist = price.get((it["scrap"], org), {})
        p = PRICES.get(it["date"][:7], {}).get(f"{it['scrap']}/{org}")      # prices the user gave for the month
        if p is None:
            p = hist.get(it["date"][:7])
        temp = False
        if p is None:
            prev = sorted(k for k in hist if k < it["date"][:7])
            p, temp = (hist[prev[-1]], True) if prev else (None, True)
        note = f"{it['doc']} / {int(it['date'][5:7])}월 " + ("임시 단가" if temp else "단가")
        new_in.append({**it, "origin": org, "price": p, "temp": temp,
                       "row": [it["scrap"], it["date"], f"{it['kg']:.0f}", f"{it['bags']:.0f}" if it["bags"] else "",
                               "" if p is None else f"{p:g}", note, org]})
    for it in src["out"]:
        if it["date"] < first_out.get(it["scrap"], "9999"):
            continue
        docs = [_norm_doc(x) for x in it["doc"].split(" / ") if x]
        if (it["scrap"], it["date"], round(it["kg"])) in out_keys or any(dd in out_docs for dd in docs):
            continue
        kind = learned.get(it["to"].upper())
        if not kind:
            unknown.append(it)
            continue
        typ, proc = kind
        new_out.append({**it, "row": [typ, it["date"], it["scrap"], proc if typ == "임가공출고" else "", f"{it['kg']:.0f}",
                                      f"{it['bags']:.0f}" if it["bags"] else "", it["doc"],
                                      f"{it['price']:g}" if (typ == "직접판매" and it["price"]) else ""]})
    return {"new_in": new_in, "new_out": new_out, "unknown_out": unknown, "ws_in": ws_in, "ws_out": ws_out}


# ── 생산 (성일 톨링) ────────────────────────────────────────────────────────
def parse_tolling(wb):
    out = []
    for ws in wb.worksheets:
        m = re.match(r"(양극 극판|Dry JR)\s*(\d{2})년\s*(\d{1,2})월", ws.title)
        if not m:
            continue
        scrap = "양극" if m.group(1) == "양극 극판" else "젤리롤"
        month = f"20{m.group(2)}-{int(m.group(3)):02d}"
        rows = list(ws.iter_rows(values_only=True))
        ti = next((i for i, r in enumerate(rows) if r and isinstance(r[0], str) and r[0].strip().startswith("합계")), None)
        if ti is None or ti + 1 >= len(rows):
            out.append({"month": month, "scrap": scrap, "error": "합계 행 없음"}); continue
        lab = [str(v or "").strip() for v in rows[ti]]
        val = rows[ti + 1]
        ix = lambda name: next(i for i, s in enumerate(lab) if name in s)
        rec = {"month": month, "scrap": scrap, "in": _num(val[ix("총입고")]), "input": _num(val[ix("총투입")]),
               "output": _num(val[ix("분말회수율") + 1]), "byprod": _num(val[ix("부산물")]), "defect": _num(val[ix("불량")])}
        # cross-check: sum of daily Output (col 5) above the totals row; weekly '소   계' rows (label in 2nd cell) excluded
        _is_sub = lambda r: any(isinstance(x, str) and "소" in x and "계" in x for x in r[:3])
        rec["detail_output"] = sum(_num(r[5]) or 0 for r in rows[3:ti] if r and not _is_sub(r) and _num(r[5]))
        out.append(rec)
    return out

def plan_tolling(recs, sh, file_tag):
    ws = sh.worksheet("생산")
    v = ws.get_all_values()
    idx = {(r[0], r[1], r[2]): i for i, r in enumerate(v) if i and len(r) >= 3}
    changes = []
    for rc in recs:
        if "error" in rc:
            changes.append({"rec": rc, "action": "error"}); continue
        new = [rc["month"], "Sungeel", rc["scrap"]] + [f"{(rc[k] or 0):.0f}" for k in ("in", "input", "output", "byprod", "defect")]
        i = idx.get((rc["month"], "Sungeel", rc["scrap"]))
        cur = (v[i] + [""] * 9)[:8] if i is not None else None
        if cur and [str(_num(x) or 0) for x in cur[3:8]] == [str(_num(x) or 0) for x in new[3:8]]:
            continue
        note = (v[i] + [""] * 9)[8] if i is not None else ""
        if cur and (not note.startswith("성일 생산내역") or "상세 합계" in note):
            changes.append({"rec": rc, "action": "protected", "old": cur, "row": new, "note": note}); continue
        changes.append({"rec": rc, "action": "update" if cur else "append", "row_index": (i + 1) if i is not None else None,
                        "old": cur, "row": new + [f"성일 생산내역 {file_tag}"]})
    return {"changes": changes, "ws": ws}


# ── TGL report / szamla (report only) ───────────────────────────────────────
def parse_tgl(wb):
    hdr, rows = _table(wb.worksheets[0], "HBL")
    c = {k: _col(hdr, k) for k in ("HBL", "CONTAINER", "INVOICE", "ETD", "ETA", "VESSEL / VOY", "LOADING")}
    out, last = [], {}
    for r in rows:
        inv = str(r[c["INVOICE"]] or "").strip()
        if not inv.startswith("KHEEXP"):
            continue
        hbl = str(r[c["HBL"]] or "").strip()
        if hbl and hbl != "None":       # a second container row of the same HBL leaves these cells empty
            last = {"hbl": hbl, "etd": _day(r[c["ETD"]]), "eta": _day(r[c["ETA"]]), "vessel": str(r[c["VESSEL / VOY"]] or "")}
        out.append({"invoice": inv, "container": str(r[c["CONTAINER"]] or ""), "loading": _day(r[c["LOADING"]]), **last})
    return out

def report_tgl(items, sh):
    v = sh.worksheet("선적").get_all_values()
    by_inv = {r[1].strip(): r for r in v[1:] if len(r) > 10 and r[1].strip()}
    hbls = {re.sub(r"-\d+$", "", r[0].strip()) for r in v[1:] if r and r[0].strip()}
    recent = date.today().toordinal() - 75
    lines = []
    for it in items:
        r = by_inv.get(it["invoice"])
        if not r and it.get("hbl") in hbls:
            continue      # older shipments: several invoices in one row of the HBL
        if not r:
            lines.append(f"시트에 없는 Invoice {it['invoice']} (컨테이너 {it['container']}, 상차 {it['loading']}, TGL HBL {it.get('hbl') or '미정'})")
            continue
        if _day(r[2]) and date.fromisoformat(_day(r[2])).toordinal() < recent:
            continue      # loaded long ago: date differences are history
        hbl, etd, eta = r[0].strip(), _day(r[9]), _day(r[10])
        if hbl.upper().startswith("TBD") and it.get("hbl"):
            lines.append(f"{it['invoice']}: 시트 {hbl} → TGL HBL {it['hbl']} (선적/배치/컨테이너 탭 키 교체 필요)")
        if (it.get("etd") and it["etd"] != etd) or (it.get("eta") and it["eta"] != eta):
            lines.append(f"{it['invoice']} ({hbl}): ETD/ETA 시트 {etd or '—'} / {eta or '—'}, TGL {it.get('etd') or '—'} / {it.get('eta') or '—'}"
                         " (MSC 기준이 우선, 확인만)")
    return lines

def report_szamla(m, sh, days):
    v = sh.worksheet("선적").get_all_values()
    cost = defaultdict(list)
    for r in v[1:]:
        if r and r[0].strip():
            cost[re.sub(r"-\d+$", "", r[0].strip())].append(r[11].strip() if len(r) > 11 else "")
    seen, lines = set(), []
    for uid, d, frm, subj, _ in MI.recent(m, days):
        mh = re.search(r"SURRENDER\s*BL.*?(TGLHUS\d+)", subj, re.I)
        if not mh or mh.group(1) in seen:
            continue
        seen.add(mh.group(1))
        c = cost.get(mh.group(1))
        state = "시트에 없음" if c is None else ("수출비 입력됨" if all(c) else f"수출비 미입력 {sum(1 for x in c if not x)}행")
        lines.append(f"{mh.group(1)}: szamla 메일 {d[:16]}, {state}")
    return lines


# ── CLI ────────────────────────────────────────────────────────────────────
def run(kinds, write, days):
    m, user = MI.connect()
    sh = _sheet()
    print(f"IMAP {user}, 시트 {SHEET}, {'쓰기' if write else '미리보기(쓰지 않음)'}")
    if "inout" in kinds:
        mail = _latest_mail(m, "inout", days)
        fn, wb = _xlsx(m, mail[0])
        print(f"\n[입출고] {mail[3]} ({mail[2]}, {mail[1][:22]}) 첨부 {fn}")
        src = parse_inout(wb)
        p = plan_inout(src, sh)
        for it in p["new_in"]:
            print(f"  + 입고 {it['row']}" + ("  <- 임시 단가" if it["temp"] else "") + ("  <- 단가 없음(쓰지 않음)" if it["price"] is None else ""))
        for it in p["new_out"]:
            print(f"  + 출고 {it['row']}")
        for it in p["unknown_out"]:
            print(f"  ? 출고처 분류 불명(쓰지 않음): {it['scrap']} {it['date']} {it['to']} {it['kg']:.0f}kg {it['doc']}")
        for it in [x for x in src["incomplete"] if x["date"] >= "2026-10-01"]:
            print(f"  ! 원본 중량 비어 있음(쓰지 않음): {it['scrap']} {it['date']} {it['doc']}")
        if not (p["new_in"] or p["new_out"]):
            print("  새 행 없음")
        if write and (p["new_in"] or p["new_out"]):
            ok_in = [it["row"] for it in p["new_in"] if it["price"] is not None]
            if ok_in:
                p["ws_in"].append_rows(ok_in, value_input_option="USER_ENTERED")
            if p["new_out"]:
                p["ws_out"].append_rows([it["row"] for it in p["new_out"]], value_input_option="USER_ENTERED")
            print(f"  -> 입고 {len(ok_in)}행, 출고 {len(p['new_out'])}행 추가함")
    if "tolling" in kinds:
        mail = _latest_mail(m, "tolling", max(days, 60))
        fn, wb = _xlsx(m, mail[0])
        tag = (re.match(r"(\d{8})", fn or "") or [None, mail[1][:10]])[1]
        print(f"\n[생산] {mail[3].strip()} ({mail[1][:22]}) 첨부 {fn}")
        recs = parse_tolling(wb)
        for rc in recs:
            if "error" not in rc and rc["output"] and abs(rc["detail_output"] - rc["output"]) > 1:
                print(f"  ! {rc['month']} {rc['scrap']}: 합계 생산 {rc['output']:.0f} vs 상세 합 {rc['detail_output']:.0f} (확인)")
        p = plan_tolling(recs, sh, tag)
        for ch in p["changes"]:
            if ch["action"] == "error":
                print(f"  ! {ch['rec']['month']} {ch['rec']['scrap']}: {ch['rec']['error']}")
            elif ch["action"] == "protected":
                print(f"  = 보호(수동 조정 행, 쓰지 않음) {ch['row'][:3]} 파일 {ch['row'][3:8]} / 시트 {ch['old'][3:8]}")
            else:
                print(f"  {'~ 변경' if ch['action'] == 'update' else '+ 추가'} {ch['row'][:8]}" + (f"  (기존 {ch['old'][3:8]})" if ch["old"] else ""))
        if not [c for c in p["changes"] if c["action"] in ("update", "append")]:
            print("  바뀐 월 없음")
        if write:
            n = 0
            for ch in p["changes"]:
                if ch["action"] == "update":
                    p["ws"].update(range_name=f"A{ch['row_index']}:I{ch['row_index']}", values=[ch["row"]], value_input_option="USER_ENTERED"); n += 1
                elif ch["action"] == "append":
                    p["ws"].append_rows([ch["row"]], value_input_option="USER_ENTERED"); n += 1
            if n:
                print(f"  -> 생산 {n}행 반영함")
    if "tgl" in kinds:
        mail = _latest_mail(m, "tgl", days)
        fn, wb = _xlsx(m, mail[0])
        print(f"\n[TGL 리포트] {mail[3]} ({mail[1][:22]}) 첨부 {fn} — 보고만")
        lines = report_tgl(parse_tgl(wb), sh)
        print("\n".join("  " + x for x in lines) if lines else "  시트와 차이 없음")
    if "szamla" in kinds:
        print("\n[TGL szamla] — 보고만 (PDF 금액은 직접 확인)")
        lines = report_szamla(m, sh, days)
        print("\n".join("  " + x for x in lines) if lines else "  최근 szamla 메일 없음")
    m.logout()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=["all", "inout", "tolling", "tgl", "szamla"])
    ap.add_argument("--write", action="store_true", help="입출고/생산을 시트에 반영 (TGL/szamla는 항상 보고만)")
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    run(["inout", "tolling", "tgl", "szamla"] if a.kind == "all" else [a.kind], a.write, a.days)
