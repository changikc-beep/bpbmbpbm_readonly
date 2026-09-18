# -*- coding: utf-8 -*-
"""Smoke test for app.py's pure helpers on a synthetic config of realistic size.

app.py renders Streamlit UI at import time, so the helper block (bp_price ..
_pnl_agg) and the Excel generator are extracted by source markers and exec'd.
No Google Drive / secrets needed.

Run from the repo root:
    python tests/smoke_test.py
Exit code 0 = all checks passed.
"""
import io, json, sys, os, re, uuid, hashlib, random, warnings, logging, inspect
from collections import defaultdict
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st

warnings.filterwarnings("ignore")
logging.getLogger("streamlit").setLevel(logging.ERROR)

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
LINES = open(APP, encoding="utf-8").read().split("\n")


def _find(marker, start=0):
    for i in range(start, len(LINES)):
        if marker in LINES[i]:
            return i
    raise SystemExit("marker not found: " + marker)


NS = {"st": st, "pd": pd, "json": json, "hashlib": hashlib, "re": re, "os": os, "uuid": uuid,
      "date": date, "datetime": datetime, "timedelta": timedelta, "defaultdict": defaultdict,
      "BytesIO": io.BytesIO, "READ_ONLY": False, "_HAS_LOCAL_CREDS": False, "CONFIG_FILE": "x"}
h0 = _find("def bp_price(");              h1 = _find("# ── Sidebar ─", h0)
x0 = _find("def generate_excel_report(");   x1 = _find("# TAB 0 — 요약 보고서", x0)
exec(compile("\n".join(LINES[h0:h1]), "helpers", "exec"), NS)
exec(compile("\n".join(LINES[x0:x1]), "excel", "exec"), NS)


# ── synthetic cfg ────────────────────────────────────────────────────────────
def build_cfg():
    random.seed(7)
    rid = lambda: str(uuid.uuid4())[:8]
    scraps = [{"id": rid(), "name": n, "ni_content": 41.9, "co_content": 7.2, "active": True,
               "storage_rate_eur": 1.3, "product": p}
              for n, p in [("양극", "BP"), ("젤리롤", "BM"), ("셀", "BM"), ("모듈", "BM")]]
    procs = [{"id": rid(), "name": n, "active": True,
              "conditions": {s["id"]: {"processing_fee": 0.53, "conversion_rate": 80.0, "impurity_rate": None}
                             for s in scraps}} for n in ["Sungeel", "Granuline", "ISBM"]]
    buyers = [{"id": rid(), "name": n, "product": p, "ni_payable": 1.13, "co_payable": 1.13,
               "ni_content": 41.93, "co_content": 7.23, "active": True, "prov_pay_days": 15, "final_pay_days": 30}
              for n, p in [("ECOPRO", "BP"), ("POSCO", "BP"), ("SUNGEEL", "BP"), ("SUNGEEL", "BM"), ("ISECO", "BP")]]
    months = [f"2026-{m:02d}" for m in range(1, 13)]
    shipments = []
    for i in range(60):
        ld = date(2026, 1 + i % 8, 1 + i % 27)
        shipments.append({
            "id": rid(), "hbl": f"TGLHUS26{i:06d}", "invoice_no": f"KHEEXP-2026-{i}",
            "loading_date": ld.isoformat(), "etd": (ld + timedelta(days=10)).isoformat(),
            "eta": (ld + timedelta(days=55)).isoformat(),
            "buyer_id": buyers[i % 5]["id"], "weight_kg": 17000 + (i * 37) % 3000,
            "invoice_usd": 230000 + i * 1000, "export_cost_usd": 4400.0 if i % 3 else None,
            "prov_month": months[max(0, ld.month - 2)], "final_month": months[ld.month - 1],
            "status": ["provisional", "final", "paid"][i % 3], "notes": "",
            "moisture_pct": 1.5, "buyer_ni_content": 41.7, "buyer_co_content": 7.6,
            "ni_content_src": "매입사값", "co_content_src": "매입사값",
            "other_adj_usd": None, "other_adj_desc": "",
            "final_amount_usd": 240000.0 if i % 3 else None, "linked_contract_id": None,
        })
    ph = [{"id": rid(), "shipment_id": shipments[i % 60]["id"], "processor_id": procs[i % 3]["id"],
           "scrap_type_id": scraps[i % 2]["id"], "output_kg": 17000.0, "conversion_rate_pct": 80.0,
           "input_kg": 21250.0, "bp_sale_per_kg": 14.1, "scrap_sale_per_kg": 5.5,
           "processing_fee_per_kg": 0.53, "buyer_id": shipments[i % 60]["buyer_id"], "notes": ""}
          for i in range(90)]
    inv = {s["id"]: {"opening": {"date": "2025-11-11", "quantity_kg": 300000.0, "unit_cost": 5.7, "ton_bags": 600},
                     "purchases": [{"date": (date(2025, 12, 1) + timedelta(days=7 * k)).isoformat(),
                                    "quantity_kg": 40000.0, "ton_bags": 80, "unit_cost": 5.6 + k * 0.01}
                                   for k in range(40)]} for s in scraps}
    dispatch = [{"id": rid(), "date": (date(2026, 1, 5) + timedelta(days=5 * k)).isoformat(),
                 "processor_id": procs[k % 3]["id"], "scrap_type_id": scraps[k % 2]["id"],
                 "quantity_kg": 40000.0, "ton_bags": 80, "notes": ""} for k in range(60)]
    contracts = [{"id": rid(), "buyer_id": buyers[k % 5]["id"], "product": "BP", "scrap_type_id": scraps[k % 2]["id"],
                  "processor_id": "", "contract_qty_mt": 500.0, "tolerance_pct": 5.0, "start_date": "2026-01-01",
                  "end_date": "2026-12-31", "notes": "", "contract_status": "active", "ni_payable_pct": None,
                  "co_payable_pct": None, "prov_pct": 80.0, "prov_index_basis": "prov", "final_index_basis": "final"}
                 for k in range(6)]
    return {"buyers": buyers, "processors": procs, "scrap_types": scraps, "shipments": shipments,
            "processing_history": ph, "raw_material_inventory": inv, "dispatch_records": dispatch,
            "direct_sales": [{"id": rid(), "date": "2026-03-01", "scrap_type_id": scraps[2]["id"],
                              "quantity_kg": 5000.0, "sale_price_per_kg": 3.1, "notes": ""}],
            "index_history": [{"month": m, "ni_index": 17000 + i * 90, "co_index": 56000 + i * 60}
                              for i, m in enumerate(months)],
            "eur_usd_rates": [{"month": m, "rate": 1.08 + i * 0.002} for i, m in enumerate(months)],
            "contracts": contracts,
            "contract_allocations": [{"id": rid(), "contract_id": contracts[k % 6]["id"],
                                      "shipment_id": shipments[k]["id"], "allocated_kg": 17000.0} for k in range(12)],
            "forwarders": [], "freight": {"eur_usd": 1.08}, "sk_prices": {}, "index_history_alt": {},
            "sga_monthly": [{"month": "2026-06", "sga": 1000.0, "other": 50.0}], "usd_krw_rates": []}


RESULTS = []


def check(label, cond):
    RESULTS.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + label)


def main():
    cfg = build_cfg()
    ships, scraps = cfg["shipments"], cfg["scrap_types"]
    f = NS

    ec = f["_eff_content"]
    check("_eff_content 매입사값/당사값/평균", ec(41.77, 41.93, "매입사값") == 41.77 and ec(41.77, 41.93, "당사값") == 41.93
          and ec(41.77, 41.92, "평균") == round((41.77 + 41.92) / 2, 2) and ec(None, 1.0, "매입사값") == 0.0)

    fifo = f["_fifo_lot_trace"]
    r1 = fifo(cfg, scraps[0]["id"]); r2 = fifo(cfg, scraps[0]["id"])
    check("_fifo_lot_trace cached result identical", r1 == r2)
    cfg["dispatch_records"].append({"id": "zz", "date": "2026-08-01", "processor_id": cfg["processors"][0]["id"],
                                    "scrap_type_id": scraps[0]["id"], "quantity_kg": 1234.0, "ton_bags": 2, "notes": ""})
    check("fingerprint cache sees cfg mutation", fifo(cfg, scraps[0]["id"]) != r1)
    cfg["dispatch_records"].pop()

    rf = f["_recompute_final_settlement"]
    check("_recompute_final_settlement signature", list(inspect.signature(rf).parameters) == ["cfg", "s", "fallback_index"])
    check("_recompute_final_settlement runs", all(v is None or v > 0 for v in (rf(cfg, s) for s in ships)))
    s0 = dict(ships[0]); s0["final_month"] = "2027-01"
    check("fallback_index path", rf(cfg, s0) is None and rf(cfg, s0, fallback_index=(17000.0, 56000.0)) > 0)
    check("_prov_invoice_calc positive", (f["_prov_invoice_calc"](cfg, ships[0]) or 0) > 0)

    ctx = f["_pnl_context"](cfg)
    rows = f["_batch_pnl_rows"](cfg, ctx)
    check("_batch_pnl_rows one row per batch", len(rows) == len(cfg["processing_history"]))
    check("batch rows positive and sourced", all(r["bp"] > 0 and r["pf"] > 0 and r["rmc_src"] for r in rows))
    agg = f["_pnl_agg"](rows, lambda x: x["month"])
    check("_pnl_agg totals match", abs(sum(a["bp"] for a in agg.values()) - sum(r["bp"] for r in rows)) < 1e-6)
    check("이동평균 mode runs", len(f["_batch_pnl_rows"](cfg, ctx, "이동평균 우선")) == len(rows))

    cfg["processing_history"].append({"id": "u1", "shipment_id": "", "processor_id": cfg["processors"][0]["id"],
                                      "scrap_type_id": scraps[0]["id"], "output_kg": 5000.0, "input_kg": 6250.0,
                                      "conversion_rate_pct": 80.0, "bp_sale_per_kg": 14.0, "scrap_sale_per_kg": 5.5,
                                      "processing_fee_per_kg": 0.53, "buyer_id": "", "notes": ""})
    check("_finished_goods_kg counts unlinked batch", f["_finished_goods_kg"](cfg, scraps[0]["id"]) == 5000.0)
    m = f["_contract_metrics"](cfg, cfg["contracts"][0])
    check("_contract_metrics keys + finished goods in avail",
          m["conv_src"] in ("실적", "계약", "기본값") and m["finished_bp_mt"] == 5.0
          and abs(m["total_avail_mt"] - (m["warehouse_bp_mt"] + m["at_proc_bp_mt"] + m["finished_bp_mt"])) < 1e-9)
    check("_conv_rate_for fallbacks",
          f["_conv_rate_for"]({"processing_history": [], "processors": [{"id": "p", "conditions": {"s": {"conversion_rate": 68}}}]}, "s") == (68.0, "계약")
          and f["_conv_rate_for"]({}, "zz") == (80.0, "기본값"))
    check("_sga_totals", f["_sga_totals"](cfg) == (1000.0, 50.0))

    xc = f["_excel_report_cached"]
    todo = [("🔴", "t", "d", "tab")]
    cash = [{"구분": "청구 가능", "HBL": "X", "매입사": "Y", "상태": "final", "Final월": "2026-04", "기준": "확정",
             "가정산 수령": 100.0, "확정산 잔액": 50.0, "예상 입금월": "2026-07"}]
    b1 = xc(cfg, 17093.18, 56598.72, 1380, "2026-08", cfg["buyers"][0]["id"], todo, cash)
    b2 = xc(cfg, 17093.18, 56598.72, 1380, "2026-08", cfg["buyers"][0]["id"], todo, cash)
    check("excel cached + valid xlsx", b1 == b2 and b1[:2] == b"PK")
    import openpyxl
    ws = openpyxl.load_workbook(io.BytesIO(b1)).active
    texts = {str(c.value) for row in ws.iter_rows() for c in row if c.value is not None}
    check("excel has 할 일·현금 전망·완제품 sections",
          any("할 일" in t for t in texts) and any("미수 현금 전망" in t for t in texts) and any("완제품" in t for t in texts))

    ok = all(RESULTS)
    print(f"\n{'ALL PASS' if ok else 'SOME FAILED'} ({sum(RESULTS)}/{len(RESULTS)})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
