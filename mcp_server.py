# -*- coding: utf-8 -*-
"""Remote MCP server for a claude.ai custom connector — read-only BP/BM data questions.

Every tool runs a bp_ask.py query, so answers use app.py's own calculation helpers and match the app.
Sign-in is Google OAuth (FastMCP OAuth proxy); only addresses in ALLOWED_EMAILS can call tools.

Environment (Cloud Run):
    BASE_URL              public https URL of this service (no trailing slash), e.g. https://bp-mcp-xxxx.a.run.app
    GOOGLE_CLIENT_ID      OAuth client (Web application) from Google Cloud Console
    GOOGLE_CLIENT_SECRET
    ALLOWED_EMAILS        comma-separated Google accounts allowed to use the tools (empty = nobody)
    DRIVE_CONFIG_FILE_ID  optional: Drive file id of config.json (otherwise found by name)
Local test without sign-in (binds 127.0.0.1 only):
    BP_MCP_LOCAL=1 python mcp_server.py
"""
import os, sys, time
from typing import Literal, Optional

sys.stdout.reconfigure(encoding="utf-8")
from fastmcp import FastMCP

LOCAL = os.environ.get("BP_MCP_LOCAL") == "1"
ALLOWED = {e.strip().lower() for e in os.environ.get("ALLOWED_EMAILS", "").split(",") if e.strip()}

INSTRUCTIONS = (
    "KHE Ecotech의 EV 배터리 스크랩 → 임가공(톨링) → BP/BM 수출 손익·재고 데이터를 읽기 전용으로 조회한다. "
    "숫자는 반드시 도구 결과에서 가져오고 직접 계산하거나 추정하지 않는다. 답에는 결과 첫 줄의 데이터 rev·저장 시각을 함께 밝힌다. "
    "매출 = 선적 확정액(없으면 가정산 Invoice) + 기타 조정. 실질 손익 = 매출 − 원료비(FIFO) − 임가공비 − 수출비 − 보관비, 판관비 제외. "
    "상태: provisional=가정산, final=확정산, paid=입금완료. 매입사 예: EcoPro, POSCO, Sungeel, IS ECO (제품 BP/BM)."
)


def _auth():
    if LOCAL:
        return None
    if not all(os.environ.get(k) for k in ("BASE_URL", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")):
        # First deploy happens before the OAuth client exists: start anyway so Cloud Run gets a URL,
        # but with no sign-in every tool call is refused in _run (no email → not allowed).
        print("BASE_URL / GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not set — all tool calls are refused.", flush=True)
        return None
    from fastmcp.server.auth.providers.google import GoogleProvider
    from key_value.aio.stores.firestore import FirestoreStore
    from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
    secret = os.environ["GOOGLE_CLIENT_SECRET"]
    # Cloud Run instances are stateless and scale to zero: keep OAuth client registrations and tokens in
    # Firestore so connections survive restarts. Encrypted with a key derived from the client secret.
    storage = FernetEncryptionWrapper(FirestoreStore(default_collection="bp_mcp_oauth"),
                                      source_material=secret, salt="bp-mcp-oauth-storage")
    return GoogleProvider(
        client_id=os.environ["GOOGLE_CLIENT_ID"], client_secret=secret,
        base_url=os.environ["BASE_URL"],
        required_scopes=["openid", "https://www.googleapis.com/auth/userinfo.email"],
        client_storage=storage,
    )


mcp = FastMCP("BP/BM 데이터", instructions=INSTRUCTIONS, auth=_auth())

_cache = {"at": 0.0, "cfg": None}

def _bp_ask():
    # Imported on the first tool call, not at startup: it loads pandas/streamlit and app.py's helpers
    # (several seconds), and Claude gives the OAuth discovery endpoints only 10 seconds after a cold start.
    import bp_ask
    return bp_ask

def _cfg():
    """Drive config, reused for 2 minutes (same freshness as the app's own cache)."""
    if _cache["cfg"] is None or time.time() - _cache["at"] > 120:
        _cache["cfg"], _cache["at"] = _bp_ask().load_cfg(), time.time()
    return _cache["cfg"]

def _run(*argv):
    if not LOCAL:
        from fastmcp.server.dependencies import get_access_token
        tok = get_access_token()
        email = ((tok.claims or {}).get("email") or "").lower() if tok else ""
        if email not in ALLOWED:                      # fail closed: empty list allows nobody
            return f"접근 권한이 없는 계정입니다 ({email or '이메일 확인 불가'})."
    return _bp_ask().ask([a for a in argv if a is not None], _cfg())

def _opt(flag, value):
    return (flag, value) if value else (None, None)


@mcp.tool
def summary(quarter: Optional[str] = None, buyer: Optional[str] = None,
            product: Optional[Literal["BP", "BM"]] = None) -> str:
    """분기 요약: 매출·선적 건수·평균 매각 단가·판매 중량·실질 손익/마진율(직전 분기 대비)과
    매입사별·스크랩 유형별 매출, 임가공사별 생산, 정산 상태. quarter 예: '2026Q3' (생략 시 실적이 있는 최근 분기).
    buyer는 매입사 이름 일부(예: 'ecopro', 'posco bm')."""
    return _run("summary", quarter, *_opt("--buyer", buyer), *_opt("--product", product))

@mcp.tool
def todo() -> str:
    """앱 홈의 '할 일' 목록: 확정산 진행 가능, Invoice 불일치, 수출비·INDEX 미입력, 입금 기록 누락 등."""
    return _run("todo")

@mcp.tool
def receivables(buyer: Optional[str] = None) -> str:
    """미수 확정산 잔액(청구 가능 / INDEX 대기 추정)과 선적건별 예상 입금일. buyer는 매입사 이름 일부."""
    return _run("ar", *_opt("--buyer", buyer))

@mcp.tool
def shipment(hbl: str) -> str:
    """선적 1건 상세: 상태, 중량, Invoice, Prov/Final월, 확정액과 계산값, 입금 기록, 수출비, 배치별 손익.
    hbl은 전체 번호 또는 일부(여러 건이 맞으면 후보 목록을 돌려줌)."""
    return _run("ship", hbl)

@mcp.tool
def shipments(buyer: Optional[str] = None,
              status: Optional[Literal["provisional", "final", "paid"]] = None) -> str:
    """선적 목록(선적일순): HBL, 매입사, 중량, Invoice, 확정액, 상태, Final월."""
    return _run("ships", *_opt("--buyer", buyer), *_opt("--status", status))

@mcp.tool
def pnl(by: Literal["month", "quarter", "buyer", "hbl", "processor", "scrap"] = "month",
        year: Optional[int] = None, buyer: Optional[str] = None,
        product: Optional[Literal["BP", "BM"]] = None) -> str:
    """손익 집계(손익 탭과 같은 엔진): 생산 MT, 매출, 원료비, 임가공비, 수출비, 보관비, 실질 손익, 마진율과 합계."""
    return _run("pnl", "--by", by, *_opt("--year", str(year) if year else None),
                *_opt("--buyer", buyer), *_opt("--product", product))

@mcp.tool
def stock() -> str:
    """재고 추정: 스크랩별 창고 원료·임가공사 보유 원료·완제품(BP/BM)과 임가공사 생산 보고 기준 생산·재고 대사."""
    return _run("stock")


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1" if LOCAL else "0.0.0.0",
            port=int(os.environ.get("PORT", "8080")), stateless_http=True)
