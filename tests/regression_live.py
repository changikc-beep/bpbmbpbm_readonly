# -*- coding: utf-8 -*-
"""Live-data regression check — run before pushing calculation changes.

Downloads the current config.json from Google Drive (read-only, local service-account file
required) and checks settlement/P&L/inventory invariants plus a few settled amounts that
must never change. Nothing is written anywhere.

    python tests/regression_live.py
Exit code 0 = all checks passed.
"""
import io, json, os, sys, warnings
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import smoke_test as T          # exec's app.py helper region into T.NS (no Streamlit runtime)

F = T.NS
CREDS = os.path.join(os.path.dirname(HERE), "bp-calculator-498206-4308cbd64cba.json")

# 확정·검증이 끝난 금액 — 계산식을 고쳐도 바뀌면 안 되는 값 (2026-09-30 기준)
SETTLED_FINAL = {
    "TGLHUS26030002": 529252.08, "TGLHUS26030004": 226484.28, "TGLHUS26040001": 486151.53,
    "TGLHUS26040004": 213937.17, "TGLHUS26040006": 387922.86, "FSKBUDS26061000": 276130.53,
}
PROV_INVOICE = {"TGLHUS26090002": 434525.58, "TGLHUS26090002-1": 209026.38}   # EcoPro 8월 QP payable 118%


def load_live():
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    creds = Credentials.from_service_account_file(CREDS, scopes=["https://www.googleapis.com/auth/drive.readonly"])
    svc = build("drive", "v3", credentials=creds)
    fid = svc.files().list(q="name='config.json' and trashed=false", fields="files(id)").execute()["files"][0]["id"]
    buf = io.BytesIO(); dl = MediaIoBaseDownload(buf, svc.files().get_media(fileId=fid)); done = False
    while not done:
        _, done = dl.next_chunk()
    return json.loads(buf.getvalue().decode("utf-8"))


RES = []
def check(label, cond, detail=""):
    RES.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + label + ("" if cond or not detail else f"  -> {detail}"))


def main():
    if not os.path.exists(CREDS):
        print("SKIP: 로컬 서비스 계정 파일이 없어 실데이터 회귀 점검을 건너뜁니다.")
        return 0
    cfg = load_live()
    ships = {s["hbl"]: s for s in cfg["shipments"]}
    print(f"config rev {cfg.get('_meta', {}).get('rev')} · 선적 {len(ships)} · 배치 {len(cfg['processing_history'])}")

    # 1) 확정 금액 고정값
    for hbl, exp in SETTLED_FINAL.items():
        s = ships.get(hbl)
        got = F["_recompute_final_settlement"](cfg, s) if s else None
        check(f"확정액 {hbl} = {exp:,.2f}", s and got is not None and abs(got - exp) < 0.01
              and abs(float(s.get("final_amount_usd") or 0) - exp) < 0.01, f"계산 {got} / 저장 {s and s.get('final_amount_usd')}")
    for hbl, exp in PROV_INVOICE.items():
        s = ships.get(hbl)
        got = F["_prov_invoice_calc"](cfg, s) if s else None
        check(f"가정산 계산 {hbl} = {exp:,.2f}", got is not None and abs(got - exp) < 0.01, f"계산 {got}")

    # 2) 불변 조건
    recalc = [s["hbl"] for s in cfg["shipments"] if s.get("final_amount_usd")
              and (lambda v: v is not None and abs(v - float(s["final_amount_usd"])) >= 0.01)(F["_recompute_final_settlement"](cfg, s))]
    check("확정액 재계산 필요 0건", not recalc, recalc)
    mism = [s["hbl"] for s in cfg["shipments"] if F["_inv_mismatch"](cfg, s)]
    check("가정산 Invoice 불일치 0건", not mism, mism)
    rm = F["_batch_revenue_map"](cfg)
    bad = []
    for s in cfg["shipments"]:
        rs = [r for r in cfg["processing_history"] if r.get("shipment_id") == s["id"]]
        if not rs:
            continue
        tgt = (float(s["final_amount_usd"]) if s.get("final_amount_usd") else float(s.get("invoice_usd") or 0)) \
              + float(s.get("other_adj_usd") or 0)
        if abs(sum(rm[r.get("id") or id(r)][0] for r in rs) - tgt) > 0.01:
            bad.append(s["hbl"])
    check("배치 매출 합계 = 선적 금액", not bad, bad)
    sids = {s["id"] for s in cfg["shipments"]}
    orphans = [r.get("id") for r in cfg["processing_history"] if r.get("shipment_id") and r["shipment_id"] not in sids]
    check("연결 끊긴 배치 0건", not orphans, orphans)
    for row in F["_production_recon"](cfg):
        tag = f"{row['임가공사']} {row['스크랩']}"
        check(f"생산 대사 {tag}: 계량차 1% 이내", abs(row["계량차(입고−출고)"]) <= 0.01 * max(row["당사 출고"], 1),
              row["계량차(입고−출고)"])
        check(f"생산 대사 {tag}: 선적 ≤ 생산 + 1%", row["선적(배치)"] <= row["생산"] * 1.01 + 1,
              f"선적 {row['선적(배치)']} / 생산 {row['생산']}")

    ok = all(RES)
    print(f"\n{'ALL PASS' if ok else 'SOME FAILED'} ({sum(RES)}/{len(RES)})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
