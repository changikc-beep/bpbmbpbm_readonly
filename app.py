import streamlit as st
import json, os, re, uuid, hashlib
import pandas as pd
from datetime import date, datetime, timedelta
from io import BytesIO

st.set_page_config(page_title="BP/BM 재고·손익 관리", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
/* ══════════════════════════════════════════════
   Notion Dark — custom theme layer
   bg:#191919  surface:#252525  border:#373737
   accent:#2383e2  text-2:#9b9b9b
   ══════════════════════════════════════════════ */

/* ── Layout ── */
.main .block-container{
    padding-top:1.5rem;padding-bottom:2.5rem
}
section[data-testid="stSidebar"]{
    min-width:260px;
    border-right:1px solid #2d2d2d !important
}

/* ── Tab bar — pill strip on dark ── */
div[data-testid="stTabs"] div[data-baseweb="tab-list"]{
    background:#252525;border-radius:10px;padding:3px;
    border:1px solid #333;gap:2px
}
div[data-testid="stTabs"] button[role="tab"]{
    border-radius:7px !important;font-size:.82rem;font-weight:500;
    padding:5px 13px !important;color:#9b9b9b;
    transition:background .15s,color .15s;border:none !important;
    white-space:nowrap
}
div[data-testid="stTabs"] button[role="tab"]:hover{
    background:rgba(255,255,255,.06) !important;color:#e5e5e5
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"]{
    background:#2383e2 !important;color:#fff !important;
    font-weight:600;box-shadow:0 1px 6px rgba(35,131,226,.40) !important
}
div[data-testid="stTabs"] button[role="tab"] p{font-weight:inherit !important}
div[data-testid="stTabs"] [data-baseweb="tab-highlight"]{display:none !important}
div[data-testid="stTabs"] [data-baseweb="tab-border"]{display:none !important}

/* ── Expanders — elevated dark card ── */
div[data-testid="stExpander"] details{
    border-radius:12px !important;
    border:1px solid #333 !important;
    background:#252525 !important;
    overflow:hidden;
    transition:border-color .15s,box-shadow .15s;
    box-shadow:0 1px 3px rgba(0,0,0,.35)
}
div[data-testid="stExpander"] details:hover{
    border-color:#4a4a4a !important;
    box-shadow:0 2px 8px rgba(0,0,0,.45) !important
}
div[data-testid="stExpander"] details summary{
    padding:13px 18px !important;font-weight:500;
    background:#2a2a2a !important
}
div[data-testid="stExpander"] details[open]>summary{
    border-bottom:1px solid #333 !important
}
div[data-testid="stExpander"] details>div,
div[data-testid="stExpander"] details>div>div{
    padding:16px 20px !important
}

/* ── Metric cards — dark surface ── */
div[data-testid="metric-container"]{
    background:#252525 !important;
    border:1px solid #333 !important;
    border-radius:12px !important;
    padding:14px 18px !important;
    transition:border-color .15s,box-shadow .15s;
    box-shadow:0 1px 3px rgba(0,0,0,.3)
}
div[data-testid="metric-container"]:hover{
    border-color:#4a4a4a !important;
    box-shadow:0 2px 8px rgba(0,0,0,.4) !important
}
div[data-testid="stMetricValue"]{font-size:1.45rem !important;letter-spacing:-.5px;font-weight:600}
div[data-testid="stMetricLabel"] p{font-size:.78rem !important;color:#9b9b9b !important}
div[data-testid="stMetricDelta"] svg{width:14px;height:14px}

/* ── Sidebar metric cards — slightly different shade ── */
section[data-testid="stSidebar"] div[data-testid="metric-container"]{
    background:#2a2a2a !important;border-color:#363636 !important
}

/* ── Buttons ── */
div[data-testid="stButton"]>button,
div[data-testid="stPopover"]>button,
div[data-testid="stFormSubmitButton"]>button{
    border-radius:8px !important;font-weight:500;
    transition:all .15s;
    border:1px solid #3d3d3d !important
}
div[data-testid="stButton"]>button:hover,
div[data-testid="stFormSubmitButton"]>button:hover{
    border-color:#555 !important;
    box-shadow:0 0 0 2px rgba(35,131,226,.25) !important
}

/* ── Inputs ── */
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextAreaInput"] textarea{
    border-radius:8px !important;
    background:#2e2e2e !important;
    border:1px solid #575757 !important;
    color:#e5e5e5 !important
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stNumberInput"] input:focus,
div[data-testid="stTextAreaInput"] textarea:focus{
    border-color:#2383e2 !important;
    box-shadow:0 0 0 2px rgba(35,131,226,.25) !important;
    outline:none !important
}
/* baseweb 버전에 따라 select 내부 div 깊이가 달라질 수 있어 루트와 1단계 자식 모두에
   동일 스타일을 적용 (multiselect 태그 pill은 건드리지 않도록 자손 전체는 건드리지 않음) */
div[data-testid="stSelectbox"] [data-baseweb="select"],
div[data-testid="stSelectbox"] [data-baseweb="select"]>div,
div[data-testid="stMultiSelect"] [data-baseweb="select"],
div[data-testid="stMultiSelect"] [data-baseweb="select"]>div{
    border-radius:8px !important;
    background:#2e2e2e !important;
    border:1px solid #575757 !important
}
div[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within,
div[data-testid="stMultiSelect"] [data-baseweb="select"]:focus-within{
    border-color:#2383e2 !important;
    box-shadow:0 0 0 2px rgba(35,131,226,.25) !important
}
div[data-testid="stDateInput"] input{
    border-radius:8px !important;
    background:#2e2e2e !important;
    border:1px solid #575757 !important;
    color:#e5e5e5 !important
}

/* ── Progress bars — slim accent ── */
div[data-testid="stProgress"]{margin-bottom:14px !important;margin-top:2px !important}
div[data-testid="stProgress"]>div{
    border-radius:20px !important;height:6px !important;
    overflow:hidden;background:#333 !important
}
div[data-testid="stProgress"]>div>div{
    border-radius:20px !important;
    background:linear-gradient(90deg,#2383e2,#60a5fa) !important
}
div[data-testid="stProgress"] p{font-size:.8rem;color:#9b9b9b;margin-bottom:5px}

/* ── Alert / info boxes ── */
div[data-testid="stAlert"]{border-radius:10px !important}

/* ── Forms ── */
div[data-testid="stForm"]{
    border-radius:12px !important;
    border:1px solid #333 !important;
    background:#252525 !important;
    padding:16px !important
}

/* ── Column row bottom spacing ── */
div[data-testid="stHorizontalBlock"]{margin-bottom:16px !important}

/* ── Dividers ── */
hr{border-color:#2d2d2d !important;margin:1.2rem 0}

/* ── Dataframes — dark card container ── */
div[data-testid="stDataFrame"]{
    border:1px solid #383838 !important;
    border-radius:10px !important;
    overflow:hidden !important;
    box-shadow:0 2px 8px rgba(0,0,0,.35) !important;
    margin-bottom:8px !important
}

/* ── Markdown tables — dark card style ── */
div[data-testid="stMarkdown"] table{
    border-collapse:separate !important;
    border-spacing:0 !important;
    border:1px solid #383838 !important;
    border-radius:10px !important;
    overflow:hidden !important;
    width:100%;
    margin-bottom:12px !important
}
div[data-testid="stMarkdown"] table thead tr th{
    background:#2d2d2d !important;
    color:#e5e5e5 !important;
    font-weight:600 !important;
    padding:10px 14px !important;
    border-bottom:1px solid #383838 !important;
    font-size:.82rem !important;
    white-space:nowrap
}
div[data-testid="stMarkdown"] table tbody tr td{
    padding:8px 14px !important;
    border-bottom:1px solid #2d2d2d !important;
    color:#c5c5c5 !important;
    font-size:.82rem !important
}
div[data-testid="stMarkdown"] table tbody tr:last-child td{
    border-bottom:none !important
}
div[data-testid="stMarkdown"] table tbody tr:hover td{
    background:rgba(255,255,255,.04) !important
}

/* ── mbox — BP/BM price cards ── */
.mbox{
    background:#252525 !important;
    border:1px solid #333 !important;
    border-radius:12px !important;
    padding:14px 18px;margin:6px 0;
    transition:border-color .15s,box-shadow .15s;
    box-shadow:0 1px 3px rgba(0,0,0,.3)
}
.mbox:hover{
    border-color:#4a4a4a !important;
    box-shadow:0 3px 10px rgba(0,0,0,.4) !important
}
.ph{
    font-size:1.35rem !important;font-weight:700 !important;
    color:#e5e5e5 !important;letter-spacing:-.4px
}
.sp{font-size:.82rem;color:#9b9b9b;margin-bottom:3px}

/* ── Status badges ── */
.b-bp{background:rgba(35,131,226,.18);color:#60a5fa;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:600;border:1px solid rgba(35,131,226,.3)}
.b-bm{background:rgba(34,197,94,.15);color:#4ade80;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:600;border:1px solid rgba(34,197,94,.25)}
.b-sc{background:rgba(251,191,36,.13);color:#fbbf24;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:600;border:1px solid rgba(251,191,36,.25)}
.b-ok{background:rgba(34,197,94,.15);color:#4ade80;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:600;border:1px solid rgba(34,197,94,.25)}
.b-wn{background:rgba(251,191,36,.13);color:#fbbf24;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:600;border:1px solid rgba(251,191,36,.25)}
/* ── 페이지 내비게이션 (상위: 채워진 필 스트립 / 하위: 밑줄 탭) ── */
.st-key-nav_top div[data-testid="stSegmentedControl"]{margin-top:-4px}
.st-key-nav_top div[data-testid="stButtonGroup"]{
    background:#252525;border:1px solid #333;border-radius:12px;padding:4px;gap:3px;
    box-shadow:0 1px 3px rgba(0,0,0,.35)
}
.st-key-nav_top div[data-testid="stButtonGroup"] button{
    border-radius:9px !important;border:none !important;background:transparent !important;
    color:#9b9b9b !important;font-size:.92rem !important;font-weight:600 !important;
    padding:8px 20px !important;transition:background .15s,color .15s;box-shadow:none !important
}
.st-key-nav_top div[data-testid="stButtonGroup"] button:hover{
    background:rgba(255,255,255,.06) !important;color:#e5e5e5 !important
}
.st-key-nav_top div[data-testid="stButtonGroup"] button[kind="segmented_controlActive"],
.st-key-nav_top div[data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"]{
    background:#2383e2 !important;color:#fff !important;
    box-shadow:0 1px 6px rgba(35,131,226,.45) !important
}
.st-key-nav_top div[data-testid="stButtonGroup"] button p{font-weight:inherit !important;font-size:inherit !important}

.st-key-nav_sub div[data-testid="stSegmentedControl"]{margin-top:2px;margin-bottom:6px}
.st-key-nav_sub div[data-testid="stButtonGroup"]{
    background:transparent;border:none;border-bottom:1px solid #333;border-radius:0;
    padding:0;gap:0;width:100%
}
.st-key-nav_sub div[data-testid="stButtonGroup"] button{
    border:none !important;border-bottom:2px solid transparent !important;border-radius:0 !important;
    background:transparent !important;color:#8a8a8a !important;
    font-size:.8rem !important;font-weight:500 !important;padding:6px 14px 7px !important;
    margin-bottom:-1px;box-shadow:none !important;transition:color .15s,border-color .15s
}
.st-key-nav_sub div[data-testid="stButtonGroup"] button:hover{color:#e5e5e5 !important}
.st-key-nav_sub div[data-testid="stButtonGroup"] button[kind="segmented_controlActive"],
.st-key-nav_sub div[data-testid="stButtonGroup"] button[data-testid="stBaseButton-segmented_controlActive"]{
    color:#e5e5e5 !important;font-weight:600 !important;border-bottom:2px solid #2383e2 !important
}
.st-key-nav_sub div[data-testid="stButtonGroup"] button p{font-weight:inherit !important;font-size:inherit !important}
.nav-crumb{font-size:.72rem;color:#7a7a7a;letter-spacing:.02em;margin:2px 0 0 2px}
.nav-crumb b{color:#c5c5c5;font-weight:600}
.b-ng{background:rgba(239,68,68,.15);color:#f87171;padding:2px 10px;border-radius:20px;font-size:.72rem;font-weight:600;border:1px solid rgba(239,68,68,.25)}

</style>""", unsafe_allow_html=True)

CONFIG_FILE  = os.path.join(os.path.dirname(__file__), "config.json")
_GSHEET_CREDS = os.path.join(os.path.dirname(__file__), "bp-calculator-498206-4308cbd64cba.json")

# ── 로컬 vs 클라우드 감지 ────────────────────────────────────────────────────
# 로컬 인증 파일 있음 → 파일로 인증, Drive를 데이터 저장소로 사용
# 클라우드(Streamlit Cloud) → Streamlit Secrets로 인증, Drive 사용
_HAS_LOCAL_CREDS = os.path.exists(_GSHEET_CREDS)
_IS_CLOUD        = not _HAS_LOCAL_CREDS   # 로컬 인증 파일 없으면 클라우드 모드

# ── 읽기 전용 배포 모드 ──────────────────────────────────────────────────────
# secrets.toml(또는 Streamlit Cloud Secrets)에 `read_only = true` 를 설정한
# 별도 배포본에서만 켜짐. 원본 앱의 secrets에는 이 키가 없으므로 항상 False.
try:
    READ_ONLY = bool(st.secrets.get("read_only", False))
except Exception:
    READ_ONLY = False

if READ_ONLY:
    st.warning(
        "🔒 **읽기 전용 모드** — 모든 저장·삭제·동기화 버튼이 비활성화되어 있습니다. "
        "데이터는 변경되지 않습니다.",
        icon="🔒",
    )
    _ro_orig_button       = st.button
    _ro_orig_form_submit  = st.form_submit_button

    def _ro_button(*args, **kwargs):
        kwargs["disabled"] = True
        _ro_orig_button(*args, **kwargs)
        return False

    def _ro_form_submit(*args, **kwargs):
        kwargs["disabled"] = True
        _ro_orig_form_submit(*args, **kwargs)
        return False

    st.button = _ro_button
    st.form_submit_button = _ro_form_submit

def _get_gcp_creds(scopes):
    """로컬: 인증 JSON 파일 / 클라우드: Streamlit Secrets."""
    from google.oauth2.service_account import Credentials
    import json as _json
    if _HAS_LOCAL_CREDS:
        return Credentials.from_service_account_file(_GSHEET_CREDS, scopes=scopes)
    info = _json.loads(st.secrets["gcp_service_account_json"])
    return Credentials.from_service_account_info(info, scopes=scopes)

def _get_drive_service():
    """Google Drive API 서비스 반환."""
    from googleapiclient.discovery import build
    creds = _get_gcp_creds(["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=creds)


def _download_cfg_raw():
    """Google Drive에서 config.json 을 즉시 내려받아 dict 반환 (캐시 없음)."""
    from googleapiclient.http import MediaIoBaseDownload
    import io
    svc     = _get_drive_service()
    file_id = st.secrets["drive_config_file_id"]
    req     = svc.files().get_media(fileId=file_id)
    buf     = io.BytesIO()
    dl      = MediaIoBaseDownload(buf, req)
    done    = False
    while not done:
        _, done = dl.next_chunk()
    buf.seek(0)
    return json.loads(buf.read().decode("utf-8"))

@st.cache_data(ttl=120, show_spinner=False)
def _load_cfg_drive():
    """config.json (120초 캐시). 앱 내 저장(save_cfg)은 즉시 캐시를 비우므로 본인 작업엔
    항상 최신이 보임. 다른 기기에서 저장한 직후엔 사이드바 '데이터 새로고침' 버튼 사용."""
    return _download_cfg_raw()

def _save_cfg_drive(c):
    """dict를 JSON으로 직렬화해 Google Drive 파일에 덮어씁니다."""
    from googleapiclient.http import MediaInMemoryUpload
    svc     = _get_drive_service()
    file_id = st.secrets["drive_config_file_id"]
    content = json.dumps(c, ensure_ascii=False, indent=2).encode("utf-8")
    media   = MediaInMemoryUpload(content, mimetype="application/json")
    svc.files().update(fileId=file_id, media_body=media).execute()
    _load_cfg_drive.clear()   # Drive 캐시 무효화
    _fifo_lot_trace.clear()   # FIFO 계산 캐시 무효화

def load_cfg():
    """항상 Google Drive에서 로드 (로컬·클라우드 공통 원본)."""
    return _load_cfg_drive()

def save_cfg(c, force=False):
    """항상 Google Drive에 저장 (로컬·클라우드 공통 원본).

    동시 저장 충돌 방지: 저장은 파일 전체를 덮어쓰므로, 두 기기(또는 탭)에서 열어두고
    각각 저장하면 나중 저장이 먼저 저장을 조용히 지운다(캐시 120초 동안 창이 열림).
    cfg['_meta']['rev'] 를 저장마다 1씩 올리고, 저장 직전 Drive의 현재 rev 가 내가
    불러온 rev 와 다르면 저장을 중단하고 새로고침을 안내한다. force=True 는 백업 복원용."""
    if READ_ONLY:
        st.error("🔒 읽기 전용 모드 — 저장이 차단되었습니다.")
        st.stop()
    loaded_rev = int((c.get("_meta") or {}).get("rev") or 0)
    if not force:
        try:
            cur_rev = int((_download_cfg_raw().get("_meta") or {}).get("rev") or 0)
        except Exception:
            cur_rev = loaded_rev          # 확인 실패 시 저장은 진행 (가용성 우선)
        if cur_rev != loaded_rev:
            st.error("다른 기기·탭에서 먼저 저장된 변경이 있어 이번 저장을 중단했습니다 (덮어쓰기 방지). "
                     "사이드바 '데이터 새로고침'을 누른 뒤 방금 입력한 내용을 다시 저장해 주세요.")
            st.stop()
    c["_meta"] = {"rev": loaded_rev + 1, "saved_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}
    _save_cfg_drive(c)
    # 로컬 개발 편의용: Drive와 별도로 로컬 백업 유지
    if _HAS_LOCAL_CREDS and os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False, indent=2)

def bp_price(ni_i,co_i,ni_c,co_c,ni_p,co_p):
    nv=ni_i*(ni_c/100)*ni_p; cv=co_i*(co_c/100)*co_p; t=nv+cv
    return nv,cv,t,t/1000

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
def _valid_date_str(s):
    """'YYYY-MM-DD' 형식이면서 실제 유효한 날짜(연도 1990~2100)인지 검증.
    Python datetime은 연도 1~9999를 다 허용하지만, pandas Timestamp는
    대략 1677~2262년만 지원해 화면에서 표/차트로 변환할 때 범위를 벗어나면
    OutOfBoundsDatetime으로 앱 전체가 죽는다. 업무상 있을 수 없는 연도(오타 등)를
    미리 걸러 이 크래시를 막는다."""
    if not s or not _DATE_RE.match(s):
        return False
    try:
        _d = datetime.strptime(s, "%Y-%m-%d")
        return 1990 <= _d.year <= 2100
    except ValueError:
        return False

# ── 처리 이력 헬퍼 (모듈 레벨 — t_proc / t_pnl 공용) ──────────────────────────
from collections import defaultdict

def _ph_input_kg(rec):
    """투입량 반환 — 저장값 우선, 없으면 output_kg ÷ conversion_rate 역산"""
    if rec.get("input_kg") is not None:   # 0.0도 저장값으로 취급 (falsy-zero 방지)
        return rec["input_kg"]
    out  = rec.get("output_kg", 0) or 0
    conv = rec.get("conversion_rate_pct") or rec.get("conversion_rate")
    return out / (conv / 100) if (out and conv and conv > 0) else 0

def _ph_export_usd(rec, cfg=None):
    """수출비 총액(USD).
    우선순위: ① 배치 직접값(구버전 호환) → ② HBL 수출비 생산량 비례 배분 → ③ 구포맷 per_kg
    """
    # ① 배치에 직접 저장된 값 (구버전 호환)
    if rec.get("export_cost_usd") is not None:
        return float(rec["export_cost_usd"])
    # ② HBL 레벨 수출비 비례 배분
    if cfg and rec.get("shipment_id"):
        ship = next((s for s in cfg.get("shipments", []) if s.get("id") == rec["shipment_id"]), {})
        hbl_eu = float(ship.get("export_cost_usd") or 0)
        if hbl_eu > 0:
            total_out = sum(
                float(r.get("output_kg", 0) or 0)
                for r in cfg.get("processing_history", [])
                if r.get("shipment_id") == rec["shipment_id"]
            )
            rec_out = float(rec.get("output_kg", 0) or 0)
            if total_out > 0 and rec_out > 0:
                return round(hbl_eu * rec_out / total_out, 2)
    # ③ 구포맷 fallback
    per_kg = rec.get("export_cost_per_kg_bp", 0) or 0
    out    = rec.get("output_kg", 0) or 0
    return per_kg * out

def _inv_moving_avg(cfg, scrap_id, as_of_date=None):
    """이동평균 단가·누적 입고량 반환.
    as_of_date: 'YYYY-MM-DD' 또는 'YYYY-MM' — 해당 월 말까지의 입고만 반영.
    반환: (avg_cost, cumulative_qty)  둘 다 None/0 이면 기초재고 미설정.
    """
    inv = cfg.get("raw_material_inventory", {}).get(scrap_id, {})
    op  = inv.get("opening")
    if not op or not op.get("quantity_kg"):
        return None, 0.0

    qty = float(op["quantity_kg"])
    avg = float(op["unit_cost"])
    cutoff = str(as_of_date)[:7] if as_of_date and str(as_of_date).strip() else None  # YYYY-MM 비교

    op_date = (op.get("date") or "")[:10]   # 기초재고 기준일 (YYYY-MM-DD)
    for p in sorted(inv.get("purchases", []), key=lambda x: x.get("date", "")):
        p_raw  = (p.get("date") or "")
        p_date = p_raw[:10]
        if op_date:
            # 입고일이 YYYY-MM(일 미입력)인 경우: 월 단위로만 비교 — 기초재고 이전 월만 제외
            # 입고일이 YYYY-MM-DD(일 포함)인 경우: 전체 날짜로 비교 — 기초재고 당일·이전 제외
            if len(p_raw.strip()) <= 7:
                if p_date[:7] < op_date[:7]:
                    continue   # 기초재고 월보다 이전 월 입고 → 이미 기초재고에 포함
            else:
                if p_date <= op_date:
                    continue   # 기초재고 날짜 이전·당일 입고 → 이미 기초재고에 포함
        if cutoff and p_date[:7] > cutoff:
            break
        pq = float(p.get("quantity_kg") or 0)
        pc = float(p.get("unit_cost")   or 0)
        if pq > 0 and pc > 0:
            avg = (qty * avg + pq * pc) / (qty + pq)
            qty += pq

    return round(avg, 5), round(qty, 3)

def _inv_balance(cfg, scrap_id, ph_list=None, as_of_date=None):
    """창고 실물 잔량 = 누적 입고 − 임가공 출고 − 직접 판매
    dispatch_records·direct_sales 가 실물 반출 기준이므로 이를 차감.
    ph_list 인자는 하위호환용으로 유지하되 계산에는 미사용.
    """
    _, total_in = _inv_moving_avg(cfg, scrap_id, as_of_date)
    dispatched  = sum(float(dr.get("quantity_kg") or 0)
                      for dr in cfg.get("dispatch_records", [])
                      if dr.get("scrap_type_id") == scrap_id)
    direct_sold = sum(float(ds.get("quantity_kg") or 0)
                      for ds in cfg.get("direct_sales", [])
                      if ds.get("scrap_type_id") == scrap_id)
    return round(total_in - dispatched - direct_sold, 3)

def _get_eur_usd(cfg, month=None):
    """월별 EUR/USD 환율 조회.
    month: 'YYYY-MM' — 해당 월 이하 가장 최근 환율 반환.
    등록된 환율이 없으면 기본값 1.10 반환.
    """
    rates = sorted(cfg.get("eur_usd_rates", []), key=lambda x: x["month"])
    if not rates:
        return 1.10
    if not month:
        return float(rates[-1]["rate"])
    match = [r for r in rates if r["month"] <= month]
    return float(match[-1]["rate"]) if match else float(rates[0]["rate"])

def _rec_ref_date(rec, cfg):
    """배치 기준일 결정: batch_date 직접 입력 > 연결 HBL 선적일 순서로 반환 (YYYY-MM-DD or None)."""
    if rec.get("batch_date"):
        return rec["batch_date"][:10]
    ship_id = rec.get("shipment_id", "")
    if ship_id:
        ship = next((s for s in cfg.get("shipments", []) if s.get("id") == ship_id), {})
        return (ship.get("loading_date") or "")[:10] or None
    return None

def _storage_rate_eur(cfg, scrap_id):
    """스크랩 유형별 창고 보관비율 (EUR/톤백/day). 미설정 시 1.5."""
    sc = next((s for s in cfg.get("scrap_types", []) if s.get("id") == scrap_id), {})
    return float(sc.get("storage_rate_eur") or 1.5)

def _ph_storage_cost(rec, cfg):
    """scrap 보관비 자동계산 (수동 storage_days 입력 배치용).
    = 톤백수 × 보관일수 × EUR/톤백/day × EUR/USD
    톤백수: ton_bags 직접 입력 우선, 없으면 투입량 ÷ 510
    storage_days 미입력 시 0 반환.
    """
    days = rec.get("storage_days") or 0
    if not days:
        return 0.0
    inp_kg = _ph_input_kg(rec)
    if inp_kg <= 0:
        return 0.0
    # 톤백: 직접 입력 우선, 없으면 중량 역산
    tb = float(rec.get("ton_bags") or 0) or (inp_kg / 510.0)
    ref_date  = _rec_ref_date(rec, cfg)
    month     = ref_date[:7] if ref_date else None
    eur_rate  = _get_eur_usd(cfg, month)
    stor_rate = _storage_rate_eur(cfg, rec.get("scrap_type_id",""))
    return round(tb * float(days) * stor_rate * eur_rate, 2)

def _cfg_fingerprint(c):
    """config dict의 내용 지문(md5). st.cache_data의 hash_funcs로 사용.
    Streamlit 기본 해셔는 dict를 잎 단위로 순회해 cfg 전체를 매 호출마다 해시하는데,
    측정 결과 호출당 약 16ms로 FIFO 계산(약 3ms)보다 느렸다. json 직렬화+md5는
    약 1ms. 내용이 바뀌면 지문이 바뀌므로 캐시 무효화도 자동으로 정확하다."""
    return hashlib.md5(
        json.dumps(c, sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")
    ).hexdigest()

@st.cache_data(show_spinner=False, hash_funcs={dict: _cfg_fingerprint})
def _fifo_lot_trace(cfg, scrap_id):
    """2단계 FIFO Lot 추적.

    Level 1  입고 Lot 큐 → 전체 출고 이벤트(임가공 출고 + 직접판매) — 날짜순
             각 임가공 출고 이벤트(dispatch_records)에 lot 귀속 정보 부여
    Level 2  임가공 출고 풀(프로세서별) → B/L 배치(processing_history) — 선적일순
             프로세서별 FIFO로 dispatch pool 소진 → 각 B/L에 lot 귀속 전파

    반환: (bl_result, all_events, lot_remaining)
      bl_result    : {shipment_id → {hbl, load_date, input_kg,
                        lots: {lot_label → {qty, amount, unit_cost, lot_date}}}}
      all_events   : 전체 출고 이벤트 목록 (attributions 포함) — 임가공출고 + 직접판매
      lot_remaining: 미소진 Lot 잔량 리스트
    """
    inv = cfg.get("raw_material_inventory", {}).get(scrap_id, {})
    op  = inv.get("opening")
    if not op or not float(op.get("quantity_kg") or 0):
        return {}, [], []

    # ── Lot 큐 구성 (FIFO = 입고일 오름차순) ─────────────────────────────────
    op_date = (op.get("date") or "")[:10]
    lots = []
    if float(op.get("quantity_kg") or 0) > 0:
        op_qty = float(op["quantity_kg"])
        op_tb  = float(op.get("ton_bags") or 0)
        # kg/백: 기초재고에 ton_bags 입력된 경우 사용, 없으면 510 역산
        op_kpb = op_qty / op_tb if op_tb > 0 else 510.0
        lots.append({
            "label":      f"기초재고 ({op_date})",
            "date":       op_date,
            "unit_cost":  float(op.get("unit_cost") or 0),
            "remain":     op_qty,
            "kg_per_bag": op_kpb,
        })
    for p in sorted(inv.get("purchases", []), key=lambda x: x.get("date", "")):
        p_raw  = (p.get("date") or "")
        p_date = p_raw[:10]
        if op_date:
            if len(p_raw.strip()) <= 7:
                if p_date[:7] < op_date[:7]:
                    continue   # 기초재고 월보다 이전 월 → 기초재고에 이미 포함
            else:
                if p_date <= op_date:
                    continue   # 기초재고 날짜 이전·당일 → 기초재고에 이미 포함
        pq = float(p.get("quantity_kg") or 0)
        if pq > 0:
            p_tb  = float(p.get("ton_bags") or 0)
            p_kpb = pq / p_tb if p_tb > 0 else 510.0
            lots.append({
                "label":      f"{p_date[:7]} 매입 ({p_date})",
                "date":       p_date,
                "unit_cost":  float(p.get("unit_cost") or 0),
                "remain":     pq,
                "kg_per_bag": p_kpb,
            })

    proc_map = {p["id"]: p for p in cfg.get("processors", [])}
    ship_map = {s["id"]: s for s in cfg.get("shipments", [])}

    # ── 출고 이벤트 구성 (임가공 출고 + 직접 판매) ───────────────────────────
    outflow_events = []
    for dr in cfg.get("dispatch_records", []):
        if dr.get("scrap_type_id") != scrap_id:
            continue
        qty = float(dr.get("quantity_kg") or 0)
        if qty <= 0:
            continue
        proc = proc_map.get(dr.get("processor_id", ""), {})
        outflow_events.append({
            "id":           dr.get("id", ""),
            "type":         "임가공출고",
            "date":         (dr.get("date") or "9999-12-31")[:10],
            "qty":          qty,
            "processor_id": dr.get("processor_id", ""),
            "processor":    proc.get("name", "—"),
            "notes":        dr.get("notes", ""),
        })
    for ds in cfg.get("direct_sales", []):
        if ds.get("scrap_type_id") != scrap_id:
            continue
        qty = float(ds.get("quantity_kg") or 0)
        if qty <= 0:
            continue
        outflow_events.append({
            "id":           ds.get("id", ""),
            "type":         "직접판매",
            "date":         (ds.get("date") or "9999-12-31")[:10],
            "qty":          qty,
            "processor_id": "",
            "processor":    "—",
            "notes":        ds.get("notes", ""),
        })
    outflow_events.sort(key=lambda x: (x["date"], x["type"]))

    # ── Level 1: lot 큐 → 출고 이벤트 FIFO 소진 ─────────────────────────────
    lot_q = [dict(l) for l in lots]
    all_events     = []
    dispatch_pool  = []   # 임가공 출고 이벤트에 lot_q_remain 부여한 풀

    for ev in outflow_events:
        need  = ev["qty"]
        attrs = []
        while need > 0.001 and lot_q:
            lot  = lot_q[0]
            take = min(lot["remain"], need)
            attrs.append({
                "lot_label":  lot["label"],
                "lot_date":   lot["date"],
                "unit_cost":  lot["unit_cost"],
                "qty":        round(take, 3),
                "amount":     round(take * lot["unit_cost"], 2),
                "kg_per_bag": lot.get("kg_per_bag", 510.0),  # Lot 고유 kg/백 비율 전파
            })
            lot["remain"] -= take
            need           -= take
            if lot["remain"] < 0.001:
                lot_q.pop(0)
        if need > 0.001:
            attrs.append({
                "lot_label":  "⚠️ 미기록 재고 (입고 이력 확인 필요)",
                "lot_date":   "",
                "unit_cost":  None,
                "qty":        round(need, 3),
                "amount":     None,
                "kg_per_bag": 510.0,
            })
        all_events.append({**ev, "attributions": attrs})

        if ev["type"] == "임가공출고":
            dispatch_pool.append({
                "dispatch_id":  ev["id"],
                "date":         ev["date"],
                "processor_id": ev["processor_id"],
                "total_qty":    ev["qty"],
                # lot 잔량 서브큐 (Level 2에서 소진) — kg_per_bag 포함
                "lot_q_remain": [
                    {"lot_label": a["lot_label"], "lot_date": a.get("lot_date",""),
                     "unit_cost": a["unit_cost"],  "remain":   a["qty"],
                     "kg_per_bag": a.get("kg_per_bag", 510.0)}
                    for a in attrs if (a.get("qty") or 0) > 0.001
                ],
            })

    # ── Level 2: 프로세서별 dispatch 풀 → B/L 배치 FIFO 소진 ─────────────────
    # 프로세서별 dispatch 큐 구성 (이미 날짜 오름차순)
    dq_by_proc = defaultdict(list)
    for de in dispatch_pool:
        dq_by_proc[de["processor_id"]].append(de)

    # processing_history → 선적일 오름차순 정렬
    ph_records = []
    for rec in cfg.get("processing_history", []):
        if rec.get("scrap_type_id") != scrap_id:
            continue
        inp_kg = float(rec.get("input_kg") or 0)
        if inp_kg <= 0:
            continue
        ship      = ship_map.get(rec.get("shipment_id", ""), {})
        load_date = (ship.get("loading_date") or "")[:10] or "9999-12-31"
        ph_records.append({
            "id":           rec.get("id", ""),
            "shipment_id":  rec.get("shipment_id", ""),
            "hbl":          ship.get("hbl", "미연결"),
            "load_date":    load_date,
            "input_kg":     inp_kg,
            "processor_id": rec.get("processor_id", ""),
        })
    ph_records.sort(key=lambda x: x["load_date"])

    bl_result = {}
    for ph in ph_records:
        dq      = dq_by_proc[ph["processor_id"]]   # mutable reference
        need    = ph["input_kg"]
        bl_lots = {}  # lot_label → {qty, amount, unit_cost, lot_date}

        while need > 0.001 and dq:
            de     = dq[0]
            avail  = sum(lr["remain"] for lr in de["lot_q_remain"])
            if avail < 0.001:
                dq.pop(0)
                continue
            take_dp = min(avail, need)
            dp_need = take_dp
            # dispatch 내부 lot 서브큐 FIFO 소진
            for lr in de["lot_q_remain"]:
                if dp_need < 0.001:
                    break
                lot_take = min(lr["remain"], dp_need)
                if lot_take > 0:
                    k = lr["lot_label"]
                    if k not in bl_lots:
                        bl_lots[k] = {"lot_label": k, "lot_date": lr.get("lot_date",""),
                                      "unit_cost": lr["unit_cost"], "qty": 0.0, "amount": 0.0,
                                      "storage_cost": 0.0, "storage_days_wsum": 0.0}
                    bl_lots[k]["qty"] += lot_take
                    if lr["unit_cost"] is not None:
                        bl_lots[k]["amount"] += round(lot_take * lr["unit_cost"], 4)
                    # ── 창고 보관비 자동 계산 (Lot 입고일 → 임가공 출고일) ─────
                    _ls_raw = lr.get("lot_date", "") or ""
                    _ll_chk = lr.get("lot_label", "")
                    # 기초재고 Lot은 기준일을 시작점으로 사용 (이전 보관비는 sunk cost)
                    if "기초재고" in _ll_chk:
                        _stor_start = op_date
                    elif len(_ls_raw) >= 10:
                        _stor_start = _ls_raw[:10]
                    elif len(_ls_raw) >= 7:
                        _stor_start = _ls_raw[:7] + "-15"  # 월만 있으면 중간값 근사
                    else:
                        _stor_start = ""
                    _sc_val = 0.0
                    _ldays  = 0
                    if _stor_start and de["date"] and de["date"] != "9999-12-31":
                        try:
                            _ldays = max(0, (
                                datetime.strptime(de["date"], "%Y-%m-%d") -
                                datetime.strptime(_stor_start, "%Y-%m-%d")
                            ).days)
                            _eur_r  = _get_eur_usd(cfg, de["date"][:7])
                            _stor_r = _storage_rate_eur(cfg, scrap_id)
                            # 톤백: Lot 고유 kg/백 비율 사용 (기초재고·입고 Lot별로 다를 수 있음)
                            _kpb   = lr.get("kg_per_bag", 510.0)
                            _tb    = lot_take / _kpb if _kpb > 0 else lot_take / 510.0
                            _sc_val = round(_tb * _ldays * _stor_r * _eur_r, 4)
                        except Exception:
                            _sc_val = 0.0
                            _ldays  = 0   # 예외 시 days도 초기화 — wsum 고아 누적 방지
                    bl_lots[k]["storage_cost"] += _sc_val
                    bl_lots[k]["storage_days_wsum"] += _ldays * lot_take  # 가중합: 나중에 평균 산출용
                    # ──────────────────────────────────────────────────────────
                    lr["remain"] -= lot_take
                    dp_need      -= lot_take
            de["lot_q_remain"] = [lr for lr in de["lot_q_remain"] if lr["remain"] > 0.001]
            need -= take_dp
            if not de["lot_q_remain"]:
                dq.pop(0)

        if need > 0.001:
            k = "⚠️ 출고 기록 미매칭 (출고 기록 탭에서 임가공 출고 입력 필요)"
            bl_lots[k] = {"lot_label": k, "lot_date": "", "unit_cost": None,
                          "qty": round(need, 3), "amount": None, "storage_cost": 0.0}

        sid = ph["shipment_id"] or f"__no_ship__{ph['id']}"
        if sid not in bl_result:
            bl_result[sid] = {"hbl": ph["hbl"], "load_date": ph["load_date"],
                              "input_kg": 0.0, "lots": {}, "storage_cost": 0.0}
        bl_result[sid]["input_kg"] += ph["input_kg"]
        for k, v in bl_lots.items():
            if k not in bl_result[sid]["lots"]:
                bl_result[sid]["lots"][k] = {**v}
            else:
                bl_result[sid]["lots"][k]["qty"] += v["qty"]
                if v.get("unit_cost") is not None:
                    bl_result[sid]["lots"][k]["amount"] = (
                        bl_result[sid]["lots"][k].get("amount", 0) + v.get("amount", 0))
                bl_result[sid]["lots"][k]["storage_cost"] = (
                    bl_result[sid]["lots"][k].get("storage_cost", 0.0) + v.get("storage_cost", 0.0))
                bl_result[sid]["lots"][k]["storage_days_wsum"] = (
                    bl_result[sid]["lots"][k].get("storage_days_wsum", 0.0) + v.get("storage_days_wsum", 0.0))
        bl_result[sid]["storage_cost"] += sum(v.get("storage_cost", 0.0) for v in bl_lots.values())

    return bl_result, all_events, lot_q   # lot_q: 미소진 잔량


def _get_contract_for_shipment(cfg, ship_id):
    """선적건 ID로 연결된 계약 반환.
    1순위: 선적건에 직접 저장된 linked_contract_id
    2순위: contract_allocations 명시적 배분
    3순위: buyer + 선적일 범위로 활성 계약 자동 매칭 (단, 후보가 1건일 때만)
    """
    ship = next((s for s in cfg.get("shipments", []) if s.get("id") == ship_id), None)
    if ship and ship.get("linked_contract_id"):
        ct = next((c for c in cfg.get("contracts", [])
                   if c.get("id") == ship["linked_contract_id"]), None)
        if ct:
            return ct
    alloc = next((a for a in cfg.get("contract_allocations", [])
                  if a.get("shipment_id") == ship_id), None)
    if alloc:
        return next((c for c in cfg.get("contracts", [])
                     if c.get("id") == alloc.get("contract_id")), None)
    # fallback: 선적건에서 buyer_id + loading_date 조회
    ship = next((s for s in cfg.get("shipments", []) if s.get("id") == ship_id), None)
    if not ship:
        return None
    buyer_id = ship.get("buyer_id", "")
    ld = ship.get("loading_date", "")
    candidates = [
        c for c in cfg.get("contracts", [])
        if c.get("buyer_id") == buyer_id
        and c.get("contract_status", "active") == "active"
        and (not c.get("start_date") or (ld and ld >= c.get("start_date", "")))
        and (not c.get("end_date")   or (ld and ld <= c.get("end_date",   "9999-12-31")))
    ]
    if not candidates and buyer_id:
        # 날짜 범위 무시하고 활성 계약 재탐색
        candidates = [c for c in cfg.get("contracts", [])
                      if c.get("buyer_id") == buyer_id
                      and c.get("contract_status", "active") == "active"]
    # 후보가 정확히 1건일 때만 자동 적용 (복수면 ambiguous → None)
    if len(candidates) == 1:
        return candidates[0]
    return None

def _settle_terms(contract, buyer):
    """계약·매입사 마스터에서 유효 정산 조건 반환.
    계약에 값이 있으면 계약 우선, 없으면 매입사 기본값 사용.
    반환: {ni_payable, co_payable(소수 형태), prov_pct, prov_idx, final_idx}

    주의: buyer.ni_payable 은 소수(0.725)로 저장,
          contract.ni_payable_pct 는 퍼센트(72.5)로 저장 → /100 정규화
    """
    ct  = contract or {}
    b   = buyer or {}
    _ni_pct = ct.get("ni_payable_pct")
    _co_pct = ct.get("co_payable_pct")
    return {
        "ni_payable": float(_ni_pct) / 100.0 if _ni_pct else float(b.get("ni_payable", 0) or 0),
        "co_payable": float(_co_pct) / 100.0 if _co_pct else float(b.get("co_payable", 0) or 0),
        "prov_pct":   float(ct.get("prov_pct")   or 100.0),
        "prov_idx":   ct.get("prov_index_basis",  "prov"),
        "final_idx":  ct.get("final_index_basis", "final"),
    }

def _eff_content(buyer_val, our_val, src):
    """최종정산에 적용할 함유량(%) — 정산 기준(매입사값/당사값/평균)에 따라 선택.
    '평균'은 소수 2자리 반올림. 선적 정산 폼·재계산·요약표가 모두 이 한 함수를 쓴다."""
    buyer_val = float(buyer_val or 0)
    our_val   = float(our_val or 0)
    return {"매입사값": buyer_val, "당사값": our_val,
            "평균": round((buyer_val + our_val) / 2, 2)}.get(src, buyer_val)

def _resolve_idx_month(basis, loading_date, prov_month, final_month):
    """INDEX 기준월 결정. basis: 'prov'|'final'|'loading'."""
    if basis == "loading":
        ld = (loading_date or "")[:7]
        return ld or prov_month
    if basis == "final":
        return final_month
    if basis == "prov":
        return prov_month
    # YYYY-MM 고정월 지정인 경우 그대로 반환
    if basis and len(basis) == 7 and basis[4] == "-":
        return basis
    return prov_month  # fallback


def _hm_for(cfg, buyer):
    """매입사별 INDEX 이력 {월: row} 딕셔너리 반환.
    매입사가 '자체 INDEX' 사용으로 설정된 경우 index_history_alt[buyer_id]만 참조
    (표준 INDEX와 섞지 않음 — 해당 월이 없으면 미등록으로 취급).
    그 외에는 표준 index_history 사용."""
    b = buyer or {}
    if b.get("custom_index") and b.get("id"):
        alt = cfg.get("index_history_alt", {}).get(b["id"], [])
        return {h["month"]: h for h in alt}
    return {h["month"]: h for h in cfg.get("index_history", [])}


def _recompute_final_settlement(cfg, s, fallback_index=None):
    """저장된 선적건 데이터 기준으로 '지금 저장하면 나올' 최종정산액을 재계산.
    final_amount_usd 스냅샷과 비교해 재계산 필요 여부를 판단할 때 사용.
    반환: 계산 불가(계약/INDEX월 미비) 시 None, 가능하면 확정산 금액(float).

    fallback_index=(ni, co): Final월 INDEX가 아직 없을 때 이 값으로 대신 계산
    (현금흐름 전망의 '추정치' 용도 — 확정 계산에는 절대 사용하지 말 것).
    """
    buyers = {b["id"]: b for b in cfg.get("buyers", [])}
    b = buyers.get(s.get("buyer_id", ""), {})
    hm_all = _hm_for(cfg, b)   # 매입사별 INDEX 예외(custom_index) 반영
    final_month = s.get("final_month", "—")
    if not final_month or final_month == "—" or final_month not in hm_all:
        if fallback_index is None:
            return None
        # Final월 INDEX 미등록 → 추정 INDEX로 대체해 계속 진행
        final_month = None
    ct = _get_contract_for_shipment(cfg, s.get("id", ""))
    st_terms = _settle_terms(ct, b)
    if final_month is None:
        # 추정 모드: fallback_index를 그대로 사용
        ni_index, co_index = fallback_index
    else:
        ld = s.get("loading_date", "")
        prov_month = s.get("prov_month", "—")
        final_idx_month = _resolve_idx_month(st_terms["final_idx"], ld, prov_month, final_month)
        if final_idx_month not in hm_all:
            final_idx_month = final_month
        fm_data = hm_all[final_idx_month]
        ni_index, co_index = fm_data["ni_index"], fm_data["co_index"]

    default_ni = float(b.get("ni_content", 0) or 0)
    default_co = float(b.get("co_content", 0) or 0)
    buyer_ni = float(s.get("buyer_ni_content") or default_ni)
    buyer_co = float(s.get("buyer_co_content") or default_co)
    eff_ni = _eff_content(buyer_ni, default_ni, s.get("ni_content_src", "매입사값"))
    eff_co = _eff_content(buyer_co, default_co, s.get("co_content_src", "매입사값"))

    _, _, _, final_pkg_raw = bp_price(ni_index, co_index,
                                       eff_ni, eff_co,
                                       st_terms["ni_payable"], st_terms["co_payable"])
    weight_kg = float(s.get("weight_kg", 0) or 0)
    moisture  = float(s.get("moisture_pct") or 0)
    final_w   = weight_kg * (1 - moisture / 100)
    rbm = b.get("round_price_before_moisture", False)
    price = round(final_pkg_raw, 2) if rbm else final_pkg_raw
    return round(price * final_w, 2)


def _prov_invoice_calc(cfg, s):
    """가정산 Invoice 계산값 = 가정산 단가(소수 2자리) × 선적 중량. 계산 불가 시 None.
    입력된 invoice_usd 와 비교해 오타·INDEX 기준월 오류를 잡는 데 쓴다."""
    buyers = {b["id"]: b for b in cfg.get("buyers", [])}
    b  = buyers.get(s.get("buyer_id", ""), {})
    pm = s.get("prov_month", "—")
    if not b or not pm or pm == "—":
        return None
    hm = _hm_for(cfg, b)
    terms = _settle_terms(_get_contract_for_shipment(cfg, s.get("id", "")), b)
    m   = _resolve_idx_month(terms["prov_idx"], s.get("loading_date", ""), pm, pm)
    row = hm.get(m) or hm.get(pm)
    if not row:
        return None
    _, _, _, pkg = bp_price(row["ni_index"], row["co_index"],
                            b.get("ni_content", 0), b.get("co_content", 0),
                            terms["ni_payable"], terms["co_payable"])
    return round(round(pkg, 2) * float(s.get("weight_kg", 0) or 0), 2)


# ── 차트 공통 스타일 (plotly) — 색 규칙: BP 파랑 / BM 초록 / 흑자 초록 / 적자 빨강 / 총계 보라 ──
_C_BP, _C_BM, _C_POS, _C_NEG, _C_TOT, _C_LINE = "#2383e2", "#22c55e", "#4ade80", "#ef4444", "#8b5cf6", "#f59e0b"
_C_COST = {"원료 매입비": "#6b7280", "임가공비(순)": "#a16207", "수출비": "#0e7490", "보관비": "#7c3aed"}
_GRID = "rgba(255,255,255,0.07)"

def _fig_style(fig, height=300, title=None, legend=True, y_fmt="$,.0f", top=None):
    """모든 plotly 차트에 같은 배경·격자·글꼴·여백·범례를 적용한다."""
    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(size=13, color="#e5e5e5"), x=0, xanchor="left") if title else None,
        margin=dict(l=10, r=10, t=(top if top is not None else (48 if title else 30)), b=10),
        plot_bgcolor="#1e1e1e", paper_bgcolor="#252525",
        font=dict(color="#c5c5c5", size=11),
        showlegend=legend,
        legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        xaxis_title="", yaxis_title="",
        hoverlabel=dict(bgcolor="#2a2a2a", bordercolor="#444", font=dict(color="#e5e5e5", size=11)),
    )
    fig.update_xaxes(showgrid=False, tickfont=dict(size=10, color="#c5c5c5"), zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor=_GRID, tickformat=y_fmt, automargin=True,
                     tickfont=dict(size=10, color="#c5c5c5"), zeroline=False)
    return fig

def _fig_monthly_pnl(rows, height=320, title=None):
    """월별 손익 구성 차트: 매출은 위로, 비용 4종은 아래로 쌓고 실질 손익을 선으로 겹친다.
    rows: [{"월", "매출(BP)", "원료 매입비", "임가공비(순)", "수출비", "보관비", "실질 손익"}]"""
    import plotly.graph_objects as go
    _x = [r["월"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=_x, y=[r["매출(BP)"] for r in rows], name="매출(BP)", marker_color=_C_BP,
                         hovertemplate="%{x}<br>매출 $%{y:,.0f}<extra></extra>"))
    for _k, _c in _C_COST.items():
        fig.add_trace(go.Bar(x=_x, y=[-(r.get(_k) or 0) for r in rows], name=_k, marker_color=_c,
                             hovertemplate="%{x}<br>" + _k + " $%{y:,.0f}<extra></extra>"))
    _real = [r["실질 손익"] for r in rows]
    fig.add_trace(go.Scatter(
        x=_x, y=_real, name="실질 손익", mode="lines+markers+text",
        line=dict(color=_C_LINE, width=2),
        marker=dict(size=8, color=[_C_POS if v >= 0 else _C_NEG for v in _real],
                    line=dict(color="#1e1e1e", width=1)),
        text=[f"${v:+,.0f}" for v in _real], textposition="top center",
        textfont=dict(size=9, color=_C_LINE),
        hovertemplate="%{x}<br>실질 손익 $%{y:+,.0f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color="rgba(255,255,255,0.25)", line_width=1)
    fig.update_layout(barmode="relative", bargap=0.35)
    _fig_style(fig, height=height, title=title)
    fig.update_xaxes(type="category")   # "YYYY-MM" 문자열을 날짜로 해석하지 않게
    return fig


def _cc_money(*cols, dec=2, kg=(), pct=(), perkg=(), small=()):
    """st.dataframe column_config 빌더 — 숫자형을 유지해 정렬이 되게 하고 표기만 통일한다."""
    cc = {}
    for c in cols:
        cc[c] = st.column_config.NumberColumn(c, format=f"$%,.{dec}f")
    for c in kg:
        cc[c] = st.column_config.NumberColumn(c, format="%,.0f")
    for c in pct:
        cc[c] = st.column_config.NumberColumn(c, format="%+.2f%%")
    for c in perkg:
        cc[c] = st.column_config.NumberColumn(c, format="$%.4f")
    for c in small:
        cc[c] = st.column_config.NumberColumn(c, format="%d", width="small")
    return cc

def status_badge(s):
    m={"provisional":("Provisional 정산","b-wn"),"final":("최종정산","b-ok"),"paid":("입금완료","b-bp")}
    lbl,cls=m.get(s,("—","b-ng"))
    return f'<span class="{cls}">{lbl}</span>'

def _kpi_card(label, value, sub="", val_color="#e5e5e5", left_border=""):
    _bl    = f"border-left:3px solid {left_border};" if left_border else ""
    _sub_h = (f'<div style="font-size:.75rem;color:#9b9b9b;margin-top:6px;line-height:1.4">'
              f'{sub}</div>') if sub else ""
    return (f'<div style="background:#2a2a2a;border:1px solid #383838;border-radius:12px;'
            f'padding:16px 18px;{_bl}box-shadow:0 2px 8px rgba(0,0,0,.4);'
            f'margin-bottom:4px">'
            f'<div style="font-size:.75rem;color:#9b9b9b;margin-bottom:8px;font-weight:500">{label}</div>'
            f'<div style="font-size:1.5rem;font-weight:700;color:{val_color};'
            f'letter-spacing:-.5px;line-height:1.15">{value}</div>'
            f'{_sub_h}</div>')

def _kpi_card_badge(label, badge_txt, badge_color, value, sub="",
                    val_color="#e5e5e5", left_border=""):
    _bl  = f"border-left:3px solid {left_border};" if left_border else ""
    _bdg = (f'<span style="background:{badge_color}26;color:{badge_color};padding:1px 8px;'
            f'border-radius:20px;font-size:.68rem;font-weight:600;'
            f'border:1px solid {badge_color}44;margin-left:7px;'
            f'vertical-align:middle">{badge_txt}</span>') if badge_txt else ""
    _sub_h = (f'<div style="font-size:.75rem;color:#9b9b9b;margin-top:6px;line-height:1.4">'
              f'{sub}</div>') if sub else ""
    return (f'<div style="background:#2a2a2a;border:1px solid #383838;border-radius:12px;'
            f'padding:16px 18px;{_bl}box-shadow:0 2px 8px rgba(0,0,0,.4);'
            f'margin-bottom:4px">'
            f'<div style="font-size:.75rem;color:#9b9b9b;margin-bottom:8px;font-weight:500">'
            f'{label}{_bdg}</div>'
            f'<div style="font-size:1.5rem;font-weight:700;color:{val_color};'
            f'letter-spacing:-.5px;line-height:1.15">{value}</div>'
            f'{_sub_h}</div>')

def _conv_rate_for(cfg, scrap_id, processor_id=None):
    """전환율(%)과 그 출처 반환. 우선순위: 처리 이력 실적 평균 → 임가공사 계약 조건 → 기본 80%.
    (예전엔 실적이 없으면 조용히 80%를 가정했음 — 출처를 함께 돌려줘 화면에 표시한다.)"""
    rates = [float(r["conversion_rate_pct"])
             for r in cfg.get("processing_history", [])
             if r.get("scrap_type_id") == scrap_id and r.get("conversion_rate_pct")
             and (processor_id is None or r.get("processor_id") == processor_id)]
    if rates:
        return round(sum(rates) / len(rates), 1), "실적"
    for p in cfg.get("processors", []):
        if processor_id and p.get("id") != processor_id:
            continue
        cv = (p.get("conditions", {}).get(scrap_id, {}) or {}).get("conversion_rate")
        if cv:
            return float(cv), "계약"
    return 80.0, "기본값"

def _avg_conv_rate(cfg, scrap_id):
    """스크랩 유형별 전환율(%) — _conv_rate_for 의 값만 (하위호환)."""
    return _conv_rate_for(cfg, scrap_id)[0]

def _finished_goods_kg(cfg, scrap_id=None, processor_id=None):
    """완제품(BP/BM) 재고 추정(kg) = 선적건에 연결되지 않은 배치의 생산량 합.
    배치가 HBL에 연결되는 순간 '선적됨'으로 보므로, 미연결 배치 생산량이 곧
    창고에 쌓인 완제품이다. scrap_id/processor_id 로 범위를 좁힐 수 있다."""
    valid_sids = {s.get("id") for s in cfg.get("shipments", [])}
    total = 0.0
    for r in cfg.get("processing_history", []):
        if scrap_id and r.get("scrap_type_id") != scrap_id:
            continue
        if processor_id and r.get("processor_id") != processor_id:
            continue
        sid = r.get("shipment_id", "")
        if sid and sid in valid_sids:
            continue
        total += float(r.get("output_kg", 0) or 0)
    return total

def _sga_totals(cfg):
    """저장된 월별 간접 판관비·기타 원가 합계 (USD). 반환: (판관비 합, 기타 합)."""
    rows = cfg.get("sga_monthly", [])
    return (sum(float(r.get("sga") or 0) for r in rows),
            sum(float(r.get("other") or 0) for r in rows))

def _at_processor_raw_kg(cfg, scrap_id, processor_id=None):
    """임가공사에 있는 미처리 원료 추정량(kg) = 출하 누계 − 처리 이력 투입 누계."""
    def _pr_ok(pid): return processor_id is None or pid == processor_id
    dispatched = sum(
        float(dr.get("quantity_kg") or 0)
        for dr in cfg.get("dispatch_records", [])
        if dr.get("scrap_type_id") == scrap_id and _pr_ok(dr.get("processor_id"))
    )
    processed = sum(
        _ph_input_kg(r)
        for r in cfg.get("processing_history", [])
        if r.get("scrap_type_id") == scrap_id and _pr_ok(r.get("processor_id"))
    )
    return max(0.0, dispatched - processed)

def _ship_in_period(ship, start, end):
    ld = ship.get("loading_date", "")
    if not ld:
        return False
    return (not start or ld >= start) and ld <= end

def _contract_metrics(cfg, contract):
    """계약 한 건의 이행 현황 지표 dict 반환."""
    contract_id = contract.get("id", "")
    buyer_id  = contract.get("buyer_id", "")
    scrap_id  = contract.get("scrap_type_id", "")
    qty_mt    = float(contract.get("contract_qty_mt") or 0)
    tol       = float(contract.get("tolerance_pct") or 0)
    def _norm_date(d, is_end=False):
        if not d: return d
        d = d.strip()
        if len(d) == 7:
            return d + ("-31" if is_end else "-01")
        return d
    start = _norm_date(contract.get("start_date", ""))
    end   = _norm_date(contract.get("end_date", "") or "9999-12-31", is_end=True) or "9999-12-31"
    _shipments  = cfg.get("shipments", [])
    ship_map    = {s["id"]: s for s in _shipments if s.get("id")}
    all_allocs  = cfg.get("contract_allocations", [])
    ct_allocs   = [a for a in all_allocs if a.get("contract_id") == contract_id]
    _buyer_scrap_contract_ids = {
        c["id"] for c in cfg.get("contracts", [])
        if buyer_id and c.get("buyer_id") == buyer_id
        and c.get("scrap_type_id") == scrap_id
    }
    _buyer_has_any_alloc = any(
        a for a in all_allocs
        if a.get("contract_id") in _buyer_scrap_contract_ids
    )
    oop_alloc_kg = 0.0   # 계약 기간 밖 선적일의 명시적 배분량 (안내용)
    if ct_allocs:
        # 명시적 배분은 사용자가 계약 귀속을 직접 지정한 것 — 선적일이 계약
        # 기간 밖이어도 집계에 포함한다 (협의 물량). 기간 필터는 자동 매칭
        # fallback에만 적용. 기간 밖 물량은 oop_alloc_mt로 반환해 UI에서 안내.
        shipped_kg = sum(float(a.get("allocated_kg") or 0) for a in ct_allocs)
        oop_alloc_kg = sum(
            float(a.get("allocated_kg") or 0)
            for a in ct_allocs
            if not _ship_in_period(ship_map.get(a.get("shipment_id",""), {}), start, end)
        )
    elif _buyer_has_any_alloc:
        shipped_kg = 0.0
    else:
        shipped_kg = sum(
            float(s.get("weight_kg") or 0)
            for s in _shipments
            if s.get("buyer_id") == buyer_id
            and _ship_in_period(s, start, end)
        )
    shipped_mt  = shipped_kg / 1000
    min_mt      = qty_mt * (1 - tol / 100)
    max_mt      = qty_mt * (1 + tol / 100)
    fulfill_pct = (shipped_mt / qty_mt * 100) if qty_mt else 0
    remaining_mt = max(0.0, min_mt - shipped_mt)
    _ct_proc_id    = contract.get("processor_id") or None
    conv, conv_src = _conv_rate_for(cfg, scrap_id, _ct_proc_id)
    _, _, _lot_rem = _fifo_lot_trace(cfg, scrap_id)
    warehouse_raw_kg  = sum(lot.get("remain", 0) for lot in _lot_rem)
    warehouse_bp_mt   = warehouse_raw_kg * conv / 100 / 1000
    at_proc_raw_kg = _at_processor_raw_kg(cfg, scrap_id, _ct_proc_id)
    at_proc_bp_mt  = at_proc_raw_kg * conv / 100 / 1000
    finished_bp_mt = _finished_goods_kg(cfg, scrap_id, _ct_proc_id) / 1000   # 미연결 배치 = 창고 완제품
    total_avail_mt = warehouse_bp_mt + at_proc_bp_mt + finished_bp_mt
    if shipped_mt >= min_mt:
        status = "complete"
    elif total_avail_mt >= remaining_mt:
        status = "ok"
    else:
        status = "short"
    return {
        "shipped_mt": shipped_mt, "qty_mt": qty_mt, "min_mt": min_mt, "max_mt": max_mt,
        "fulfill_pct": fulfill_pct, "remaining_mt": remaining_mt, "conv_pct": conv,
        "warehouse_raw_kg": warehouse_raw_kg, "warehouse_bp_mt": warehouse_bp_mt,
        "at_proc_raw_kg": at_proc_raw_kg, "at_proc_bp_mt": at_proc_bp_mt,
        "total_avail_mt": total_avail_mt, "status": status,
        "oop_alloc_mt": oop_alloc_kg / 1000,
        "finished_bp_mt": finished_bp_mt, "conv_src": conv_src,
    }

# ── 손익 엔진 (손익·시나리오 페이지 · 요약 보고서 · 엑셀 보고서 공용) ─────────────────
# 예전엔 원료단가·자동 창고비 결정 함수가 손익·시나리오 페이지 안에서 정의되고, 요약
# 보고서와 엑셀이 '그 탭이 먼저 실행됐다'는 전제로 그 이름을 빌려 썼다.
# 여기로 올려 세 곳이 같은 함수를 쓰고, 탭 실행 순서에 의존하지 않게 한다.
def _pnl_context(cfg):
    """FIFO 원가·자동 창고비 사전 계산과 원료단가/보관비 결정 함수 묶음."""
    ph_all  = cfg.get("processing_history", [])
    inv_cfg = cfg.get("raw_material_inventory", {})
    dr_sc   = {dr.get("scrap_type_id") for dr in cfg.get("dispatch_records", [])}
    sc_ids  = {r.get("scrap_type_id", "") for r in ph_all
               if r.get("scrap_type_id")
               and inv_cfg.get(r.get("scrap_type_id", ""), {}).get("opening")
               and r.get("scrap_type_id") in dr_sc}
    rmc_map, stor_map = {}, {}          # (scrap_id, ship_id) → $/kg  /  USD
    for sc in sc_ids:
        bl, _, _ = _fifo_lot_trace(cfg, sc)
        for sid, d in bl.items():
            lots = d.get("lots", {})
            q = sum(v["qty"]    for v in lots.values() if v.get("unit_cost") is not None)
            a = sum(v["amount"] for v in lots.values() if v.get("unit_cost") is not None)
            if q > 0:
                rmc_map[(sc, sid)] = a / q
            stor_map[(sc, sid)] = d.get("storage_cost", 0.0)
    inp_total = defaultdict(float)      # 동일 (scrap, shipment) 내 비례 배분용
    for r in ph_all:
        inp_total[(r.get("scrap_type_id", ""), r.get("shipment_id", ""))] += _ph_input_kg(r)

    def key(rec):
        return (rec.get("scrap_type_id", ""),
                rec.get("shipment_id", "") or f"__no_ship__{rec.get('id','')}")

    def auto_storage(rec):
        """FIFO 자동 창고비 — 수동 storage_days 없는 배치의 fallback (입고량 비례 배분)."""
        sc, sid = rec.get("scrap_type_id", ""), rec.get("shipment_id", "")
        total = stor_map.get((sc, sid), 0.0)
        if total <= 0:
            return 0.0
        it, ir = inp_total.get((sc, sid), 0.0), _ph_input_kg(rec)
        return round(total * (ir / it), 4) if it > 0 else 0.0

    def eff_storage(rec):
        m = _ph_storage_cost(rec, cfg)
        return m if m else auto_storage(rec)

    def rmc_fifo(rec, default_rmc=0.0):
        """원료단가 결정 (FIFO 우선). 반환: (단가, 출처)"""
        fifo = rmc_map.get(key(rec))
        if fifo is not None:
            return fifo, "FIFO"
        stored = rec.get("raw_material_cost_per_kg")
        if stored is not None:
            return float(stored), "수동"
        avg, _ = _inv_moving_avg(cfg, rec.get("scrap_type_id", ""), _rec_ref_date(rec, cfg))
        if avg is not None:
            return avg, "이동평균"
        if default_rmc > 0:
            return default_rmc, "기본값"
        return 0.0, "—"

    def rmc_mavg(rec, default_rmc=0.0):
        """원료단가 결정 (이동평균 우선). 반환: (단가, 출처)"""
        avg, _ = _inv_moving_avg(cfg, rec.get("scrap_type_id", ""), _rec_ref_date(rec, cfg))
        if avg is not None:
            return avg, "이동평균"
        stored = rec.get("raw_material_cost_per_kg")
        if stored is not None:
            return float(stored), "수동"
        fifo = rmc_map.get(key(rec))
        if fifo is not None:
            return fifo, "FIFO"
        if default_rmc > 0:
            return default_rmc, "기본값"
        return 0.0, "—"

    return {"rmc_map": rmc_map, "stor_map": stor_map, "inp_total": inp_total,
            "sc_ids": sc_ids, "key": key, "auto_storage": auto_storage,
            "eff_storage": eff_storage, "rmc_fifo": rmc_fifo, "rmc_mavg": rmc_mavg}

def _batch_pnl_rows(cfg, ctx, rmc_mode="FIFO 우선", default_rmc=0.0):
    """배치별 손익 레코드 (관리회계 기준: 스크랩 매각·재매입 상계 → 임가공비(순)).
    월별/HBL별/매입사별/임가공사별 집계는 이 결과를 _pnl_agg 로 합산만 한다."""
    ship_m  = {s["id"]: s for s in cfg.get("shipments", [])}
    buyer_m = {b["id"]: b for b in cfg.get("buyers", [])}
    proc_m  = {p["id"]: p for p in cfg.get("processors", [])}
    sc_m    = {s["id"]: s for s in cfg.get("scrap_types", [])}
    pick    = ctx["rmc_mavg"] if rmc_mode == "이동평균 우선" else ctx["rmc_fifo"]
    rows = []
    for r in cfg.get("processing_history", []):
        sid = r.get("shipment_id", "")
        sh  = ship_m.get(sid, {})
        b   = buyer_m.get(r.get("buyer_id") or sh.get("buyer_id", ""), {})
        out = float(r.get("output_kg", 0) or 0)
        inp = _ph_input_kg(r)
        rmc, rmc_src = pick(r, default_rmc)
        stor = ctx["eff_storage"](r)
        rows.append({
            "rec": r, "sid": sid, "ship": sh, "hbl": sh.get("hbl", "—"),
            "month": (sh.get("loading_date") or "")[:7],
            "buyer": b, "buyer_lbl": f"{b.get('name','?')} ({b.get('product','?')})",
            "product": (b.get("product") or "").upper(),
            "proc_id": r.get("processor_id", ""),
            "proc_nm": proc_m.get(r.get("processor_id", ""), {}).get("name", "—"),
            "scrap_id": r.get("scrap_type_id", ""),
            "sc_nm": sc_m.get(r.get("scrap_type_id", ""), {}).get("name", "—"),
            "out": out, "inp": inp,
            "bp":  float(r.get("bp_sale_per_kg", 0) or 0) * out,
            "pf":  float(r.get("processing_fee_per_kg", 0) or 0) * inp,
            "sc_rev": float(r.get("scrap_sale_per_kg", 0) or 0) * inp,
            "eu":  _ph_export_usd(r, cfg),
            "raw": rmc * inp, "rmc": rmc, "rmc_src": rmc_src,
            "stor": stor,
            "stor_src": "수동" if _ph_storage_cost(r, cfg) else ("FIFO 자동" if stor else "—"),
        })
    return rows

def _pnl_agg(rows, key_fn):
    """_batch_pnl_rows 결과를 key_fn 기준으로 합산. 값: bp/pf/eu/raw/stor/sc_rev/out/inp/cnt"""
    agg = defaultdict(lambda: {"bp": 0.0, "pf": 0.0, "eu": 0.0, "raw": 0.0, "stor": 0.0,
                               "sc_rev": 0.0, "out": 0.0, "inp": 0.0, "cnt": 0})
    for x in rows:
        a = agg[key_fn(x)]
        for k in ("bp", "pf", "eu", "raw", "stor", "sc_rev", "out", "inp"):
            a[k] += x[k]
        a["cnt"] += 1
    return agg

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.spinner("데이터 불러오는 중..."):     # 캐시 히트 시엔 표시되지 않음
    cfg = load_cfg()

# ── 기존 배치 스크랩 매각단가 일괄 기본값 적용 (미설정 배치만) ─────────────
if not READ_ONLY:
    _mig_buyers = {b["id"]: b for b in cfg.get("buyers", [])}
    _mig_ships  = {s["id"]: s for s in cfg.get("shipments", [])}
    _mig_changed = False
    for _mrec in cfg.get("processing_history", []):
        if _mrec.get("scrap_sale_per_kg"):
            continue  # 이미 설정된 배치는 건너뜀
        _mbid = (_mrec.get("buyer_id","") or
                 _mig_ships.get(_mrec.get("shipment_id",""), {}).get("buyer_id",""))
        _mprod = _mig_buyers.get(_mbid, {}).get("product","").upper()
        if "BP" in _mprod:
            _mrec["scrap_sale_per_kg"] = 5.5
            _mig_changed = True
        elif "BM" in _mprod:
            _mrec["scrap_sale_per_kg"] = 3.2
            _mig_changed = True
    if _mig_changed:
        save_cfg(cfg)
# ─────────────────────────────────────────────────────────────────────────────

# ── 선적건 날짜 필드 정합성 정리 (오타 등으로 깨진 값 → 공란 처리) ─────────
if not READ_ONLY:
    _dmig_changed = False
    for _dship in cfg.get("shipments", []):
        for _dfield in ("loading_date", "etd", "eta"):
            _dval = _dship.get(_dfield, "")
            if _dval and not _valid_date_str(_dval):
                _dship[_dfield] = ""
                _dmig_changed = True
    # 계약 상태가 None/빈칸이면 'active' 로 정규화 — 조회 코드가 .get("contract_status","active")
    # 로 기본값을 주지만 키가 None 으로 저장돼 있으면 기본값이 안 먹어 계약이 통째로 무시됐음
    for _cmig in cfg.get("contracts", []):
        if not _cmig.get("contract_status"):
            _cmig["contract_status"] = "active"
            _dmig_changed = True
    if _dmig_changed:
        save_cfg(cfg)
# ─────────────────────────────────────────────────────────────────────────────

hist_opts = [h["month"] for h in sorted(cfg.get("index_history",[]),key=lambda x:x["month"],reverse=True)]

# NI/CO: 가장 최근 INDEX 이력 자동 적용 (사이드바 입력 제거)
_latest_idx = sorted(cfg.get("index_history", []), key=lambda x: x["month"], reverse=True)
NI = _latest_idx[0]["ni_index"] if _latest_idx else 17093.18
CO = _latest_idx[0]["co_index"] if _latest_idx else 56598.72

with st.sidebar:
    st.title("현황")

    # ── 환율 — INDEX·환율·판관비 서브페이지에 저장된 최근 월 USD/KRW 를 기본값으로, 세션에서 덮어쓰기 가능 ──
    _xr_rates = sorted(cfg.get("usd_krw_rates", []), key=lambda x: x["month"])
    _xr_dflt  = float(_xr_rates[-1]["rate"]) if _xr_rates else 1380.0
    XR = st.number_input("💱 USD / KRW", value=_xr_dflt, step=1.0, format="%.0f", key="xr_input",
                         help=("INDEX·환율·판관비 서브페이지 " + _xr_rates[-1]["month"] + " 등록값") if _xr_rates else "미등록 — 기본값 1,380")
    st.divider()

    # ── 요약 한 줄 (경고·재고 상세는 홈의 할 일 패널로 일원화) ──
    _sb_ships  = cfg.get("shipments", [])
    _sb_nosett = sum(1 for s in _sb_ships if not s.get("status","") or s.get("status") == "provisional")
    st.caption(f"선적 {len(_sb_ships)}건 · 미확정 {_sb_nosett}건")
    _sb_meta = cfg.get("_meta") or {}
    if _sb_meta.get("saved_at"):
        st.caption(f"마지막 저장 {_sb_meta['saved_at'][:16].replace('T', ' ')} (rev {_sb_meta.get('rev', 0)})")

    if _latest_idx:
        st.caption(f"INDEX 기준: {_latest_idx[0]['month']}  Ni \\${NI:,.0f} / Co \\${CO:,.0f}")

    # ── 수동 새로고침 ────────────────────────────────────────────────────────
    # 캐시 TTL(config 120초/문서 600초) 내에 다른 기기에서 저장된 변경을
    # 즉시 반영해야 할 때 사용. 본인 저장은 자동으로 캐시가 비워지므로 불필요.
    st.divider()
    if st.button("데이터 새로고침", use_container_width=True,
                 help="Google Drive에서 최신 데이터를 다시 불러옵니다"):
        _load_cfg_drive.clear()
        _fifo_lot_trace.clear()
        st.rerun()

st.title("BP / BM 재고·손익 관리")

# ── 페이지 내비게이션 ─────────────────────────────────────────────────────────
# st.tabs 는 보이지 않는 탭의 코드까지 매 조작마다 전부 실행한다(스타일 표 40여 개·
# 차트·손익 집계). 선택한 페이지의 코드만 실행하도록 세그먼트 컨트롤로 전환.
_PAGES = ["홈", "선적·계약", "손익·시나리오", "재고·임가공", "마스터·동기화"]
PG_HOME, PG_SHIP, PG_PNL, PG_STOCK, PG_MASTER = _PAGES
# URL ?page=슬러그&sub=서브페이지 로 북마크·공유할 수 있고, 새로고침해도 현재 위치가 유지된다.
_PAGE_SLUGS = dict(zip(_PAGES, ["home", "ship", "pnl", "stock", "master"]))
_SLUG_PAGES = {v: k for k, v in _PAGE_SLUGS.items()}
_SLUG_PAGES.update({  # 구 페이지 슬러그 호환
    "report": PG_HOME, "price": PG_PNL, "sens": PG_PNL, "freight": PG_MASTER,
    "contract": PG_SHIP, "settings": PG_MASTER,
})
if "main_nav" not in st.session_state:
    _qp_page = _SLUG_PAGES.get(str(st.query_params.get("page", "")), None)
    if _qp_page:
        st.session_state["main_nav"] = _qp_page
_nav_kw = {} if "main_nav" in st.session_state else {"default": _PAGES[0]}
def _nav_box(key):
    """CSS 타깃용 키 컨테이너 (구버전 Streamlit은 key 미지원 → 일반 컨테이너)."""
    try:
        return st.container(key=key)
    except TypeError:
        return st.container()
with _nav_box("nav_top"):
    try:
        _page = st.segmented_control("페이지", _PAGES, key="main_nav", selection_mode="single",
                                     label_visibility="collapsed", **_nav_kw)
    except AttributeError:   # 구버전 Streamlit
        _page = st.radio("페이지", _PAGES, horizontal=True, key="main_nav", label_visibility="collapsed")
if not _page:
    _page = _PAGES[0]
if st.query_params.get("page") != _PAGE_SLUGS[_page]:
    st.query_params["page"] = _PAGE_SLUGS[_page]

# ── 서브 페이지 (페이지별 2단계 내비게이션) — 선택한 서브 페이지의 코드만 실행된다 ──
SUB_SHIP, SUB_CONTRACT = "선적 정산", "계약 이행"
SUB_PNL_SUM, SUB_PNL_UNIT, SUB_PNL_TH, SUB_PNL_DS = "손익 요약", "HBL·매입사·임가공사별", "이론 마진", "직접 판매"
SUB_PRICE, SUB_SENS = "단가 계산", "민감도"
SUB_INOUT, SUB_PROC = "원료 입출고", "임가공사·배치"
SUB_BUYER, SUB_SCRAP, SUB_FWD, SUB_INDEX, SUB_SYNC = "매입사", "스크랩 유형", "포워더 운임", "INDEX·환율·판관비", "동기화·백업"
_SUBS = {
    PG_SHIP:   [SUB_SHIP, SUB_CONTRACT],
    PG_PNL:    [SUB_PNL_SUM, SUB_PNL_UNIT, SUB_PNL_TH, SUB_PNL_DS, SUB_PRICE, SUB_SENS],
    PG_STOCK:  [SUB_INOUT, SUB_PROC],
    PG_MASTER: [SUB_BUYER, SUB_SCRAP, SUB_FWD, SUB_INDEX, SUB_SYNC],
}
_sub = None
if _page in _SUBS:
    _sub_key = f"sub_nav_{_PAGE_SLUGS[_page]}"
    _sub_qp  = str(st.query_params.get("sub", ""))
    if _sub_key not in st.session_state and _sub_qp in _SUBS[_page]:
        st.session_state[_sub_key] = _sub_qp
    _sub_kw = {} if _sub_key in st.session_state else {"default": _SUBS[_page][0]}
    with _nav_box("nav_sub"):
        try:
            _sub = st.segmented_control("구분", _SUBS[_page], key=_sub_key, selection_mode="single",
                                        label_visibility="collapsed", **_sub_kw)
        except AttributeError:
            _sub = st.radio("구분", _SUBS[_page], horizontal=True, key=_sub_key, label_visibility="collapsed")
    if not _sub:
        _sub = _SUBS[_page][0]
    st.markdown(f'<div class="nav-crumb">{_page} &rsaquo; <b>{_sub}</b></div>', unsafe_allow_html=True)
    if st.query_params.get("sub") != _sub:
        st.query_params["sub"] = _sub
elif "sub" in st.query_params:
    del st.query_params["sub"]

active_buyers = [b for b in cfg["buyers"] if b.get("active",True)]
active_procs  = [p for p in cfg.get("processors",[]) if p.get("active",True)]
active_scraps = [s for s in cfg.get("scrap_types",[]) if s.get("active",True)]
buyer_opts    = {f"{b['name']} ({b['product']})": b["id"] for b in cfg["buyers"]}   # 선적·임가공사 탭 공용


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — BP/BM 매각 단가
# ══════════════════════════════════════════════════════════════════════════════
if _page == PG_PNL and _sub == SUB_PRICE:
    st.subheader("BP/BM 매각 단가 계산")
    with st.expander("Metal INDEX ($/ton)", expanded=False):
        _bp_ref = st.selectbox("이력 불러오기", ["최신값 자동"] + hist_opts, key="bp_idx_ref")
        if _bp_ref == "최신값 자동":
            _bp_ni, _bp_co = NI, CO
        else:
            _hm2 = {h["month"]: h for h in cfg.get("index_history", [])}
            _bp_ni = _hm2[_bp_ref]["ni_index"] if _bp_ref in _hm2 else NI
            _bp_co = _hm2[_bp_ref]["co_index"] if _bp_ref in _hm2 else CO
        _bic1, _bic2 = st.columns(2)
        _bp_ni = _bic1.number_input("Ni INDEX (LME)", value=_bp_ni, step=10.0, format="%.2f", key="bp_ni")
        _bp_co = _bic2.number_input("Co INDEX (MB Rotterdam)", value=_bp_co, step=10.0, format="%.2f", key="bp_co")
    if not active_buyers: st.warning("매입사가 없습니다.")
    else:
        f1,f2=st.columns(2)
        with f1: fp=st.multiselect("품목",["BP","BM"],default=["BP","BM"],key="bp_fp")
        with f2:
            nm=sorted(set(b["name"] for b in active_buyers))
            fb=st.multiselect("매입사",nm,default=nm,key="bp_fb")
        show=[b for b in active_buyers if b["product"] in fp and b["name"] in fb]
        if show:
            rows=[]
            for b in show:
                nv,cv,tot,pkg=bp_price(_bp_ni,_bp_co,b["ni_content"],b["co_content"],b["ni_payable"],b["co_payable"])
                rows.append({"매입사":b["name"],"품목":b["product"],
                    "Ni 함유량":b["ni_content"],"Co 함유량":b["co_content"],
                    "Ni 지불율":b["ni_payable"],"Co 지불율":b["co_payable"],
                    "Ni Value($/ton)":round(nv,2),"Co Value($/ton)":round(cv,2),
                    "단가($/ton)":round(tot,2),"단가($/kg)":round(pkg,5),
                    "단가(원/ton)":round(tot*XR,0),"단가(원/kg)":round(pkg*XR,2)})
            _MAX_CARD_COLS = 4
            _pairs = list(zip(show, rows))
            for _ci in range(0, len(_pairs), _MAX_CARD_COLS):
                _chunk = _pairs[_ci:_ci + _MAX_CARD_COLS]
                _cols = st.columns(len(_chunk))
                for i, (b, r) in enumerate(_chunk):
                  with _cols[i]:
                    bd=f'<span class="b-{"bp" if b["product"]=="BP" else "bm"}">{b["product"]}</span>'
                    st.markdown(f"#### {b['name']}  {bd}",unsafe_allow_html=True)
                    st.markdown(f"""<div class="mbox"><div class="sp">매각 단가</div>
                      <div class="ph">${r['단가($/kg)']:.4f} / kg</div>
                      <div class="sp">${r['단가($/ton)']:,.2f} / ton</div></div>
                    <div class="mbox"><div class="sp">한화 (@{XR:,.0f})</div>
                      <div class="ph">₩{r['단가(원/kg)']:,.2f} / kg</div>
                      <div class="sp">₩{r['단가(원/ton)']:,.0f} / ton</div></div>
                    <div class="mbox"><div class="sp">Ni ({b['ni_content']}% × {b['ni_payable']})</div>
                      <div>${r['Ni Value($/ton)']:,.2f}/ton</div>
                      <div class="sp">Co ({b['co_content']}% × {b['co_payable']})</div>
                      <div>${r['Co Value($/ton)']:,.2f}/ton</div></div>""",unsafe_allow_html=True)
            st.divider()
            df=pd.DataFrame(rows)
            st.dataframe(df.style.format({"Ni 함유량":"{:.2f}%","Co 함유량":"{:.2f}%",
                "Ni 지불율":"{:.2f}","Co 지불율":"{:.2f}",
                "Ni Value($/ton)":"${:,.2f}","Co Value($/ton)":"${:,.2f}",
                "단가($/ton)":"${:,.2f}","단가($/kg)":"${:.4f}",
                "단가(원/ton)":"₩{:,.0f}","단가(원/kg)":"₩{:,.2f}"}),
                use_container_width=True,hide_index=True)
            st.download_button("CSV",df.to_csv(index=False,encoding="utf-8-sig"),
                f"BP_BM_{date.today():%Y%m%d}.csv","text/csv")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — 민감도 분석
# ══════════════════════════════════════════════════════════════════════════════
if _page == PG_PNL and _sub == SUB_SENS:
    st.subheader("민감도 분석")
    if not active_buyers: st.warning("매입사가 없습니다.")
    else:
        sb1,sb2=st.columns(2)
        with sb1: sens_b=st.selectbox("매입사",[f"{b['name']} ({b['product']})" for b in active_buyers],key="sens_b")
        with sb2: sens_t=st.selectbox("변동 대상",["Ni INDEX","Co INDEX","Ni + Co 동시"],key="sens_t")
        sel=active_buyers[[f"{b['name']} ({b['product']})" for b in active_buyers].index(sens_b)]
        st.caption(f"기준 — Ni: \\${NI:,.2f} / Co: \\${CO:,.2f}  (최신 INDEX 자동 적용)")
        rng=st.slider("변동 범위 (%)",min_value=-30,max_value=30,value=(-20,20),step=5)
        steps=list(range(rng[0],rng[1]+1,5))
        srows=[]
        for pct in steps:
            f=1+pct/100
            ni_v=NI*f if sens_t in ["Ni INDEX","Ni + Co 동시"] else NI
            co_v=CO*f if sens_t in ["Co INDEX","Ni + Co 동시"] else CO
            _,_,tot,pkg=bp_price(ni_v,co_v,sel["ni_content"],sel["co_content"],sel["ni_payable"],sel["co_payable"])
            srows.append({"변동률":f"{pct:+d}%","Ni INDEX($/ton)":round(ni_v,2),
                "Co INDEX($/ton)":round(co_v,2),"단가($/kg)":round(pkg,5),"단가(원/kg)":round(pkg*XR,2)})
        df_s=pd.DataFrame(srows)

        def hl_base(row):
            if row["변동률"]=="+0%":
                return ["background-color:#1f4e79;color:white" for _ in row]
            return [""]*len(row)

        st.dataframe(df_s.style.apply(hl_base,axis=1).format({
            "Ni INDEX($/ton)":"${:,.2f}","Co INDEX($/ton)":"${:,.2f}",
            "단가($/kg)":"${:.4f}","단가(원/kg)":"₩{:,.2f}"}),
            use_container_width=True,hide_index=True)
        try:
            import plotly.graph_objects as go
            _sx  = [r["변동률"] for r in srows]
            _sy  = [r["단가($/kg)"] for r in srows]
            _fig_s = go.Figure()
            _fig_s.add_trace(go.Scatter(
                x=_sx, y=_sy, mode="lines+markers+text", name="단가($/kg)",
                line=dict(color=_C_BP, width=2), marker=dict(size=7, color=_C_BP),
                text=[f"${v:.2f}" for v in _sy], textposition="top center", textfont=dict(size=9),
                hovertemplate="%{x}<br>$%{y:.4f}/kg<extra></extra>",
            ))
            if "+0%" in _sx:
                _i0 = _sx.index("+0%")
                _fig_s.add_trace(go.Scatter(
                    x=[_sx[_i0]], y=[_sy[_i0]], mode="markers", name="현재 INDEX",
                    marker=dict(size=14, color=_C_LINE, symbol="diamond",
                                line=dict(color="#1e1e1e", width=1)),
                    hovertemplate="현재 INDEX 기준<br>$%{y:.4f}/kg<extra></extra>",
                ))
            st.plotly_chart(_fig_style(_fig_s, height=280, y_fmt="$,.2f",
                                       title=f"{sens_b} — {sens_t} 변동 시 매각 단가"),
                            use_container_width=True)
        except ImportError:
            st.line_chart(df_s.set_index("변동률")[["단가($/kg)"]])

        # ── 임가공비 단가 시나리오 ─────────────────────────────────────────
        st.divider()
        st.markdown("#### 임가공비 단가 시나리오")
        st.caption("임가공사의 임가공비($/kg 투입) 변동이 연간 지출·매출총이익률에 미치는 영향. "
                   "물량·매출·원료비는 처리 이력 실적(관리회계, 판관비 제외) 기준이며 다른 조건은 불변으로 가정합니다.")
        if not active_procs or not cfg.get("processing_history"):
            st.info("임가공사와 처리 이력이 있어야 시나리오를 계산할 수 있습니다.")
        else:
            _sc_c1, _sc_c2, _sc_c3, _sc_c4 = st.columns(4)
            _sc_proc_lbl = _sc_c1.selectbox("임가공사", [p["name"] for p in active_procs], key="sc_proc")
            _sc_proc = next(p for p in active_procs if p["name"] == _sc_proc_lbl)
            _sc_rows = [x for x in _batch_pnl_rows(cfg, _pnl_context(cfg)) if x["proc_id"] == _sc_proc["id"]]
            if not _sc_rows:
                st.info("이 임가공사의 처리 이력이 없습니다.")
            else:
                _sc_inp     = sum(x["inp"] for x in _sc_rows)
                _sc_cur_fee = (sum(x["pf"] for x in _sc_rows) / _sc_inp) if _sc_inp > 0 else 0.0
                _sc_from = _sc_c2.number_input("현재 단가 ($/kg 투입)", value=round(_sc_cur_fee, 4),
                                               step=0.01, format="%.4f", key="sc_from")
                _sc_to   = _sc_c3.number_input("요청 단가 ($/kg 투입)", value=round(_sc_cur_fee + 0.15, 4),
                                               step=0.01, format="%.4f", key="sc_to")
                _sc_step = _sc_c4.number_input("단계 ($/kg)", value=0.05, min_value=0.01, step=0.01,
                                               format="%.2f", key="sc_step")
                _sc_annual = st.toggle("연환산 (실적 개월 수 → 12개월)", value=False, key="sc_annual")
                _sc_months = sorted({x["month"] for x in _sc_rows if x["month"]})
                _sc_scale  = (12.0 / len(_sc_months)) if (_sc_annual and _sc_months) else 1.0
                _sc_rev    = sum(x["bp"]  for x in _sc_rows) * _sc_scale
                _sc_raw    = sum(x["raw"] for x in _sc_rows) * _sc_scale
                _sc_pf0    = sum(x["pf"]  for x in _sc_rows) * _sc_scale
                _sc_inp_s  = _sc_inp * _sc_scale
                _sc_gp_ex  = _sc_rev - _sc_raw            # 임가공비 차감 전 매출총이익
                _sc_out = []
                _f = _sc_from
                while _f <= _sc_to + 1e-9 and len(_sc_out) < 60:
                    _pf = _sc_inp_s * _f
                    _gp = _sc_gp_ex - _pf
                    _sc_out.append({"$/kg 투입": round(_f, 4),
                                    "임가공비 총액": round(_pf, 0),
                                    "증감(현재 대비)": round(_pf - _sc_inp_s * _sc_from, 0),
                                    "매출총이익": round(_gp, 0),
                                    "GP율(%)": round(_gp / _sc_rev * 100, 2) if _sc_rev > 0 else None,
                                    "매출 대비 임가공비(%)": round(_pf / _sc_rev * 100, 2) if _sc_rev > 0 else None})
                    _f = round(_f + _sc_step, 6)
                if not _sc_out:
                    st.warning("요청 단가가 현재 단가보다 낮습니다 — 범위를 확인하세요.")
                else:
                    st.caption(f"기준 물량: 투입 {_sc_inp_s:,.0f} kg · 매출 \\${_sc_rev:,.0f} · 원료비 \\${_sc_raw:,.0f} · "
                               f"실적 임가공비 \\${_sc_pf0:,.0f}"
                               + (f"  (실적 {len(_sc_months)}개월 → 12개월 환산)" if _sc_scale != 1.0 else ""))
                    st.dataframe(pd.DataFrame(_sc_out).style.format(na_rep="—", formatter={
                        "$/kg 투입": "${:.4f}", "임가공비 총액": "${:,.0f}", "증감(현재 대비)": "${:+,.0f}",
                        "매출총이익": "${:,.0f}",
                        "GP율(%)": lambda v: f"{v:.2f}%" if v is not None else "—",
                        "매출 대비 임가공비(%)": lambda v: f"{v:.2f}%" if v is not None else "—",
                    }), use_container_width=True, hide_index=True)
                    # 스크랩 유형별 원가 구성(원료비+임가공비) 중 임가공비 비중
                    _sc_mix = []
                    for _sn, _sv in _pnl_agg(_sc_rows, lambda x: x["sc_nm"]).items():
                        if _sv["inp"] <= 0:
                            continue
                        _raw_pk = _sv["raw"] / _sv["inp"]
                        _mix = {"스크랩": _sn, "원료비 $/kg 투입": f"${_raw_pk:.4f}"}
                        for _r in _sc_out:
                            _fv = _r["$/kg 투입"]
                            _mix[f"@${_fv:.2f}"] = f"{_fv / (_raw_pk + _fv) * 100:.1f}%" if (_raw_pk + _fv) > 0 else "—"
                        _sc_mix.append(_mix)
                    if _sc_mix:
                        st.markdown("**원가 구성(원료비+임가공비) 중 임가공비 비중 — 단가 단계별**")
                        st.dataframe(pd.DataFrame(_sc_mix), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — 선적 정산 추적  (Provisional/Final 비교 통합)
# ══════════════════════════════════════════════════════════════════════════════
if _page == PG_SHIP and _sub == SUB_SHIP:
    st.subheader("선적 정산")
    with st.expander("ℹ️ 정산 프로세스 안내", expanded=False):
        st.markdown("""
**Provisional 정산 (Provisional, M-1)**
선적 후 바이어 도착 전, 전월 INDEX 기준으로 임시 Invoice를 발행합니다.
Ni/Co 지불율과 M-1 INDEX를 적용한 단가로 먼저 대금을 수취합니다.

**최종정산 (Final, M+0)**
바이어가 실제 인수 검사한 함량·중량 확정 후, 선적월 INDEX로 재정산합니다.
Provisional 정산액과의 차액을 추가 수취 또는 반환합니다.

**입금완료 (Paid)**
최종정산 금액까지 모두 수취 완료된 상태입니다.
""")
    shipments = cfg.get("shipments",[])
    buyer_map  = {b["id"]:b for b in cfg["buyers"]}
    buyer_opts = {f"{b['name']} ({b['product']})":b["id"] for b in cfg["buyers"]}

    # ── 요약 메트릭 ──
    if shipments:
        total_wkg   = sum(s.get("weight_kg",0) for s in shipments)
        total_inv   = sum(s.get("invoice_usd",0) for s in shipments)
        prov_cnt    = sum(1 for s in shipments if s.get("status")=="provisional")
        final_cnt   = sum(1 for s in shipments if s.get("status")=="final")
        paid_cnt    = sum(1 for s in shipments if s.get("status")=="paid")
        m1,m2,m3,m4,m5=st.columns(5)
        m1.markdown(_kpi_card("총 선적건", f"{len(shipments)}건"), unsafe_allow_html=True)
        m2.markdown(_kpi_card("총 중량", f"{total_wkg/1000:,.1f} MT"), unsafe_allow_html=True)
        _p_col = "#fb923c" if prov_cnt else "#e5e5e5"
        m3.markdown(_kpi_card("Provisional 정산", f"{prov_cnt}건", val_color=_p_col), unsafe_allow_html=True)
        m4.markdown(_kpi_card("최종정산", f"{final_cnt}건"), unsafe_allow_html=True)
        m5.markdown(_kpi_card("입금완료", f"{paid_cnt}건", val_color="#4ade80"), unsafe_allow_html=True)
        # ── 미완료 알림 ──
        _pend = [s for s in shipments if s.get("status") in ("provisional","final")]
        if _pend:
            _pend_msgs = []
            for _ps in _pend:
                _pb = buyer_map.get(_ps.get("buyer_id",""),{})
                _st_lbl = "🟡 Provisional" if _ps.get("status")=="provisional" else "🟢 최종(미입금)"
                _pend_msgs.append(f"{_st_lbl} **{_ps.get('hbl','—')}** ({_pb.get('name','?')}, {_ps.get('loading_date','?')})")
            st.warning("⚠️ **정산 미완료 건이 있습니다.**\n\n" + "  \n".join(_pend_msgs))

        # ── 매입사별 정산 현황 요약 (입금완료 제외) ──────────────────────────
        _by_buyer_settle = {}
        for _bs in shipments:
            if _bs.get("status") == "paid":
                continue
            _bb = buyer_map.get(_bs.get("buyer_id",""), {})
            _bkey = _bb.get("name","미지정")
            _bst = _settle_terms(_get_contract_for_shipment(cfg, _bs.get("id","")), _bb)
            _b_prov_paid = float(_bs.get("invoice_usd") or 0) * (_bst["prov_pct"] / 100.0)
            _b_snapshot  = _bs.get("final_amount_usd")
            _b_confirmed = float(_b_snapshot) if _b_snapshot else _recompute_final_settlement(cfg, _bs)
            _b_rec = _by_buyer_settle.setdefault(_bkey, {"건수":0,"가정산 수령액":0.0,"확정산 예상액":0.0,"잔액":0.0,"확정_건수":0})
            _b_rec["건수"] += 1
            _b_rec["가정산 수령액"] += _b_prov_paid
            if _b_confirmed is not None:
                _b_net = _b_confirmed - _b_prov_paid + float(_bs.get("other_adj_usd") or 0)
                _b_rec["확정산 예상액"] += _b_confirmed
                _b_rec["잔액"] += _b_net
                _b_rec["확정_건수"] += 1

        if _by_buyer_settle:
            with st.expander("매입사별 정산 현황 (입금완료 제외)", expanded=False):
                _tot_balance = sum(v["잔액"] for v in _by_buyer_settle.values())
                st.markdown(_kpi_card("미확정 정산 잔액 합계",
                                       f"${_tot_balance:+,.0f}",
                                       "양수: 추가 청구 예정 · 음수: 반환 예정 · 확정산액 없는 건은 미포함"),
                            unsafe_allow_html=True)
                _bb_rows = []
                for _bn, _v in sorted(_by_buyer_settle.items(), key=lambda x: -abs(x[1]["잔액"])):
                    _bb_rows.append({
                        "매입사":       _bn,
                        "미완료 건수":  _v["건수"],
                        "가정산 수령액": round(_v["가정산 수령액"], 2),
                        "확정산 예상액": round(_v["확정산 예상액"], 2) if _v["확정_건수"] else None,
                        "잔액":         round(_v["잔액"], 2) if _v["확정_건수"] else None,
                    })
                st.dataframe(
                    pd.DataFrame(_bb_rows).style.format(na_rep="—", formatter={
                        "가정산 수령액": "${:,.2f}",
                        "확정산 예상액": "${:,.2f}",
                        "잔액":         "${:+,.2f}",
                    }),
                    use_container_width=True, hide_index=True,
                )

        # ── 확정 스냅샷 재계산 필요 목록 ──────────────────────────────────────
        _recalc_candidates = []
        for _rs in shipments:
            if _rs.get("status") in ("final", "paid") and _rs.get("final_amount_usd"):
                _live = _recompute_final_settlement(cfg, _rs)
                if _live is not None and abs(_live - float(_rs["final_amount_usd"])) >= 0.01:
                    _recalc_candidates.append((_rs, _live))
        if _recalc_candidates:
            with st.expander(f"재계산 필요 — {len(_recalc_candidates)}건 (저장된 확정액이 현재 계산식과 다름)",
                              expanded=False):
                st.caption("계산식 개선(반올림 순서, 수분공제 방식 등) 이후 저장된 확정 스냅샷이 최신 결과와 어긋난 건입니다.")
                for _rs, _live in _recalc_candidates:
                    _rb = buyer_map.get(_rs.get("buyer_id", ""), {})
                    _diff = _live - float(_rs["final_amount_usd"])
                    _rc1, _rc2 = st.columns([5, 1])
                    _rc1.write(f"**{_rs.get('hbl', '—')}** · {_rb.get('name', '?')}  "
                               f"저장 \\${float(_rs['final_amount_usd']):,.2f} → 현재 \\${_live:,.2f}  "
                               f"(차이 \\${_diff:+,.2f})")
                    if _rc2.button("재계산", key=f"bulk_recalc_{_rs['id']}"):
                        _rs["final_amount_usd"] = _live
                        save_cfg(cfg); st.toast("✅ 재계산 완료"); st.rerun()
                if st.button(f"전체 {len(_recalc_candidates)}건 일괄 재계산", key="bulk_recalc_all"):
                    for _rs, _live in _recalc_candidates:
                        _rs["final_amount_usd"] = _live
                    save_cfg(cfg)
                    st.toast(f"✅ {len(_recalc_candidates)}건 일괄 재계산 완료")
                    st.rerun()

        # ── 확정 상태인데 저장된 확정액이 없는 건 (시트 동기화로 final 전환된 경우 등) ──
        _no_snap = [(_ns, _recompute_final_settlement(cfg, _ns)) for _ns in shipments
                    if _ns.get("status") in ("final", "paid") and not _ns.get("final_amount_usd")]
        _no_snap_ok = [(_s, _v) for _s, _v in _no_snap if _v is not None]
        if _no_snap:
            with st.expander(f"확정액 미확정 — {len(_no_snap)}건 (final/paid 상태이나 저장된 확정액 없음)",
                             expanded=False):
                st.caption("시트 동기화로 상태만 final이 된 건입니다. 화면의 '(추정)' 값을 저장된 확정액으로 확정합니다. "
                           "분석값·수분율·계약 조건이 정확히 입력됐는지 먼저 확인하세요.")
                for _ns, _nv in _no_snap:
                    _nb = buyer_map.get(_ns.get("buyer_id", ""), {})
                    st.write(f"**{_ns.get('hbl','—')}** · {_nb.get('name','?')}  →  "
                             + (f"\\${_nv:,.2f}" if _nv is not None else "계산 불가 (Final월 INDEX·계약 확인)"))
                if _no_snap_ok and st.button(f"계산 가능한 {len(_no_snap_ok)}건 일괄 확정", key="bulk_snap_all"):
                    for _ns, _nv in _no_snap_ok:
                        _ns["final_amount_usd"] = _nv
                    save_cfg(cfg); st.toast(f"✅ {len(_no_snap_ok)}건 확정"); st.rerun()
        st.divider()

    # ── 필터 ──
    sf1,sf2=st.columns(2)
    with sf1: flt_stat=st.multiselect("상태 필터",["provisional","final","paid"],
                                       default=["provisional","final","paid"],key="ship_stat")
    with sf2: flt_buy=st.multiselect("매입사 필터",list(buyer_opts.keys()),
                                      default=list(buyer_opts.keys()),key="ship_buy")

    flt_ids={v for k,v in buyer_opts.items() if k in flt_buy}
    show_ships=[s for s in shipments if s.get("status","provisional") in flt_stat
                and (not s.get("buyer_id") or s.get("buyer_id") in flt_ids)]
    show_ships=sorted(show_ships, key=lambda x: x.get("loading_date","9999"))

    if not show_ships and shipments:
        st.info("필터 조건에 맞는 선적건이 없습니다.")
    elif not shipments:
        st.info("등록된 선적건이 없습니다. 아래에서 추가하세요.")
    else:
        # ── 📅 항차 일정 타임라인 ──────────────────────────────────────────────
        st.markdown("#### 항차 일정")
        _tl = []
        for _si, _s in enumerate(show_ships, 1):
            _b2  = buyer_map.get(_s.get("buyer_id",""), {})
            _ld2 = _s.get("loading_date","") or "미정"
            _eta2= _s.get("eta","") or "TBD"
            _tl.append({
                "No.":    _si,
                "HBL":    _s.get("hbl","—"),
                "매입사": f"{_b2.get('name','?')} ({_b2.get('product','?')})",
                "선적일": _ld2,
                "ETA":    _eta2,
                "중량(kg)": _s.get("weight_kg",0),
                "상태":   {"provisional":"🟡 Provisional","final":"🟢 최종","paid":"🔵 입금"}.get(_s.get("status","provisional"),"—"),
            })
        st.dataframe(pd.DataFrame(_tl), use_container_width=True, hide_index=True,
                     column_config=_cc_money(kg=("중량(kg)",), small=("No.",)))

        # Gantt 차트 — 기본은 미정산(provisional·final)만, 입금완료는 토글
        _g_paid = st.toggle("입금완료 건도 일정에 표시", value=False, key="gantt_paid")
        try:
            import plotly.express as px
            _gantt = []
            for _r in _tl:
                if _r["선적일"] == "미정": continue
                if not _g_paid and _r["상태"].endswith("입금"): continue
                try:
                    _s_dt = datetime.strptime(_r["선적일"], "%Y-%m-%d")
                    _e_dt = (datetime.strptime(_r["ETA"], "%Y-%m-%d")
                             if _r["ETA"] != "TBD" else _s_dt + timedelta(days=60))
                    _gantt.append({
                        "항차":   _r["HBL"],
                        "매입사": _r["매입사"],
                        "ETD":    _s_dt,
                        "ETA":    _e_dt,
                        "상태":   _r["상태"],
                    })
                except: pass
            if _gantt:
                _df_g = pd.DataFrame(_gantt)
                # 막대 안 라벨: 매입사 약칭 + 항해일수
                _df_g["라벨"] = _df_g.apply(
                    lambda r: f"{r['매입사'].split('(')[0].strip()}  "
                              f"({(r['ETA']-r['ETD']).days}일)", axis=1)
                # 상태별 색상 — 색 규칙(가정산 노랑 / 최종 초록 / 입금 파랑)과 통일
                _cmap = {"🟡 Provisional": "#b45309", "🟢 최종": "#15803d", "🔵 입금": "#1d4ed8"}
                _fig  = px.timeline(
                    _df_g, x_start="ETD", x_end="ETA", y="항차",
                    color="상태", text="라벨",
                    hover_name="항차",
                    hover_data={"매입사":True,"ETD":True,"ETA":True,"라벨":False,"상태":False},
                    color_discrete_map=_cmap,
                )
                _today_dt = datetime.today()
                _fig.update_traces(
                    textposition="inside", insidetextanchor="middle",
                    textfont=dict(color="white", size=10),
                    marker_line=dict(color="rgba(255,255,255,0.35)", width=1),
                )
                # 이미 도착(ETA 경과)한 항차는 흐리게
                for _tr in _fig.data:
                    _tr.marker.opacity = [0.45 if _e < _today_dt else 1.0
                                          for _e in pd.to_datetime(_df_g.loc[_df_g["상태"] == _tr.name, "ETA"])]
                _fig.add_vline(
                    x=_today_dt.timestamp()*1000,
                    line_dash="dot", line_color=_C_NEG, line_width=2,
                    annotation_text=f"오늘 {_today_dt.strftime('%m/%d')}",
                    annotation_font=dict(color=_C_NEG, size=10),
                    annotation_position="top left",
                )
                _fig_style(_fig, height=max(220, len(_gantt)*38+90), y_fmt=None)
                _fig.update_yaxes(autorange="reversed", showgrid=True, gridcolor=_GRID,
                                  tickfont=dict(size=11, color="#D0D0E8"))
                _fig.update_xaxes(showgrid=True, gridcolor=_GRID, tickformat="%m/%d")
                st.plotly_chart(_fig, use_container_width=True)
        except ImportError:
            st.caption("plotly 설치 시 Gantt 차트 표시 — `pip install plotly`")

        st.divider()

        # ── 편집할 선적건 선택 — 한 건의 편집 폼만 렌더링 ────────────────────────
        # (예전엔 필터된 모든 선적건의 편집 폼(각 30여 개 위젯)을 전부 그렸음)
        _ed_opts = {}
        for _ei, _es in enumerate(show_ships):
            _eb = buyer_map.get(_es.get("buyer_id",""), {})
            _ed_opts[f"#{_ei+1}  {_es.get('hbl','').strip() or 'HBL미정'}  ·  {_eb.get('name','?')}  ·  "
                     f"{_es.get('loading_date','') or '선적일 미정'}  ·  {_es.get('status','provisional')}"] = _es["id"]
        # 홈 '할 일'의 HBL 링크(?hbl=)로 진입한 경우 해당 선적건을 편집 대상으로 선택
        _qp_hbl = str(st.query_params.get("hbl", "")).strip()
        if _qp_hbl and "ship_edit_sel" not in st.session_state:
            _qp_sid = next((x["id"] for x in show_ships if x.get("hbl","").strip() == _qp_hbl), None)
            _qp_lbl = next((k for k, v in _ed_opts.items() if v == _qp_sid), None)
            if _qp_lbl:
                st.session_state["ship_edit_sel"] = _qp_lbl
        _ed_sel = st.selectbox("편집할 선적건", list(_ed_opts), key="ship_edit_sel")
        _ed_sid = _ed_opts[_ed_sel]

        _ship_id_idx = {sh.get("id"): _ri for _ri, sh in enumerate(shipments)}
        for i,s in enumerate(show_ships):
            if s["id"] != _ed_sid:
                continue
            real_i=_ship_id_idx[s["id"]]
            b=buyer_map.get(s.get("buyer_id"),{})
            hm_all_b=_hm_for(cfg, b)  # 매입사별 INDEX 예외 반영
            buyer_lbl=f"{b.get('name','?')} ({b.get('product','?')})"
            # 상태 텍스트 (expander는 HTML 미지원 → 이모지 사용)
            stat_txt={"provisional":"🟡 Provisional 정산","final":"🟢 최종정산","paid":"🔵 입금완료"}.get(s.get("status","provisional"),"—")
            # 정산 미리보기: 최종정산 확정(final_amount_usd 스냅샷)된 경우에만 표시
            settle_preview=""
            _snapped = s.get("final_amount_usd")
            if _snapped:
                _hdr_st = _settle_terms(_get_contract_for_shipment(cfg, s.get("id","")), b)
                _hdr_prov_paid = float(s.get("invoice_usd") or 0) * (_hdr_st["prov_pct"] / 100.0)
                _hdr_net = float(_snapped) - _hdr_prov_paid + float(s.get("other_adj_usd") or 0)
                settle_preview = f"가정산 \\${_hdr_prov_paid:,.0f}  ·  확정산 \\${_hdr_net:+,.0f}"
            ld_disp   = s.get("loading_date","").strip() or "선적일 미정"
            _eta_raw  = s.get("eta","").strip()
            eta_disp  = _eta_raw[5:] if _eta_raw and len(_eta_raw) >= 7 else (_eta_raw or "TBD")
            _inv_hdr    = f"  ·  \\${float(s.get('invoice_usd') or 0):,.0f}" if s.get("invoice_usd") else ""
            _settle_hdr = f"  ·  {settle_preview}" if settle_preview else ""
            _eu_hdr     = "  ·  수출비 미입력" if not s.get("export_cost_usd") else ""
            hdr = (f"#{i+1}  ·  {stat_txt}"
                   f"  │  {s.get('hbl','—')}  ·  {buyer_lbl}"
                   f"  │  {ld_disp} → ETA {eta_disp}"
                   f"  │  {s.get('weight_kg',0):,.0f} kg{_inv_hdr}{_settle_hdr}{_eu_hdr}")
            with st.expander(hdr,expanded=True):
                # 컨테이너 가중평균 계산기의 '적용' 값 반영 — 위젯이 생성되기 전에
                # session_state에 넣어야 하므로 expander 최상단에서 처리
                _ctr_pend = st.session_state.pop(f"ctr_apply_{real_i}", None)
                if _ctr_pend:
                    st.session_state[f"sh_bni_{real_i}"]   = _ctr_pend["ni"]
                    st.session_state[f"sh_bco_{real_i}"]   = _ctr_pend["co"]
                    st.session_state[f"sh_moist_{real_i}"] = _ctr_pend["moist"]
                # ── 기본 정보 입력 ──
                e1,e2,e3,e4=st.columns(4)
                with e1:
                    new_hbl=st.text_input("HBL",s.get("hbl",""),key=f"sh_hbl_{real_i}")
                    new_inv=st.text_input("Invoice No.",s.get("invoice_no",""),key=f"sh_inv_{real_i}")
                    new_ld =st.text_input("선적일 (YYYY-MM-DD)",s.get("loading_date",""),key=f"sh_ld_{real_i}")
                with e2:
                    cur_b_lbl=[k for k,v in buyer_opts.items() if v==s.get("buyer_id","")]
                    new_b=st.selectbox("매입사",list(buyer_opts.keys()),
                        index=list(buyer_opts.keys()).index(cur_b_lbl[0]) if cur_b_lbl else 0,key=f"sh_buy_{real_i}")
                    new_wkg=st.number_input("선적 중량 (kg)",value=float(s.get("weight_kg",0)),step=1.0,format="%.0f",key=f"sh_wkg_{real_i}")
                    new_iusd=st.number_input("Invoice 총액 (USD)",value=float(s.get("invoice_usd",0)),step=1.0,format="%.2f",key=f"sh_iusd_{real_i}")
                    new_eusd=st.number_input("수출비 (USD)",value=float(s.get("export_cost_usd") or 0),step=1.0,format="%.2f",key=f"sh_eusd_{real_i}",
                        help="Ocean Freight, THC 등 이 선적건 전체 수출비 합계. 배치별 생산량 비례로 자동 배분됩니다.")
                with e3:
                    new_pm=st.selectbox("Provisional 월",["—"]+hist_opts,
                        index=(["—"]+hist_opts).index(s.get("prov_month","—")) if s.get("prov_month","—") in ["—"]+hist_opts else 0,
                        key=f"sh_pm_{real_i}")
                    new_fm=st.selectbox("Final 월",["—"]+hist_opts,
                        index=(["—"]+hist_opts).index(s.get("final_month","—")) if s.get("final_month","—") in ["—"]+hist_opts else 0,
                        key=f"sh_fm_{real_i}")
                    new_stat=st.selectbox("상태",["provisional","final","paid"],
                        index=["provisional","final","paid"].index(s.get("status","provisional")),key=f"sh_stat_{real_i}")
                with e4:
                    new_etd=st.text_input("ETD",s.get("etd",""),key=f"sh_etd_{real_i}")
                    new_eta=st.text_input("ETA",s.get("eta",""),key=f"sh_eta_{real_i}")
                    new_note=st.text_input("비고",s.get("notes",""),key=f"sh_note_{real_i}")

                # ── 계약 연결 ──────────────────────────────────────────────────
                _cur_bid = buyer_opts.get(new_b, s.get("buyer_id",""))
                _buyer_cts = [c for c in cfg.get("contracts", [])
                              if c.get("buyer_id") == _cur_bid
                              and c.get("contract_status","active") == "active"]
                if _buyer_cts:
                    _ct_label_map = {"자동 매칭": ""}
                    for _bc in _buyer_cts:
                        _bc_st = _bc.get("start_date","")[:7]
                        _bc_en = _bc.get("end_date","")[:7]
                        _bc_qty = _bc.get("contract_qty_mt",0)
                        _bc_lbl = f"{_bc_st}~{_bc_en}  {_bc_qty:,.0f}MT  (ID:{_bc.get('id','')})"
                        _ct_label_map[_bc_lbl] = _bc.get("id","")
                    _cur_linked = s.get("linked_contract_id","")
                    _cur_ct_lbl = next((k for k,v in _ct_label_map.items() if v == _cur_linked), "자동 매칭")
                    _ct_sel_col, _ct_info_col = st.columns([3,2])
                    _new_ct_lbl = _ct_sel_col.selectbox(
                        "계약 연결", list(_ct_label_map.keys()),
                        index=list(_ct_label_map.keys()).index(_cur_ct_lbl),
                        key=f"sh_ct_{real_i}",
                        help="'자동 매칭'은 활성 계약이 1건일 때 자동 적용. 복수 계약이면 직접 선택하세요.")
                    new_linked_ct_id = _ct_label_map[_new_ct_lbl]
                    # 선택된(또는 자동 매칭) 계약 조건 미리보기
                    _preview_ct = next((c for c in _buyer_cts if c.get("id") == new_linked_ct_id), None)
                    if not _preview_ct and len(_buyer_cts) == 1:
                        _preview_ct = _buyer_cts[0]
                    if _preview_ct:
                        _pst = _settle_terms(_preview_ct, b)
                        _ct_info_col.caption(
                            f"가정산 {_pst['prov_pct']:.0f}%  ·  "
                            f"Ni {_pst['ni_payable']*100:.1f}%  ·  Co {_pst['co_payable']*100:.1f}%  ·  "
                            f"Prov-INDEX: {_preview_ct.get('prov_index_basis','prov')}  ·  "
                            f"Final-INDEX: {_preview_ct.get('final_index_basis','final')}"
                        )
                else:
                    new_linked_ct_id = s.get("linked_contract_id","")

                # ── 확정산 세부 정보 ──
                st.markdown("---")
                st.markdown("**📊 확정산 상세 (수분·분석값·기타 조정)**")
                sa1,sa2,sa3=st.columns(3)
                with sa1:
                    st.markdown("**수분 공제**")
                    new_moisture=st.number_input("수분 공제율 (%)",
                        value=float(s.get("moisture_pct") or 0),
                        min_value=0.0,max_value=20.0,step=0.1,format="%.2f",
                        key=f"sh_moist_{real_i}")
                    final_weight_disp=new_wkg*(1-new_moisture/100)
                    st.caption(f"정산 중량: **{final_weight_disp:,.1f} kg** ({new_wkg:,.0f} → {final_weight_disp:,.1f})")
                with sa2:
                    st.markdown("**매입사 샘플 분석값**")
                    default_ni=float(s.get("buyer_ni_content") or (b.get("ni_content",0) if b else 0))
                    default_co=float(s.get("buyer_co_content") or (b.get("co_content",0) if b else 0))
                    new_buyer_ni=st.number_input("Ni 분석값 (%)",
                        value=default_ni,step=0.01,format="%.2f",
                        key=f"sh_bni_{real_i}")
                    new_buyer_co=st.number_input("Co 분석값 (%)",
                        value=default_co,step=0.01,format="%.2f",
                        key=f"sh_bco_{real_i}")
                    if b:
                        ni_diff=new_buyer_ni-b.get("ni_content",0)
                        co_diff=new_buyer_co-b.get("co_content",0)
                        st.caption(f"매입사 대비 당사: Ni {ni_diff:+.2f}%p / Co {co_diff:+.2f}%p")
                    if s.get("container_calc"):
                        _ctr_saved_cnt = len(s["container_calc"].get("containers", []))
                        st.caption(f"🧮 컨테이너별 가중평균 계산기로 산출된 값 ({_ctr_saved_cnt}개 컨테이너) — "
                                   f"아래 팝오버에서 원본 입력값 확인 가능")
                    # 최종정산 기준값 선택 (Ni / Co 각각)
                    _src_opts = ["매입사값", "당사값", "평균"]
                    _ni_src = st.selectbox("Ni 정산 기준",  _src_opts,
                        index=_src_opts.index(s.get("ni_content_src","매입사값"))
                              if s.get("ni_content_src") in _src_opts else 0,
                        key=f"sh_ni_src_{real_i}",
                        help="최종정산 단가 계산에 사용할 Ni 함유량 기준")
                    _co_src = st.selectbox("Co 정산 기준",  _src_opts,
                        index=_src_opts.index(s.get("co_content_src","매입사값"))
                              if s.get("co_content_src") in _src_opts else 0,
                        key=f"sh_co_src_{real_i}",
                        help="최종정산 단가 계산에 사용할 Co 함유량 기준")
                    _co_ni = b.get("ni_content",0) if b else 0  # 당사값
                    _co_co = b.get("co_content",0) if b else 0
                    _eff_ni = _eff_content(new_buyer_ni, _co_ni, _ni_src)
                    _eff_co = _eff_content(new_buyer_co, _co_co, _co_src)
                    st.caption(f"적용 Ni: **{_eff_ni:.2f}%** / Co: **{_eff_co:.2f}%**")
                with sa3:
                    st.markdown("**기타 조정**")
                    new_other_adj=st.number_input("기타 조정 (USD)",
                        value=float(s.get("other_adj_usd") or 0),
                        step=1.0,format="%.2f",
                        help="+: 추가 수령 / -: 추가 지급",
                        key=f"sh_adj_{real_i}")
                    new_other_desc=st.text_input("조정 사유",
                        s.get("other_adj_desc",""),
                        key=f"sh_adjd_{real_i}")

                # ── 입금 기록 (실제 입금일·금액 — 채권 Aging·현금 전망에 반영) ──
                st.markdown("**입금 기록**")
                pr1, pr2, pr3, pr4 = st.columns(4)
                new_ppd = pr1.text_input("가정산 입금일 (YYYY-MM-DD)", s.get("prov_paid_date","") or "", key=f"sh_ppd_{real_i}")
                new_ppu = pr2.number_input("가정산 입금액 (USD)", value=float(s.get("prov_paid_usd") or 0),
                                           step=1.0, format="%.2f", key=f"sh_ppu_{real_i}",
                                           help="비어 있으면 미입금으로 봅니다. 예상액은 Invoice × 가정산 비율")
                new_fpd = pr3.text_input("확정산 입금일 (YYYY-MM-DD)", s.get("final_paid_date","") or "", key=f"sh_fpd_{real_i}")
                new_fpu = pr4.number_input("확정산 입금액 (USD)", value=float(s.get("final_paid_usd") or 0),
                                           step=1.0, format="%.2f", key=f"sh_fpu_{real_i}",
                                           help="확정산 청구액(④)으로 실제 입금된 금액. 반환한 경우 음수")

                # ── 컨테이너별 가중평균 계산기 ──────────────────────────────
                with st.popover("컨테이너별 가중평균 계산기"):
                    st.caption("매입사가 컨테이너 단위로 성분분석·정산한 경우: 컨테이너별 값을 "
                               "입력하면 HBL 하나로 반영할 가중평균을 계산합니다. "
                               "'적용'을 누르면 위 분석값·수분율 필드에 채워지고, "
                               "여기 입력한 컨테이너별 원본값도 이 선적건에 함께 저장됩니다. "
                               "잔여 반올림 차이는 기타 조정에 기재하세요.")
                    _ctr_saved = s.get("container_calc", {}).get("containers", [])
                    # 시트 동기화는 컨테이너 1개짜리 HBL에도 container_calc를 저장하므로 최소 1
                    _ctr_n = int(st.number_input("컨테이너 수", min_value=1, max_value=12,
                                                 value=max(1, len(_ctr_saved)) if _ctr_saved else 2,
                                                 step=1, key=f"ctr_n_{real_i}"))
                    _ctr_rows = []
                    for _cj in range(_ctr_n):
                        _cr_saved = _ctr_saved[_cj] if _cj < len(_ctr_saved) else {}
                        _cc1, _cc2, _cc3, _cc4 = st.columns(4)
                        _cw = _cc1.number_input(f"#{_cj+1} 중량(kg)", min_value=0.0, step=1.0,
                                                format="%.0f", value=float(_cr_saved.get("w", 0.0)),
                                                key=f"ctr_w_{real_i}_{_cj}")
                        _cn = _cc2.number_input(f"#{_cj+1} Ni(%)", min_value=0.0, step=0.01,
                                                format="%.2f", value=float(_cr_saved.get("ni", 0.0)),
                                                key=f"ctr_ni_{real_i}_{_cj}")
                        _cc = _cc3.number_input(f"#{_cj+1} Co(%)", min_value=0.0, step=0.01,
                                                format="%.2f", value=float(_cr_saved.get("co", 0.0)),
                                                key=f"ctr_co_{real_i}_{_cj}")
                        _cm = _cc4.number_input(f"#{_cj+1} 수분(%)", min_value=0.0, max_value=20.0,
                                                step=0.01, format="%.2f", value=float(_cr_saved.get("moist", 0.0)),
                                                key=f"ctr_m_{real_i}_{_cj}")
                        _ctr_rows.append((_cw, _cn, _cc, _cm))
                    _ctr_gw = sum(r[0] for r in _ctr_rows)                    # 총 중량
                    _ctr_sw = sum(r[0] * (1 - r[3]/100) for r in _ctr_rows)   # 정산중량 합
                    if _ctr_gw > 0 and _ctr_sw > 0:
                        # Ni/Co는 '정산중량' 가중평균 — 정산액이 함유량에 선형이라
                        # 컨테이너별 합계가 정확히 재현됨 (반올림 차이 제외).
                        # 수분율은 총중량 대비 정산중량으로 역산.
                        _ctr_eni = sum(r[1] * r[0] * (1 - r[3]/100) for r in _ctr_rows) / _ctr_sw
                        _ctr_eco = sum(r[2] * r[0] * (1 - r[3]/100) for r in _ctr_rows) / _ctr_sw
                        _ctr_em  = (1 - _ctr_sw / _ctr_gw) * 100
                        st.markdown(f"가중평균 — Ni **{_ctr_eni:.4f}%** · Co **{_ctr_eco:.4f}%** · "
                                    f"수분 **{_ctr_em:.4f}%**  "
                                    f"(총 {_ctr_gw:,.0f} kg → 정산 {_ctr_sw:,.1f} kg)")
                        if abs(_ctr_gw - new_wkg) > 1:
                            st.caption(f"⚠️ 컨테이너 중량 합({_ctr_gw:,.0f} kg)이 "
                                       f"선적 중량({new_wkg:,.0f} kg)과 다릅니다.")
                        if st.button("분석값·수분율에 적용 + 저장", key=f"ctr_apply_btn_{real_i}"):
                            st.session_state[f"ctr_apply_{real_i}"] = {
                                "ni":    round(_ctr_eni, 4),
                                "co":    round(_ctr_eco, 4),
                                "moist": round(_ctr_em, 4),
                            }
                            cfg["shipments"][real_i]["container_calc"] = {
                                "containers": [{"w": r[0], "ni": r[1], "co": r[2], "moist": r[3]}
                                               for r in _ctr_rows]
                            }
                            save_cfg(cfg)
                            st.rerun()
                    else:
                        st.caption("컨테이너별 중량을 입력하면 가중평균이 계산됩니다.")

                # ── 정산 요약 계산 ──
                # 계약 조건 조회 (계약 있으면 ni/co 지불율·가정산비율·INDEX기준 계약 우선)
                _settle_ct   = _get_contract_for_shipment(cfg, s.get("id",""))
                _st          = _settle_terms(_settle_ct, b)
                _ni_pay      = _st["ni_payable"]
                _co_pay      = _st["co_payable"]
                _prov_pct_val= _st["prov_pct"]
                _prov_idx_b  = _st["prov_idx"]
                _final_idx_b = _st["final_idx"]
                _ld_for_idx  = s.get("loading_date","")

                _snapped_final = s.get("final_amount_usd")

                if b and new_pm!="—":
                    _prov_idx_month = _resolve_idx_month(_prov_idx_b, _ld_for_idx, new_pm, new_pm)
                    if _prov_idx_month not in hm_all_b:
                        _prov_idx_month = new_pm
                    pm_data=hm_all_b.get(_prov_idx_month)
                    if pm_data:
                        _,_,_,_prov_pkg_raw=bp_price(pm_data["ni_index"],pm_data["co_index"],
                            b.get("ni_content",0),b.get("co_content",0),
                            _ni_pay, _co_pay)
                        prov_pkg = round(_prov_pkg_raw, 2)
                    else:
                        prov_pkg = None
                    # Invoice 총액 → Provisional 지급액
                    prov_paid = new_iusd * (_prov_pct_val / 100.0)
                    st.markdown("---")
                    # Invoice 금액 검증 — 가정산 단가 × 중량과 1% 이상 어긋나면 오타·기준월 오류 경고
                    if prov_pkg is not None and new_wkg > 0 and new_iusd > 0:
                        _inv_calc = round(prov_pkg * new_wkg, 2)
                        _inv_gap  = (_inv_calc - new_iusd) / new_iusd * 100
                        if abs(_inv_gap) > 1.0:
                            st.warning(f"Invoice 총액 \\${new_iusd:,.2f}이 가정산 단가 기준 계산값 \\${_inv_calc:,.2f} "
                                       f"(\\${prov_pkg:.2f}/kg × {new_wkg:,.0f} kg)과 {_inv_gap:+.1f}% 차이납니다 — "
                                       "입력 오타 또는 Provisional INDEX 기준월을 확인하세요.")

                    # Provisional 조건 표시
                    if _settle_ct:
                        _ct_hint = []
                        if _settle_ct.get("prov_pct"): _ct_hint.append(f"가정산 {_prov_pct_val:.0f}%")
                        if _settle_ct.get("ni_payable_pct"): _ct_hint.append(f"Ni {_ni_pay*100:.1f}%")
                        if _settle_ct.get("co_payable_pct"): _ct_hint.append(f"Co {_co_pay*100:.1f}%")
                        if _prov_idx_b != "prov": _ct_hint.append(f"INDEX 기준: {_prov_idx_month}")
                        if _ct_hint:
                            st.caption(f"📋 계약 조건 적용: {', '.join(_ct_hint)}")

                    if not pm_data and b.get("custom_index"):
                        st.warning(f"⚠️ {b.get('name','')} 전용 INDEX 이력에 {_prov_idx_month}월 값이 없습니다 — "
                                   f"마스터·동기화 > INDEX·환율·판관비에서 등록하면 아래 단가 계산이 표시됩니다.")

                    _final_idx_month = None
                    fm_data = None
                    if new_fm != "—":
                        _final_idx_month = _resolve_idx_month(_final_idx_b, _ld_for_idx, new_pm, new_fm)
                        if _final_idx_month not in hm_all_b:
                            _final_idx_month = new_fm
                        fm_data = hm_all_b.get(_final_idx_month)

                    if fm_data:
                        # 확정산 계산 (INDEX 값 조회 가능)
                        _,_,_,_final_pkg_raw=bp_price(fm_data["ni_index"],fm_data["co_index"],
                            _eff_ni,_eff_co,
                            _ni_pay, _co_pay)
                        final_pkg = round(_final_pkg_raw, 2)  # 화면 표시용
                        final_w=new_wkg*(1-new_moisture/100)
                        # 매입사에 따라 단가 반올림 시점이 다름: 기본은 원단가 사용, 매입사 설정 시 반올림 단가 사용
                        _rbm = b.get("round_price_before_moisture", False) if b else False
                        final_amt=round((final_pkg if _rbm else _final_pkg_raw)*final_w, 2)
                        index_diff=(final_pkg-prov_pkg) if prov_pkg is not None else None
                        # Final 스냅샷 값 (저장된 값 우선)
                        _display_final = _snapped_final if _snapped_final else final_amt
                        net_settle=_display_final - prov_paid + new_other_adj

                        # ── 정산 흐름 요약 (5 metrics) ──────────────────────
                        st.markdown("**📋 정산 요약**")
                        rs1,rs2,rs3,rs4,rs5=st.columns(5)
                        _inv_per_kg   = new_iusd / new_wkg if new_wkg else 0
                        _final_per_kg = _display_final / final_w if final_w else 0
                        _inv_vs_final = _display_final - new_iusd
                        _inv_vs_final_adj = _inv_vs_final + new_other_adj
                        _net_col  = "#4ade80" if net_settle >= 0 else "#f87171"
                        _diff_col = "#4ade80" if _inv_vs_final >= 0 else "#f87171"
                        _diff_adj_col = "#4ade80" if _inv_vs_final_adj >= 0 else "#f87171"
                        _final_lbl = "③ 최종정산액 (확정)" if _snapped_final else "③ 최종정산액 (계산)"
                        _net_lbl   = "④ 확정산 청구액" if net_settle >= 0 else "④ 확정산 반환액"
                        rs1.markdown(_kpi_card("① Invoice 총액",
                                               f"${new_iusd:,.2f}",
                                               f"단가 ${_inv_per_kg:.2f}/kg  ·  {new_wkg:,.0f} kg"), unsafe_allow_html=True)
                        rs2.markdown(_kpi_card(_final_lbl,
                                               f"${_display_final:,.2f}",
                                               f"Final INDEX {_final_idx_month}  ·  ${final_pkg:.2f}/kg"), unsafe_allow_html=True)
                        rs3.markdown(_kpi_card(_net_lbl,
                                               f"${abs(net_settle):,.2f}",
                                               f"KRW ₩{net_settle*XR:+,.0f}",
                                               val_color=_net_col), unsafe_allow_html=True)
                        rs4.markdown(_kpi_card("Invoice ↔ 최종 차이",
                                               f"${_inv_vs_final:+,.2f}",
                                               f"최종단가 ${_final_per_kg:.2f}/kg",
                                               val_color=_diff_col), unsafe_allow_html=True)
                        rs5.markdown(_kpi_card("Invoice ↔ 최종 차이 (기타조정 반영)",
                                               f"${_inv_vs_final_adj:+,.2f}",
                                               f"기타조정 ${new_other_adj:+,.2f} 포함 · 추가 인보이스 발급액",
                                               val_color=_diff_adj_col), unsafe_allow_html=True)
                        if new_other_adj:
                            st.caption(f"기타 조정: ${new_other_adj:+,.2f}  {new_other_desc or ''}")

                        # 확정 스냅샷이 최신 계산식(반올림 전 원단가) 결과와 다르면 재계산 제안
                        if _snapped_final and abs(_snapped_final - final_amt) >= 0.01:
                            st.warning(
                                f"⚠️ 확정 스냅샷(\\${_snapped_final:,.2f})이 현재 계산식(\\${final_amt:,.2f})과 "
                                f"\\${_snapped_final - final_amt:+,.2f} 차이납니다 — 단가 반올림 방식 개선 이전 값일 수 있습니다."
                            )
                            if st.button("최신 계산식으로 재계산", key=f"sh_recalc_{real_i}"):
                                cfg["shipments"][real_i]["final_amount_usd"] = final_amt
                                save_cfg(cfg); st.toast("✅ 재계산 완료"); st.rerun()

                        # ── 정산 흐름표 ───────────────────────────────────────
                        _prov_pkg_disp   = f"{prov_pkg:.2f}" if prov_pkg is not None else "—"
                        _index_diff_disp = f"{index_diff:+.2f}" if index_diff is not None else "—"
                        _fl_rows = [
                            f"| ① | Invoice 발행 | **\\${new_iusd:,.2f}** | 단가 \\${_inv_per_kg:.2f}/kg · {new_wkg:,.0f} kg |",
                            f"| ② | 가정산 수령 ({_prov_pct_val:.0f}%) | −\\${prov_paid:,.2f} | INDEX {_prov_idx_month} · \\${_prov_pkg_disp}/kg |",
                            f"| | **가정산 후 미수잔액** | **\\${new_iusd - prov_paid:,.2f}** | |",
                            f"| ③ | 최종정산액{'(확정)' if _snapped_final else '(계산)'} | \\${_display_final:,.2f} | INDEX {_final_idx_month} · \\${final_pkg:.2f}/kg · {_ni_src}/{_co_src} |",
                        ]
                        if new_other_adj:
                            _fl_rows.append(f"| | 기타 조정 | \\${new_other_adj:+,.2f} | {new_other_desc or '—'} |")
                        _fl_net_lbl  = "확정산 청구액" if net_settle >= 0 else "확정산 반환액"
                        _fl_net_icon = "🟢 수령 예정" if net_settle >= 0 else "🔴 반환 예정"
                        _fl_rows.append(f"| **④** | **{_fl_net_lbl}** | **\\${net_settle:+,.2f}** | {_fl_net_icon} |")
                        st.markdown("| 단계 | 항목 | 금액 | 비고 |\n|:----:|------|-----:|------|\n" + "\n".join(_fl_rows))

                        # ── Invoice vs 최종 비교표 (Prov/Final INDEX가 모두 조회 가능할 때만) ──
                        if pm_data:
                            _ni_diff  = _eff_ni  - b.get("ni_content", 0)
                            _co_diff  = _eff_co  - b.get("co_content", 0)
                            _idx_ni_d = fm_data["ni_index"] - pm_data["ni_index"]
                            _idx_co_d = fm_data["co_index"] - pm_data["co_index"]
                            _wt_diff  = final_w - new_wkg
                            with st.expander("Invoice ↔ 최종정산 변동 분석", expanded=False):
                                st.markdown(f"""
| 구분 | Invoice 기준 | 최종정산 기준 | 변동 | 비고 |
|------|:------------:|:------------:|:----:|------|
| INDEX 기준월 | {_prov_idx_month} | {_final_idx_month} | — | |
| Ni INDEX | \\${pm_data['ni_index']:,.2f} | \\${fm_data['ni_index']:,.2f} | \\${_idx_ni_d:+,.2f} | /MT |
| Co INDEX | \\${pm_data['co_index']:,.2f} | \\${fm_data['co_index']:,.2f} | \\${_idx_co_d:+,.2f} | /MT |
| Ni 함유량 | {b.get('ni_content',0):.2f}% (당사) | {new_buyer_ni:.2f}% (매입사) · **{round(_eff_ni,2):.2f}%** 적용 | {_ni_diff:+.2f}%p | 기준: {_ni_src} |
| Co 함유량 | {b.get('co_content',0):.2f}% (당사) | {new_buyer_co:.2f}% (매입사) · **{round(_eff_co,2):.2f}%** 적용 | {_co_diff:+.2f}%p | 기준: {_co_src} |
| 정산 중량 | {new_wkg:,.0f} kg | {final_w:,.1f} kg | {_wt_diff:+,.1f} kg | 수분 {new_moisture:.1f}% 공제 |
| 단가 ($/kg) | **\\${_prov_pkg_disp}** | **\\${final_pkg:.2f}** | **\\${_index_diff_disp}** | |
| 정산 합계 | \\${new_iusd:,.2f} | \\${_display_final:,.2f} | **\\${_inv_vs_final:+,.2f}** | |
""")
                        else:
                            st.caption(f"ℹ️ Provisional월({_prov_idx_month}) INDEX 이력이 없어 변동 분석은 생략합니다.")
                    elif _snapped_final:
                        # Final월 INDEX 이력은 없지만 이미 확정된 스냅샷은 그대로 표시 (매입사 자체 INDEX 미등록 등)
                        final_w = new_wkg * (1 - new_moisture / 100)
                        _display_final = float(_snapped_final)
                        net_settle = _display_final - prov_paid + new_other_adj
                        st.markdown("**📋 정산 요약 (확정)**")
                        rs1, rs2, rs3, rs4 = st.columns(4)
                        _inv_per_kg = new_iusd / new_wkg if new_wkg else 0
                        _net_col = "#4ade80" if net_settle >= 0 else "#f87171"
                        _inv_vs_final = _display_final - new_iusd
                        _inv_vs_final_adj = _inv_vs_final + new_other_adj
                        _diff_adj_col = "#4ade80" if _inv_vs_final_adj >= 0 else "#f87171"
                        rs1.markdown(_kpi_card("① Invoice 총액", f"${new_iusd:,.2f}",
                                               f"단가 ${_inv_per_kg:.2f}/kg  ·  {new_wkg:,.0f} kg"), unsafe_allow_html=True)
                        rs2.markdown(_kpi_card("③ 최종정산액 (확정)", f"${_display_final:,.2f}",
                                               f"Final {new_fm}"), unsafe_allow_html=True)
                        _net_lbl = "④ 확정산 청구액" if net_settle >= 0 else "④ 확정산 반환액"
                        rs3.markdown(_kpi_card(_net_lbl, f"${abs(net_settle):,.2f}",
                                               f"KRW ₩{net_settle*XR:+,.0f}", val_color=_net_col), unsafe_allow_html=True)
                        rs4.markdown(_kpi_card("Invoice ↔ 최종 차이 (기타조정 반영)",
                                               f"${_inv_vs_final_adj:+,.2f}",
                                               f"기타조정 ${new_other_adj:+,.2f} 포함 · 추가 인보이스 발급액",
                                               val_color=_diff_adj_col), unsafe_allow_html=True)
                        if new_other_adj:
                            st.caption(f"기타 조정: ${new_other_adj:+,.2f}  {new_other_desc or ''}")
                        st.caption(f"ℹ️ {b.get('name','')} 전용 INDEX 이력에 {_final_idx_month}월 값이 없어 "
                                   f"단가 상세·변동 분석은 표시하지 않습니다 — 확정액 자체는 저장된 값입니다.")
                    elif new_fm != "—":
                        st.info(f"Final월({new_fm}) INDEX 이력이 등록되지 않아 확정산을 계산할 수 없습니다.")
                    else:
                        # Provisional만 있는 경우 (Final월 미지정)
                        if pm_data:
                            _prov_label2 = f"가정산 수령 ({_prov_pct_val:.0f}%)" if _prov_pct_val < 100 else "Provisional 정산액"
                            st.info(
                                f"Prov INDEX {_prov_idx_month}: **\\${prov_pkg:.2f}/kg**  |  "
                                f"Invoice 총액: **\\${new_iusd:,.2f}**  |  {_prov_label2}: **\\${prov_paid:,.2f}**  "
                                f"— Final 월을 선택하면 확정산 청구액을 계산합니다."
                            )
                        else:
                            st.caption(f"ℹ️ Provisional월({_prov_idx_month}) INDEX 이력이 없어 가정산 단가를 계산할 수 없습니다.")

                ca,cb=st.columns(2)
                with ca:
                    if st.button("저장",key=f"sh_save_{real_i}"):
                        _save_err = []
                        # 선적일 형식·정합성 검사
                        if new_ld and not _valid_date_str(new_ld):
                            _save_err.append("선적일 형식이 잘못됐습니다 (YYYY-MM-DD, 연도 1990~2100)")
                        # ETA > 선적일 검사
                        if new_ld and new_eta and new_eta < new_ld:
                            _save_err.append(f"ETA({new_eta})가 선적일({new_ld})보다 앞섭니다")
                        for _pd_lbl, _pd_val in (("가정산 입금일", new_ppd), ("확정산 입금일", new_fpd)):
                            if _pd_val.strip() and not _valid_date_str(_pd_val.strip()):
                                _save_err.append(f"{_pd_lbl} 형식이 잘못됐습니다 (YYYY-MM-DD)")
                        # Final월 >= Provisional월 검사
                        if new_pm != "—" and new_fm != "—" and new_fm < new_pm:
                            _save_err.append(f"Final월({new_fm})이 Provisional월({new_pm})보다 앞섭니다")
                        # HBL 중복 체크 (자기 자신 제외)
                        if new_hbl:
                            _dup = [s2 for j2,s2 in enumerate(shipments) if j2!=real_i and s2.get("hbl","").strip()==new_hbl.strip()]
                            if _dup: _save_err.append(f"HBL '{new_hbl}' 이(가) 이미 존재합니다")
                        # 빈 HBL 동일 조합 중복 체크
                        if not new_hbl.strip() and new_ld and new_wkg:
                            _dup2 = [s2 for j2,s2 in enumerate(shipments)
                                     if j2!=real_i
                                     and not s2.get("hbl","").strip()
                                     and s2.get("loading_date","") == new_ld
                                     and s2.get("buyer_id","") == buyer_opts[new_b]
                                     and abs(float(s2.get("weight_kg",0)) - new_wkg) < 1]
                            if _dup2: _save_err.append("HBL 미입력인 동일 매입사·선적일·중량 선적건이 이미 있습니다")
                        if _save_err:
                            for _e in _save_err: st.error(_e)
                        else:
                            # Final 스냅샷: final 상태인데 스냅샷이 없으면 저장 시점에 확정
                            # (앱에서 직접 전환한 경우뿐 아니라, 구글시트 동기화로 이미
                            #  final 상태가 된 뒤 스냅샷만 비어있는 경우도 포함)
                            _snap_final = s.get("final_amount_usd")
                            if new_stat == "final" and not _snap_final:
                                # 현재 계산값으로 스냅샷 저장
                                _snap_ct  = _get_contract_for_shipment(cfg, s.get("id",""))
                                _snap_st  = _settle_terms(_snap_ct, b)
                                if new_fm != "—" and new_fm in hm_all_b:
                                    _snap_fidx = _resolve_idx_month(_snap_st["final_idx"], new_ld, new_pm, new_fm)
                                    if _snap_fidx not in hm_all_b: _snap_fidx = new_fm
                                    _sfmd = hm_all_b[_snap_fidx]
                                    _,_,_,_sfpkg_raw = bp_price(_sfmd["ni_index"],_sfmd["co_index"],
                                                            _eff_ni, _eff_co,
                                                            _snap_st["ni_payable"], _snap_st["co_payable"])
                                    _snap_rbm = b.get("round_price_before_moisture", False) if b else False
                                    _snap_price = round(_sfpkg_raw, 2) if _snap_rbm else _sfpkg_raw
                                    _snap_final = round(_snap_price * new_wkg * (1 - new_moisture/100), 2)
                            elif new_stat == "provisional":
                                _snap_final = None  # final 상태 해제(재정산) 시에만 스냅샷 제거 — paid는 final 스냅샷을 유지
                            cfg["shipments"][real_i].update({
                                "hbl":new_hbl,"invoice_no":new_inv,
                                "loading_date":new_ld,"buyer_id":buyer_opts[new_b],
                                "weight_kg":new_wkg,"invoice_usd":new_iusd,
                                "export_cost_usd":new_eusd if new_eusd > 0 else None,
                                "prov_month":new_pm,"final_month":new_fm,
                                "status":new_stat,"etd":new_etd,"eta":new_eta,"notes":new_note,
                                "moisture_pct":new_moisture if new_moisture > 0 else None,
                                "buyer_ni_content":new_buyer_ni if new_buyer_ni!=default_ni or s.get("buyer_ni_content") else None,
                                "buyer_co_content":new_buyer_co if new_buyer_co!=default_co or s.get("buyer_co_content") else None,
                                "ni_content_src":_ni_src,
                                "co_content_src":_co_src,
                                "linked_contract_id": new_linked_ct_id if new_linked_ct_id else None,
                                "other_adj_usd":new_other_adj if new_other_adj else None,
                                "other_adj_desc":new_other_desc,
                                "prov_paid_date":  new_ppd.strip() or None,
                                "prov_paid_usd":   new_ppu if new_ppu else None,
                                "final_paid_date": new_fpd.strip() or None,
                                "final_paid_usd":  new_fpu if new_fpu else None,
                                "final_amount_usd": _snap_final})
                            save_cfg(cfg); st.toast("✅ 저장 완료"); st.rerun()
                with cb:
                    with st.popover("삭제", use_container_width=True):
                        st.warning(f"**{s.get('hbl','?')}** 선적건을 삭제합니다.")
                        if st.button("삭제 확인", key=f"sh_del_cfm_{real_i}", type="primary", use_container_width=True):
                            cfg["shipments"].pop(real_i); save_cfg(cfg); st.rerun()

        # ── 전체 요약 테이블 ──
        if show_ships:
            st.divider()
            tbl_rows=[]
            for s in show_ships:
                bx=buyer_map.get(s.get("buyer_id",""),{})
                hm_all_x=_hm_for(cfg, bx)  # 매입사별 INDEX 예외 반영
                # 추가정산 계산 (가능한 경우)
                net_disp="—"
                pm2=s.get("prov_month","—"); fm2=s.get("final_month","—")
                if (bx and pm2!="—" and pm2 in hm_all_x):
                    _tst = _settle_terms(_get_contract_for_shipment(cfg, s.get("id","")), bx)
                    _tprov = float(s.get("invoice_usd",0)) * (_tst["prov_pct"] / 100.0)
                    _snapped2 = s.get("final_amount_usd")
                    if _snapped2:
                        net_v = float(_snapped2) - _tprov + (s.get("other_adj_usd") or 0)
                        net_disp = f"${net_v:+,.2f}"
                    elif fm2!="—" and fm2 in hm_all_x:
                        _bni2 = s.get("buyer_ni_content") or bx.get("ni_content",0)
                        _bco2 = s.get("buyer_co_content") or bx.get("co_content",0)
                        _eni2 = _eff_content(_bni2, bx.get("ni_content",0), s.get("ni_content_src","매입사값"))
                        _eco2 = _eff_content(_bco2, bx.get("co_content",0), s.get("co_content_src","매입사값"))
                        _,_,_,fpkg2=bp_price(hm_all_x[fm2]["ni_index"],hm_all_x[fm2]["co_index"],
                            _eni2, _eco2, _tst["ni_payable"], _tst["co_payable"])
                        mst=s.get("moisture_pct") or 0
                        fw2=s.get("weight_kg",0)*(1-mst/100)
                        net_v=fpkg2*fw2 - _tprov + (s.get("other_adj_usd") or 0)
                        net_disp=f"${net_v:+,.2f} (추정)"
                tbl_rows.append({
                    "HBL":s.get("hbl","—"),
                    "매입사":f"{bx.get('name','?')} ({bx.get('product','?')})",
                    "선적일":s.get("loading_date",""),
                    "중량(kg)":s.get("weight_kg",0),
                    "Invoice(USD)":s.get("invoice_usd",0),
                    "Prov월":s.get("prov_month","—"),
                    "Final월":s.get("final_month","—"),
                    "추가정산(USD)":net_disp,
                    "상태":s.get("status","provisional")})
            st.dataframe(pd.DataFrame(tbl_rows).style.format({"중량(kg)":"{:,.0f}","Invoice(USD)":"${:,.2f}"}),
                         use_container_width=True,hide_index=True)
            st.download_button("CSV",pd.DataFrame(tbl_rows).to_csv(index=False,encoding="utf-8-sig"),
                f"선적정산_{date.today():%Y%m%d}.csv","text/csv")

        # ── 채권 Aging 보고서 (입금 기록 기준) ───────────────────────────────
        # 미수 = (가정산 예정액 − 가정산 입금액) + (확정산 청구액 − 확정산 입금액, final/paid 건만).
        # 만기 = 가정산: 선적일 + 매입사 가정산 입금 조건 / 확정산: (ETA, 없으면 선적일+60일) + 확정산 조건.
        # (예전엔 입금 기록이 없어 선적일 경과일수로 근사했음)
        _today_d = date.today()
        _aging_rows = []
        for _as in shipments:
            _ab  = buyer_map.get(_as.get("buyer_id",""), {})
            _ast = _settle_terms(_get_contract_for_shipment(cfg, _as.get("id","")), _ab)
            _inv = float(_as.get("invoice_usd") or 0)
            _prov_exp  = _inv * (_ast["prov_pct"] / 100.0)
            _prov_open = _prov_exp - float(_as.get("prov_paid_usd") or 0)
            _final_open = 0.0
            if _as.get("status") in ("final", "paid"):
                _famt = _as.get("final_amount_usd") or _recompute_final_settlement(cfg, _as)
                if _famt is not None:
                    _final_net  = float(_famt) - _prov_exp + float(_as.get("other_adj_usd") or 0)
                    _final_open = _final_net - float(_as.get("final_paid_usd") or 0)
            _prov_open  = _prov_open  if abs(_prov_open)  > 1 else 0.0
            _final_open = _final_open if abs(_final_open) > 1 else 0.0
            if not _prov_open and not _final_open:
                continue
            try:
                _ld_d = date.fromisoformat(_as.get("loading_date", ""))
            except Exception:
                _ld_d = None
            _eta_d = None
            if _valid_date_str(_as.get("eta", "")):
                _eta_d = date.fromisoformat(_as["eta"])
            elif _ld_d:
                _eta_d = _ld_d + timedelta(days=60)
            _prov_due  = (_ld_d  + timedelta(days=int(_ab.get("prov_pay_days")  or 0) or 30)) if _ld_d  else None
            _final_due = (_eta_d + timedelta(days=int(_ab.get("final_pay_days") or 0) or 30)) if _eta_d else None
            _dues = [d for d, o in ((_prov_due, _prov_open), (_final_due, _final_open)) if d and o]
            _due  = min(_dues) if _dues else None
            _days = (_today_d - _due).days if _due else None
            if _days is None:   _band = "만기 미정"
            elif _days < 0:     _band = "미도래"
            elif _days < 30:    _band = "< 30일"
            elif _days < 60:    _band = "30–60일"
            elif _days < 90:    _band = "60–90일"
            else:               _band = "> 90일"
            _aging_rows.append({
                "Aging":      _band,
                "경과일":     _days,
                "HBL":        _as.get("hbl","—"),
                "매입사":     _ab.get("name","?"),
                "상태":       _as.get("status","provisional"),
                "가정산 미수": round(_prov_open, 2),
                "확정산 미수": round(_final_open, 2),
                "미수 합계":  round(_prov_open + _final_open, 2),
                "기준 만기일": _due.isoformat() if _due else "—",
            })
        if _aging_rows:
            with st.expander(f"미수채권 Aging — {len(_aging_rows)}건 (입금 기록 기준)", expanded=False):
                _aging_rows.sort(key=lambda r: (r["경과일"] is None, -(r["경과일"] or 0)))
                _band_cnt = {}
                for _r in _aging_rows:
                    _band_cnt[_r["Aging"]] = _band_cnt.get(_r["Aging"], 0) + 1
                _tot_open = sum(r["미수 합계"] for r in _aging_rows)
                _tot_over = sum(r["미수 합계"] for r in _aging_rows if r["경과일"] is not None and r["경과일"] >= 0)
                st.caption("  ·  ".join(f"**{b}**: {n}건" for b, n in sorted(_band_cnt.items()))
                           + f"  |  미수 합계 **\\${_tot_open:,.0f}**  |  만기 경과분 **\\${_tot_over:,.0f}**"
                           "  |  음수 = 반환 예정. 입금 조건은 매입사 관리에서 설정(미설정 30일)")
                st.dataframe(
                    pd.DataFrame(_aging_rows).style.format(na_rep="—", formatter={
                        "가정산 미수": "${:,.2f}", "확정산 미수": "${:,.2f}", "미수 합계": "${:,.2f}",
                        "경과일": lambda v: f"{v:+.0f}일" if pd.notna(v) else "—"}),
                    use_container_width=True, hide_index=True,
                )

    st.divider()
    with st.expander("새 선적건 수동 추가 (시트 동기화가 기본)", expanded=False):
        with st.form("add_ship"):
            a1,a2,a3,a4=st.columns(4)
            with a1: a_hbl=st.text_input("HBL"); a_inv=st.text_input("Invoice No.")
            with a2: a_buy=st.selectbox("매입사",list(buyer_opts.keys())); a_ld=st.text_input("선적일 (YYYY-MM-DD)",placeholder="2026-04-01")
            with a3: a_etd=st.text_input("ETD (YYYY-MM-DD)",placeholder="2026-04-05"); a_wkg=st.number_input("중량 (kg)",value=0.0,step=1.0,format="%.0f")
            with a4: a_iusd=st.number_input("Invoice (USD)",value=0.0,step=1.0,format="%.2f"); a_pm=st.selectbox("Provisional 월",["—"]+hist_opts); a_fm=st.selectbox("Final 월",["—"]+hist_opts)
            if st.form_submit_button("추가"):
                cfg["shipments"].append({"id":str(uuid.uuid4())[:8],"hbl":a_hbl,"invoice_no":a_inv,
                    "loading_date":a_ld,"etd":a_etd.strip(),"buyer_id":buyer_opts[a_buy],"weight_kg":a_wkg,"invoice_usd":a_iusd,
                    "prov_month":a_pm,"final_month":a_fm,"status":"provisional","eta":"","notes":"",
                    "moisture_pct":None,"buyer_ni_content":None,"buyer_co_content":None,
                    "other_adj_usd":None,"other_adj_desc":""})
                save_cfg(cfg); st.toast("✅ 추가 완료!"); st.rerun()

    # ── 🔍 HBL 수명주기 조회 ────────────────────────────────────────────────────
    if shipments:
        st.divider()
        st.markdown("#### HBL 수명주기 조회")
        _lc_proc_m  = {p["id"]: p for p in cfg.get("processors", [])}
        _lc_scrap_m = {s["id"]: s for s in cfg.get("scrap_types", [])}
        _lc_hbl_opts = {}
        for _ls in sorted(shipments, key=lambda x: x.get("loading_date",""), reverse=True):
            if not _ls.get("id"):
                continue
            _lk = (f"{_ls.get('hbl','—')}  ·  "
                   f"{buyer_map.get(_ls.get('buyer_id',''),{}).get('name','?')}  ·  "
                   f"{_ls.get('loading_date','미정')}")
            if _lk in _lc_hbl_opts:
                _lk = f"{_lk}  [{_ls['id'][:4]}]"
            _lc_hbl_opts[_lk] = _ls["id"]
        _lc_sel = st.selectbox("HBL 선택", list(_lc_hbl_opts), key="lc_hbl_sel")
        _lc_sid  = _lc_hbl_opts[_lc_sel]
        _lc_ship = next((s for s in shipments if s.get("id") == _lc_sid), {})
        _lc_buyer = buyer_map.get(_lc_ship.get("buyer_id",""), {})
        _lc_batches = [r for r in cfg.get("processing_history", []) if r.get("shipment_id") == _lc_sid]

        # 이벤트 목록 구성
        _lc_events = []

        # 처리 배치
        for _lb in _lc_batches:
            _bd   = _rec_ref_date(_lb, cfg) or "—"
            _pname = _lc_proc_m.get(_lb.get("processor_id",""), {}).get("name", "?")
            _sname = _lc_scrap_m.get(_lb.get("scrap_type_id",""), {}).get("name", "?")
            _inp   = _ph_input_kg(_lb)
            _out   = float(_lb.get("output_kg", 0) or 0)
            _lc_events.append({
                "sort": _bd, "icon": "🏭", "title": f"임가공 처리  —  {_pname}",
                "detail": f"{_sname}  |  투입 {_inp/1000:.3f} MT  →  BP {_out/1000:.3f} MT  (전환율 {_out/_inp*100:.1f}%)" if _inp > 0 else f"{_sname}",
            })

        # 선적
        _ld = _lc_ship.get("loading_date", "")
        if _ld:
            _lc_events.append({
                "sort": _ld, "icon": "🚢", "title": "선적 출항",
                "detail": f"HBL: {_lc_ship.get('hbl','—')}  |  {float(_lc_ship.get('weight_kg',0))/1000:.3f} MT  |  매입사: {_lc_buyer.get('name','?')} ({_lc_buyer.get('product','')})",
            })

        # ETA
        _eta = _lc_ship.get("eta", "")
        if _eta:
            _arrived = _eta <= date.today().isoformat()
            _lc_events.append({
                "sort": _eta, "icon": "⚓" if _arrived else "🕐",
                "title": f"{'입항 (도착)' if _arrived else 'ETA (예정)'}",
                "detail": f"{_eta}",
            })

        # Provisional 정산
        _pm = _lc_ship.get("prov_month", "")
        if _pm and _pm != "—":
            _lc_events.append({
                "sort": _pm + "-15", "icon": "🟡", "title": "Provisional 정산",
                "detail": f"기준월: {_pm}  |  Invoice: ${float(_lc_ship.get('invoice_usd',0)):,.2f}",
            })

        # 최종/입금
        _fm = _lc_ship.get("final_month", "")
        _st = _lc_ship.get("status", "provisional")
        if _st in ("final", "paid") and _fm and _fm != "—":
            _lc_events.append({
                "sort": _fm + "-28", "icon": "🟢" if _st == "final" else "🔵",
                "title": "최종 정산" if _st == "final" else "입금 완료",
                "detail": f"기준월: {_fm}",
            })

        _lc_events.sort(key=lambda e: e["sort"] if e["sort"] and e["sort"] != "—" else "9999-12-31")

        if _lc_events:
            for _ei, _ev in enumerate(_lc_events):
                _ca, _cb = st.columns([1, 15])
                _ca.markdown(f"## {_ev['icon']}")
                _cb.markdown(f"**{_ev['title']}**")
                _cb.caption(_ev["detail"])
                if _ei < len(_lc_events) - 1:
                    st.markdown("<div style='margin-left:28px;color:#555;font-size:18px;line-height:0.8'>│<br>│</div>",
                                unsafe_allow_html=True)
        else:
            st.info("연결된 처리 배치가 없습니다. 임가공사·배치 서브페이지에서 HBL을 연결하세요.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — 포워더 운임 관리
# ══════════════════════════════════════════════════════════════════════════════
if _page == PG_MASTER and _sub == SUB_FWD:
    st.subheader("포워더 운임 관리")
    st.caption("포워더별 운임 견적을 관리합니다. 배치 수출비 설정에 활용됩니다.")

    eur_usd_val = _get_eur_usd(cfg)   # 최신 월별 EUR/USD (INDEX·환율 서브페이지에서 관리)
    st.caption(f"EUR 견적은 최신 월별 EUR/USD {eur_usd_val:.4f}로 환산합니다.")
    fwd_list_tab = cfg.get("forwarders", [])
    st.divider()

    if not fwd_list_tab:
        st.info("등록된 포워더가 없습니다. 아래에서 추가하세요.")

    for fi, fwd in enumerate(fwd_list_tab):
        q_count = len(fwd.get("quotes", []))
        with st.expander(
            f"{'✅' if fwd.get('active', True) else '⛔'}  {fwd['name']}  ({q_count}개 견적)",
            expanded=True
        ):
            fhc1, fhc2 = st.columns([3, 1])
            with fhc1: fnm = st.text_input("포워더명", fwd["name"], key=f"fwd_nm_{fi}")
            with fhc2: fact = st.checkbox("활성", fwd.get("active", True), key=f"fwd_act_{fi}")

            quotes = fwd.get("quotes", [])
            if not quotes:
                st.caption("등록된 견적이 없습니다.")

            for qi, q in enumerate(quotes):
                curr    = q.get("currency", "USD")
                dest    = q.get("destination","").strip() or "목적지 미지정"
                t_items = (q.get("pickup_rail",0)+q.get("ocean_freight",0)+q.get("dg_surcharge",0)
                           +q.get("fuel_surcharge",0)+q.get("documentation",0)+q.get("terminal_handling",0))
                t_usd   = t_items * eur_usd_val if curr == "EUR" else t_items
                cap     = q.get("capacity_kg", 1) or 1
                pkg_usd = t_usd / cap

                q_title = (f"견적 {qi+1}  ·  [{dest}]  {q.get('label','—')}  ·  "
                           f"{q.get('container_type','?').upper()}  ·  "
                           f"{curr} {t_items:,.0f}  →  \\${t_usd:,.2f}  (\\${pkg_usd:.4f}/kg)")
                with st.expander(q_title, expanded=False):
                    qr1, qr2, qr3, qr4 = st.columns(4)
                    with qr1:
                        q_dest  = st.text_input("목적지", q.get("destination",""),
                                                placeholder="예: CIF BUSAN", key=f"fwd_qdest_{fi}_{qi}")
                        q_label = st.text_input("견적명", q.get("label",""), key=f"fwd_ql_{fi}_{qi}")
                        q_cntr  = st.selectbox("컨테이너", ["20ft","40ft"],
                                               ["20ft","40ft"].index(q.get("container_type","20ft")),
                                               key=f"fwd_qcntr_{fi}_{qi}")
                        q_cap   = st.number_input("용량 (kg)", value=float(q.get("capacity_kg",20000)),
                                                  step=100.0, format="%.0f", key=f"fwd_qcap_{fi}_{qi}")
                        q_curr  = st.selectbox("통화", ["USD","EUR"],
                                               ["USD","EUR"].index(q.get("currency","USD")),
                                               key=f"fwd_qcurr_{fi}_{qi}")
                    with qr2:
                        st.markdown(f"**비용 항목 ({q.get('currency','USD')})**")
                        q_pr = st.number_input("픽업+Rail",        value=float(q.get("pickup_rail",0)),    step=1.0, format="%.0f", key=f"fwd_pr_{fi}_{qi}")
                        q_of = st.number_input("Ocean Freight",    value=float(q.get("ocean_freight",0)),  step=1.0, format="%.0f", key=f"fwd_of_{fi}_{qi}")
                        q_dg = st.number_input("DG Surcharge",     value=float(q.get("dg_surcharge",0)),   step=1.0, format="%.0f", key=f"fwd_dg_{fi}_{qi}")
                    with qr3:
                        st.markdown("‎")
                        q_fs = st.number_input("Fuel Surcharge",   value=float(q.get("fuel_surcharge",0)), step=1.0, format="%.0f", key=f"fwd_fs_{fi}_{qi}")
                        q_dc = st.number_input("Documentation",    value=float(q.get("documentation",0)),  step=1.0, format="%.0f", key=f"fwd_dc_{fi}_{qi}")
                        q_th = st.number_input("Terminal Handling", value=float(q.get("terminal_handling",0)), step=1.0, format="%.0f", key=f"fwd_th_{fi}_{qi}")
                    with qr4:
                        t_loc = q_pr+q_of+q_dg+q_fs+q_dc+q_th
                        t_u   = t_loc * eur_usd_val if q_curr=="EUR" else t_loc
                        t_e   = t_loc / eur_usd_val if q_curr=="USD" else t_loc
                        p_u   = t_u / q_cap if q_cap > 0 else 0
                        st.markdown("**합계**")
                        st.markdown(_kpi_card(f"합계 ({q_curr})", f"{q_curr} {t_loc:,.0f}"), unsafe_allow_html=True)
                        if q_curr=="EUR":
                            st.markdown(_kpi_card("합계 (USD)", f"${t_u:,.2f}", f"× {eur_usd_val} EUR/USD"), unsafe_allow_html=True)
                        else:
                            st.markdown(_kpi_card("합계 (EUR)", f"€{t_e:,.2f}", f"÷ {eur_usd_val} EUR/USD"), unsafe_allow_html=True)
                        st.markdown(_kpi_card("단가 ($/kg)", f"${p_u:.4f}"), unsafe_allow_html=True)
                        q_notes = st.text_input("비고", q.get("notes",""), key=f"fwd_qnotes_{fi}_{qi}")

                    qs1, qs2 = st.columns(2)
                    with qs1:
                        if st.button("견적 저장", key=f"fwd_qsave_{fi}_{qi}", use_container_width=True):
                            cfg["forwarders"][fi]["quotes"][qi].update({
                                "destination":q_dest, "label":q_label, "container_type":q_cntr, "capacity_kg":q_cap,
                                "currency":q_curr, "pickup_rail":q_pr, "ocean_freight":q_of,
                                "dg_surcharge":q_dg, "fuel_surcharge":q_fs,
                                "documentation":q_dc, "terminal_handling":q_th, "notes":q_notes})
                            save_cfg(cfg); st.success("견적 저장됨"); st.rerun()
                    with qs2:
                        with st.popover("", use_container_width=True):
                            st.warning(f"견적 **{q.get('label','?')}** 삭제")
                            if st.button("삭제 확인", key=f"fwd_qdel_cfm_{fi}_{qi}", type="primary", use_container_width=True):
                                cfg["forwarders"][fi]["quotes"].pop(qi)
                                save_cfg(cfg); st.rerun()

            st.markdown("---")
            fb1, fb2, fb3 = st.columns(3)
            with fb1:
                if st.button("견적 추가", key=f"fwd_qadd_{fi}", use_container_width=True):
                    cfg["forwarders"][fi].setdefault("quotes", []).append({
                        "id":str(uuid.uuid4())[:8], "destination":"", "label":"새 견적",
                        "container_type":"20ft", "capacity_kg":20000, "currency":"USD",
                        "pickup_rail":0, "ocean_freight":0, "dg_surcharge":0,
                        "fuel_surcharge":0, "documentation":0, "terminal_handling":0, "notes":""})
                    save_cfg(cfg); st.rerun()
            with fb2:
                if st.button("포워더 저장", key=f"fwd_save_{fi}", use_container_width=True):
                    cfg["forwarders"][fi].update({"name":fnm, "active":fact})
                    save_cfg(cfg); st.toast("✅ 저장됨"); st.rerun()
            with fb3:
                with st.popover("포워더 삭제", use_container_width=True):
                    st.warning(f"포워더 **{fwd.get('name','?')}** 전체 삭제 (견적 포함)")
                    if st.button("삭제 확인", key=f"fwd_del_cfm_{fi}", type="primary", use_container_width=True):
                        cfg["forwarders"].pop(fi)
                        save_cfg(cfg); st.rerun()

    st.divider()
    st.subheader("새 포워더 추가")
    with st.form("add_forwarder"):
        fnew = st.text_input("포워더명")
        if st.form_submit_button("추가"):
            if not fnew: st.error("포워더명을 입력하세요.")
            else:
                cfg.setdefault("forwarders", []).append({
                    "id":str(uuid.uuid4())[:8], "name":fnew, "active":True, "quotes":[]})
                save_cfg(cfg); st.success(f"{fnew} 추가!"); st.rerun()

    # ── 목적지별 수출비 비교표 ──────────────────────────────────────────────────
    st.divider()
    st.markdown("#### 목적지별 수출비 비교")
    _eur = _get_eur_usd(cfg)
    _cmp = []
    for _fwd in cfg.get("forwarders", []):
        if not _fwd.get("active", True): continue
        for _q in _fwd.get("quotes", []):
            _curr = _q.get("currency", "USD")
            _tot  = (_q.get("pickup_rail",0)+_q.get("ocean_freight",0)+_q.get("dg_surcharge",0)
                     +_q.get("fuel_surcharge",0)+_q.get("documentation",0)+_q.get("terminal_handling",0))
            _tusd = _tot * _eur if _curr=="EUR" else _tot
            _cap  = _q.get("capacity_kg", 1) or 1
            _cmp.append({
                "목적지":   _q.get("destination","").strip() or "(미지정)",
                "포워더":   _fwd["name"],
                "견적명":   _q.get("label","—"),
                "컨테이너": _q.get("container_type","?").upper(),
                "용량(kg)": int(_cap),
                "통화":     _curr,
                "수출비합계": round(_tot, 0),
                "USD 환산": round(_tusd, 2),
                "$/kg":     round(_tusd / _cap, 4),
            })

    if _cmp:
        df_cmp_all = pd.DataFrame(_cmp).sort_values(["목적지","컨테이너","$/kg"]).reset_index(drop=True)

        # 컨테이너 필터
        _cntr_types = ["전체"] + sorted(df_cmp_all["컨테이너"].unique().tolist())
        _sel_cntr = st.radio("컨테이너 필터", _cntr_types, horizontal=True, key="cmp_cntr_flt")
        df_cmp = df_cmp_all if _sel_cntr=="전체" else df_cmp_all[df_cmp_all["컨테이너"]==_sel_cntr].reset_index(drop=True)

        _min_dest = df_cmp.groupby("목적지")["$/kg"].min()

        def _hl_best(row):
            if row["$/kg"] == _min_dest.get(row["목적지"]):
                return ["background-color:#1E8449;color:white;font-weight:600"]*len(row)
            return [""]*len(row)

        st.dataframe(
            df_cmp.style.apply(_hl_best, axis=1).format({
                "용량(kg)":"{:,.0f}", "수출비합계":"{:,.0f}",
                "USD 환산":"${:,.2f}", "$/kg":"${:.4f}"}),
            use_container_width=True, hide_index=True)
        st.caption("🟢 목적지별 최저 수출비")

        # 목적지 × 포워더 피벗 매트릭스
        st.markdown("##### 목적지 × 포워더  $/kg 매트릭스")
        try:
            _pivot = df_cmp.pivot_table(
                index="목적지", columns="포워더", values="$/kg", aggfunc="min").round(4)

            def _hl_row_min(row):
                mn = row.min()
                return ["background-color:#1E8449;color:white;font-weight:600" if v==mn else "" for v in row]

            st.dataframe(
                _pivot.style.apply(_hl_row_min, axis=1).format("${:.4f}", na_rep="—"),
                use_container_width=True)
            st.caption("셀 값: 해당 포워더·목적지의 최저 $/kg  |  🟢 행 최저값")
        except Exception:
            st.info("목적지 및 포워더가 2개 이상 등록되면 매트릭스가 표시됩니다.")
    else:
        st.info("견적을 등록하면 비교표가 표시됩니다.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — 손익 분석
# ══════════════════════════════════════════════════════════════════════════════
if _page == PG_PNL:
    st.subheader("손익 분석")

    # ③ EUR/USD 공백 경고: 출고·처리 이력 월 중 최신 등록 환율보다 이후 월 검출
    _eur_rates_sorted = sorted(cfg.get("eur_usd_rates", []), key=lambda x: x["month"])
    if _eur_rates_sorted:
        _eur_latest = _eur_rates_sorted[-1]["month"]
        _dispatch_months = {
            (dr.get("date") or "")[:7]
            for dr in cfg.get("dispatch_records", [])
            if (dr.get("date") or "")[:7] > _eur_latest
        }
        _ph_months = set()
        for _gr in cfg.get("processing_history", []):
            _grd = _rec_ref_date(_gr, cfg)
            if _grd and _grd[:7] > _eur_latest:
                _ph_months.add(_grd[:7])
        _gap_months = sorted(_dispatch_months | _ph_months)
        if _gap_months:
            st.warning(
                f"⚠️ **EUR/USD 환율 미등록 월**: {', '.join(_gap_months)}  \n"
                f"해당 월의 창고비(보관비) 계산에 {_eur_latest} 환율({_eur_rates_sorted[-1]['rate']:.4f})이 적용됩니다.  \n"
                "정확한 계산을 위해 **마스터·동기화 > INDEX·환율·판관비**에서 해당 월 EUR/USD를 등록하세요."
            )

    _ph_all   = cfg.get("processing_history", [])
    _bm_pnl   = {b["id"]: b for b in cfg["buyers"]}
    _sm_pnl   = {s["id"]: s for s in cfg.get("shipments", [])}
    _pm_pnl   = {p["id"]: p for p in cfg.get("processors", [])}
    _scm_pnl  = {s["id"]: s for s in cfg.get("scrap_types", [])}

    # ── 손익 엔진 바인딩 (모듈 레벨 _pnl_context 공용) ──────────────────────
    _pctx = _pnl_context(cfg)
    _fifo_rmc_map          = _pctx["rmc_map"]
    _fifo_sc_ids_avail     = _pctx["sc_ids"]
    _auto_storage_for_batch = _pctx["auto_storage"]
    _get_rmc_fifo          = _pctx["rmc_fifo"]
    _get_rmc_mavg          = _pctx["rmc_mavg"]
    _linked_pnl = [r for r in _ph_all if r.get("shipment_id","")]   # 이론 vs 실적 비교에서도 사용

    # ══════════════════════════════════════════════════════════════════════════
    # 섹션 1 — 관리회계 손익 요약 (상계 기준)
    # 세금계산서상 총액 흐름(스크랩 매각·BP 재매입)은 상계 처리하고,
    # 매출 − 원료비 − 임가공비(순) − 판관비 구조로 먼저 보여준다.
    # 총액(그로스) 흐름은 아래 '세금계산서 기준 총액 흐름' expander에 유지.
    # ══════════════════════════════════════════════════════════════════════════
if _page == PG_PNL and _sub == SUB_PNL_SUM:
    st.markdown("#### 관리회계 손익 요약")
    if not _ph_all:
        st.info("처리 이력(재고·임가공 > 임가공사·배치 > 세부 내역)을 입력하면 실적 기반 손익이 표시됩니다.")
    else:
        _tot_out  = sum(r.get("output_kg",0) or 0 for r in _ph_all)
        _tot_inp  = sum(_ph_input_kg(r) for r in _ph_all)
        # 전체 흐름 집계 (스크랩 매각수익 · BP 재매입원가 — 상계 전 총액)
        _tot_sc_rev  = sum((r.get("scrap_sale_per_kg",0) or 0) * _ph_input_kg(r) for r in _ph_all)  # 스크랩 매각수익
        _tot_pf      = sum((r.get("processing_fee_per_kg",0) or 0) * _ph_input_kg(r) for r in _ph_all)  # 임가공비
        _tot_repr    = _tot_sc_rev + _tot_pf   # BP 재매입 원가 합계 (= 스크랩 + 임가공비)
        _tot_eu      = sum(_ph_export_usd(r, cfg) for r in _ph_all)
        _tot_bp      = sum((r.get("bp_sale_per_kg",0) or 0) * (r.get("output_kg",0) or 0) for r in _ph_all)
        # 거래 마진 = BP매각 + 스크랩매각 - BP재매입 - 수출비  (스크랩 상계 → 임가공비+수출비만 남음)
        _tot_net  = _tot_bp + _tot_sc_rev - _tot_repr - _tot_eu
        _avg_mg   = _tot_net / _tot_bp * 100 if _tot_bp > 0 else 0
        _repr_per_kg = _tot_repr / _tot_out if _tot_out > 0 else 0
        _pf_per_kg   = _tot_pf   / _tot_out if _tot_out > 0 else 0
        _epk_all     = _tot_eu   / _tot_out if _tot_out > 0 else 0

        # 원료비·보관비 (waterfall·단가 분해와 공용 — FIFO 기준)
        _default_rmc_s1 = float(st.session_state.get("pnl_rmc_default", 0.0))
        if _tot_out > 0:
            _raw_fifo_s1 = sum(_get_rmc_fifo(r, _default_rmc_s1)[0] * _ph_input_kg(r) for r in _ph_all)
            _raw_mavg_s1 = sum(_get_rmc_mavg(r, _default_rmc_s1)[0] * _ph_input_kg(r) for r in _ph_all)
            _stor_s1     = sum(
                _ph_storage_cost(r, cfg) if r.get("storage_days") else _auto_storage_for_batch(r)
                for r in _ph_all
            )
        else:
            _raw_fifo_s1 = _raw_mavg_s1 = _stor_s1 = 0.0
        _tot_real_fifo = _tot_net - _raw_fifo_s1 - _stor_s1

        # 간접 판관비·기타 — 마스터·동기화 > INDEX·환율·판관비에 저장된 월별 값의 합계
        _sga_s1, _other_s1 = _sga_totals(cfg)
        _tot_gp_s1 = _tot_bp - _raw_fifo_s1 - _tot_pf                # 매출총이익
        _tot_op_s1 = _tot_real_fifo - _sga_s1 - _other_s1            # 영업이익(실질 손익)
        _op_pct_s1 = _tot_op_s1 / _tot_bp * 100 if _tot_bp > 0 else 0
        _gp_pct_s1 = _tot_gp_s1 / _tot_bp * 100 if _tot_bp > 0 else 0

        _km1,_km2,_km3,_km4 = st.columns(4)
        _op_col = "#4ade80" if _tot_op_s1 >= 0 else "#f87171"
        _gp_col = "#4ade80" if _tot_gp_s1 >= 0 else "#f87171"
        _km1.markdown(_kpi_card("총 BP 생산",   f"{_tot_out/1000:,.2f} MT",
                                f"투입 {_tot_inp/1000:,.2f} MT"), unsafe_allow_html=True)
        _km2.markdown(_kpi_card("매출 (BP 매각)", f"${_tot_bp:,.0f}"), unsafe_allow_html=True)
        _km3.markdown(_kpi_card("매출총이익",     f"${_tot_gp_s1:+,.0f}",
                                f"매출 대비 {_gp_pct_s1:+.1f}%", val_color=_gp_col), unsafe_allow_html=True)
        _km4.markdown(_kpi_card("영업이익 (실질)", f"${_tot_op_s1:+,.0f}",
                                f"영업이익률 {_op_pct_s1:+.1f}%", val_color=_op_col), unsafe_allow_html=True)

        # ── 단계식 손익계산서 (상계 기준) ─────────────────────────────────────
        def _pl_pct(v):
            return f"{v/_tot_bp*100:+.1f}%" if _tot_bp > 0 else "—"
        _pl_rows = [
            f"| 매출 — BP 매각 | **\\${_tot_bp:,.0f}** | 100.0% |",
            f"| (−) 원료 매입비 (FIFO) | −\\${_raw_fifo_s1:,.0f} | {_pl_pct(-_raw_fifo_s1)} |",
            f"| (−) 임가공비 (순 — 스크랩 매각·재매입 상계) | −\\${_tot_pf:,.0f} | {_pl_pct(-_tot_pf)} |",
            f"| **= 매출총이익** | **\\${_tot_gp_s1:+,.0f}** | **{_pl_pct(_tot_gp_s1)}** |",
            f"| (−) 수출비 | −\\${_tot_eu:,.0f} | {_pl_pct(-_tot_eu)} |",
            f"| (−) 보관비 | −\\${_stor_s1:,.0f} | {_pl_pct(-_stor_s1)} |",
            f"| (−) 간접 판관비·기타 | −\\${_sga_s1 + _other_s1:,.0f} | {_pl_pct(-(_sga_s1 + _other_s1))} |",
            f"| **= 영업이익 (실질 손익)** | **\\${_tot_op_s1:+,.0f}** | **{_pl_pct(_tot_op_s1)}** |",
        ]
        st.markdown("| 구분 | 금액 | 매출 대비 |\n|------|-----:|-----:|\n" + "\n".join(_pl_rows))
        st.caption("스크랩 매각수익과 BP 재매입원가는 상계되어 임가공비(순)로만 반영됩니다. "
                   "원료 매입비는 FIFO 기준, 간접 판관비·기타는 마스터·동기화 > INDEX·환율·판관비의 월별 등록값 합계입니다.")

        # ── 세금계산서 기준 총액 흐름 (상계 전 — 백데이터 검증용) ─────────────
        with st.expander("세금계산서 기준 총액 흐름 (스크랩 매각·BP 재매입 상계 전)", expanded=False):
            st.caption("장부·세금계산서 대사용 총액입니다. 스크랩 매각수익과 BP 재매입원가의 "
                       "스크랩 부분은 상계 — 순 차감원가 = 임가공비 + 수출비")
            _kg1,_kg2,_kg3,_kg4 = st.columns(4)
            _net_col = "#4ade80" if _tot_net >= 0 else "#f87171"
            _kg1.markdown(_kpi_card("BP 매각 수익",  f"${_tot_bp:,.0f}"), unsafe_allow_html=True)
            _kg2.markdown(_kpi_card("스크랩 매각수익", f"${_tot_sc_rev:,.0f}",
                                    sub=f"${_tot_sc_rev/_tot_out:.4f}/kg BP" if _tot_out>0 else ""), unsafe_allow_html=True)
            _kg3.markdown(_kpi_card("BP 재매입 원가",  f"${_tot_repr:,.0f}",
                                    sub="스크랩단가 × 투입량 + 임가공비"), unsafe_allow_html=True)
            _kg4.markdown(_kpi_card("거래 마진",      f"${_tot_net:+,.0f}",
                                    f"마진율 {_avg_mg:+.1f}%", val_color=_net_col), unsafe_allow_html=True)
            _kd1,_kd2,_kd3,_kd4 = st.columns(4)
            _kd1.markdown(_kpi_card("임가공비 (순)",   f"${_tot_pf:,.0f}",
                                    sub=f"${_pf_per_kg:.4f}/kg BP" if _tot_out>0 else ""), unsafe_allow_html=True)
            _kd2.markdown(_kpi_card("재매입/kg BP",    f"${_repr_per_kg:.4f}" if _tot_out>0 else "—"), unsafe_allow_html=True)
            _kd3.markdown(_kpi_card("수출비",           f"${_tot_eu:,.0f}",
                                    sub=f"${_epk_all:.4f}/kg BP" if _tot_out>0 else ""), unsafe_allow_html=True)
            _kd4.markdown(_kpi_card("순 차감원가",     f"${_tot_pf + _tot_eu:,.0f}",
                                    sub="임가공비 + 수출비 (상계 후)"), unsafe_allow_html=True)

        # ── 임가공비 상세 검증 ─────────────────────────────────────────────────
        with st.expander("임가공비 배치별 상세 검증", expanded=False):
            _proc_map  = {p["id"]: p["name"] for p in cfg.get("processors", [])}
            _stype_map = {s["id"]: s["name"] for s in cfg.get("scrap_types", [])}
            _ship_map2 = {s["id"]: s.get("hbl","—") for s in cfg.get("shipments", [])}
            _veri_rows = []
            for _vr in _ph_all:
                _vi   = _ph_input_kg(_vr)
                _vo   = _vr.get("output_kg", 0) or 0
                _vfee = float(_vr.get("processing_fee_per_kg") or 0)
                _vcv  = (_vo / _vi * 100) if _vi > 0 else 0
                _vtot = _vfee * _vi
                _vbp  = (_vtot / _vo) if _vo > 0 else 0
                _veri_rows.append({
                    "HBL":          _ship_map2.get(_vr.get("shipment_id",""), "—"),
                    "임가공사":     _proc_map.get(_vr.get("processor_id",""), "—"),
                    "스크랩":       _stype_map.get(_vr.get("scrap_type_id",""), "—"),
                    "투입(kg)":     round(_vi, 1),
                    "생산(kg BP)":  round(_vo, 1),
                    "전환율(%)":    round(_vcv, 1),
                    "단가($/kg투입)": _vfee,
                    "총 임가공비($)": round(_vtot, 2),
                    "임가공비/kg BP": round(_vbp, 4),
                })
            if _veri_rows:
                _vdf = pd.DataFrame(_veri_rows)
                st.dataframe(
                    _vdf.style.format({
                        "투입(kg)": "{:,.1f}", "생산(kg BP)": "{:,.1f}",
                        "전환율(%)": "{:.1f}", "단가($/kg투입)": "${:.4f}",
                        "총 임가공비($)": "${:,.2f}", "임가공비/kg BP": "${:.4f}",
                    }),
                    use_container_width=True, hide_index=True,
                )
                # 임가공사별 소계
                st.markdown("**임가공사별 소계**")
                _vsub = _vdf.groupby("임가공사").agg(
                    투입=("투입(kg)", "sum"),
                    생산=("생산(kg BP)", "sum"),
                    임가공비=("총 임가공비($)", "sum"),
                ).reset_index()
                _vsub["전환율(%)"]    = (_vsub["생산"] / _vsub["투입"] * 100).round(1)
                _vsub["단가/kg투입"]  = (_vsub["임가공비"] / _vsub["투입"]).round(4)
                _vsub["단가/kg BP"]   = (_vsub["임가공비"] / _vsub["생산"]).round(4)
                st.dataframe(
                    _vsub.style.format({
                        "투입": "{:,.1f}", "생산": "{:,.1f}", "전환율(%)": "{:.1f}",
                        "임가공비": "${:,.2f}", "단가/kg투입": "${:.4f}", "단가/kg BP": "${:.4f}",
                    }),
                    use_container_width=True, hide_index=True,
                )
                st.caption("💡 '단가($/kg투입)' = 계약서 기준 단가. '임가공비/kg BP' = 전환율 반영 후 BP 생산량 기준 환산값")

        # (원료비·보관비는 섹션 상단에서 이미 계산 — _raw_fifo_s1/_raw_mavg_s1/_stor_s1)

        # P&L Waterfall 차트 (관리회계 기준: 매출 → 영업이익)
        try:
            import plotly.graph_objects as go
            _op_sign  = "▲" if _tot_op_s1 >= 0 else "▼"
            _wf = go.Figure(go.Waterfall(
                orientation="v",
                measure=["absolute", "relative", "relative", "total",
                         "relative", "relative", "relative", "total"],
                x=["매출 (BP 매각)", "원료 매입비", "임가공비 (순)", "매출총이익",
                   "수출비", "보관비", "판관비·기타", "영업이익 (실질)"],
                y=[_tot_bp, -_raw_fifo_s1, -_tot_pf, 0,
                   -_tot_eu, -_stor_s1, -(_sga_s1 + _other_s1), 0],
                text=[f"${_tot_bp:,.0f}", f"-${abs(_raw_fifo_s1):,.0f}", f"-${_tot_pf:,.0f}",
                      f"${_tot_gp_s1:+,.0f}",
                      f"-${_tot_eu:,.0f}", f"-${abs(_stor_s1):,.0f}",
                      f"-${_sga_s1 + _other_s1:,.0f}", f"${_tot_op_s1:+,.0f}"],
                textposition="outside",
                increasing=dict(marker=dict(color=_C_BP)),
                decreasing=dict(marker=dict(color=_C_NEG)),
                totals=dict(marker=dict(color=_C_TOT)),
                connector=dict(line=dict(color="#484848", width=1, dash="dot")),
                hovertemplate="%{x}<br>$%{y:+,.2f}<extra></extra>",
            ))
            _fig_style(_wf, height=380, legend=False,
                       title=f"매출 ${_tot_bp:,.0f}  →  영업이익 {_op_sign} ${_tot_op_s1:+,.0f}  (원료비 FIFO 기준)")
            st.plotly_chart(_wf, use_container_width=True)
        except ImportError:
            pass

        # ── BP 1kg당 단가 분해 ────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("**📐 BP 1kg당 단가 분해**")
        st.caption("전체 처리 이력 합산 기준. 원료 취득원가는 FIFO·이동평균 두 가지 기준 비교.")
        if _tot_out > 0:

            _bp_pk   = _tot_bp  / _tot_out
            _pf_pk   = _tot_pf  / _tot_out
            _eu_pk   = _tot_eu  / _tot_out
            _rf_pk   = _raw_fifo_s1 / _tot_out
            _rm_pk   = _raw_mavg_s1 / _tot_out
            _st_pk   = _stor_s1     / _tot_out
            _gpf_pk  = _bp_pk - _rf_pk - _pf_pk   # 매출총이익 FIFO
            _gpm_pk  = _bp_pk - _rm_pk - _pf_pk   # 매출총이익 이동평균
            _rlf_pk  = _gpf_pk - _eu_pk - _st_pk  # 실질손익 FIFO
            _rlm_pk  = _gpm_pk - _eu_pk - _st_pk  # 실질손익 이동평균

            _bpkg_rows = [
                ("BP 매각가 (매출)",    _bp_pk,  _bp_pk,  0.0),
                ("  (−) 원료 매입비",   _rf_pk,  _rm_pk,  _rf_pk - _rm_pk),
                ("  (−) 임가공비 (순)", _pf_pk,  _pf_pk,  0.0),
                ("= 매출총이익",        _gpf_pk, _gpm_pk, _gpf_pk - _gpm_pk),
                ("  (−) 수출비",        _eu_pk,  _eu_pk,  0.0),
                ("  (−) 보관비",        _st_pk,  _st_pk,  0.0),
                ("= 실질 손익",         _rlf_pk, _rlm_pk, _rlf_pk - _rlm_pk),
            ]
            _df_bpkg = pd.DataFrame(
                _bpkg_rows,
                columns=["항목", "FIFO 기준 ($/kg BP)", "이동평균 기준 ($/kg BP)", "차이"],
            )

            def _hl_bpkg(row):
                lbl  = row["항목"]
                fv   = row["FIFO 기준 ($/kg BP)"]
                mv   = row["이동평균 기준 ($/kg BP)"]
                diff = row["차이"]
                if "실질 손익" in lbl:
                    bg = "#1E8449" if fv >= 0 else "#922b21"
                    s  = f"background-color:{bg};color:white;font-weight:700"
                    return ["font-weight:700", s, s, "font-weight:700"]
                if lbl.startswith("="):
                    return ["font-weight:700", "font-weight:700", "font-weight:700", "font-weight:700"]
                if "BP 매각가" in lbl:
                    return ["font-weight:700",
                            "color:#1565c0;font-weight:600",
                            "color:#1565c0;font-weight:600", ""]
                if "원료" in lbl and abs(diff) > 0.0001:
                    # 낮은 값(= 유리한 쪽)을 녹색으로 표시
                    fc = "color:#1E8449;font-weight:600" if fv <= mv else "color:#E74C3C;font-weight:600"
                    mc = "color:#1E8449;font-weight:600" if mv <= fv else "color:#E74C3C;font-weight:600"
                    return ["color:#555", fc, mc, "font-weight:600"]
                return ["color:#555", "", "", ""]

            def _fmt_pk(v):
                return f"${v:+.4f}" if v is not None else "—"

            def _fmt_diff(v):
                return f"${v:+.4f}" if v is not None and abs(v) > 0.00001 else "—"

            st.dataframe(
                _df_bpkg.style.apply(_hl_bpkg, axis=1).format({
                    "FIFO 기준 ($/kg BP)":    _fmt_pk,
                    "이동평균 기준 ($/kg BP)": _fmt_pk,
                    "차이":                    _fmt_diff,
                }),
                use_container_width=True, hide_index=True,
            )
            _conv_avg = _tot_out / _tot_inp * 100 if _tot_inp > 0 else 0
            _rmc_gap  = abs(_rf_pk - _rm_pk)
            _gap_note = ""
            if _rmc_gap > 0.0001:
                _cheaper = "FIFO" if _rf_pk < _rm_pk else "이동평균"
                _gap_note = f" | 원료단가 차이 **${_rmc_gap:.4f}/kg BP** → {_cheaper}가 유리"
            st.caption(
                f"전환율 가중평균 **{_conv_avg:.1f}%** (스크랩 투입 → BP 생산)"
                + _gap_note
                + "  \n원료단가 기본값 변경·FIFO↔이동평균 전환은 아래 HBL별 손익 요약 섹션에서 가능합니다."
            )

        # ── 월별 손익 집계 (관리회계 기준 — 스크랩 매각·재매입 상계) ──────────
        _mon_agg2 = defaultdict(lambda: {"bp":0,"pf":0,"eu":0,"raw":0,"stor":0,"cnt":0,"out":0})
        for _mr in _ph_all:
            _msid  = _mr.get("shipment_id","")
            _ms    = _sm_pnl.get(_msid, {})
            _mld   = (_ms.get("loading_date") or "")[:7] or "미상"
            _mo    = _mr.get("output_kg",0) or 0
            _mi    = _ph_input_kg(_mr)
            _mpf   = (_mr.get("processing_fee_per_kg",0) or 0) * _mi   # 임가공비(순) — 스크랩 상계 후
            _meu   = _ph_export_usd(_mr, cfg)
            _mbp   = (_mr.get("bp_sale_per_kg",0) or 0) * _mo
            _mrc, _ = _get_rmc_fifo(_mr, _default_rmc_s1)
            # 보관비: 수동 storage_days 우선, 없으면 FIFO 자동 fallback
            _mstor = _ph_storage_cost(_mr, cfg) or _auto_storage_for_batch(_mr)
            _mon_agg2[_mld]["bp"]   += _mbp
            _mon_agg2[_mld]["pf"]   += _mpf
            _mon_agg2[_mld]["eu"]   += _meu
            _mon_agg2[_mld]["raw"]  += _mrc * _mi
            _mon_agg2[_mld]["stor"] += _mstor
            _mon_agg2[_mld]["cnt"]  += 1
            _mon_agg2[_mld]["out"]  += _mo
        if _mon_agg2:
            with st.expander("월별 손익 추이", expanded=True):
                _mon_rows2 = []
                for _mkey in sorted(_mon_agg2.keys()):
                    _mv2  = _mon_agg2[_mkey]
                    _mgp2 = _mv2["bp"] - _mv2["raw"] - _mv2["pf"]          # 매출총이익
                    _mr2  = _mgp2 - _mv2["eu"] - _mv2["stor"]              # 실질 손익
                    _mon_rows2.append({
                        "월":         _mkey,
                        "HBL수":      _mv2["cnt"],
                        "생산(kg)":   round(_mv2["out"], 0),
                        "매출(BP)":   round(_mv2["bp"], 2),
                        "원료 매입비": round(_mv2["raw"], 2),
                        "임가공비(순)": round(_mv2["pf"], 2),
                        "매출총이익": round(_mgp2, 2),
                        "수출비":     round(_mv2["eu"], 2),
                        "보관비":     round(_mv2["stor"], 2),
                        "실질 손익":  round(_mr2, 2),
                    })
                _df_mon2 = pd.DataFrame(_mon_rows2)
                # ── 트렌드 차트 (매출 ↑ / 비용 ↓ 쌓기 + 실질 손익 선) ──
                try:
                    st.plotly_chart(_fig_monthly_pnl([r for r in _mon_rows2 if r["월"] != "미상"], height=320),
                                    use_container_width=True)
                except (ImportError, Exception):
                    pass

                st.dataframe(_df_mon2, use_container_width=True, hide_index=True,
                             column_config=_cc_money("매출(BP)", "원료 매입비", "임가공비(순)", "매출총이익",
                                                     "수출비", "보관비", "실질 손익",
                                                     kg=("생산(kg)",), small=("HBL수",)))
                st.caption("매출총이익 = 매출 − 원료 매입비(FIFO 우선) − 임가공비(순)  |  "
                           "실질 손익 = 매출총이익 − 수출비 − 보관비  |  "
                           "스크랩 매각·BP 재매입은 상계, 간접 판관비·기타(기간 합계)는 월별 배분에서 제외. "
                           "원료단가 수동 기본값은 아래 '실질 손익 분석' 섹션에서 조정 가능합니다.")

if _page == PG_PNL and _sub == SUB_PNL_UNIT:

    # 보관비 헬퍼 (섹션 2·3 공용)
    _eff_storage = _pctx["eff_storage"]

    # ══════════════════════════════════════════════════════════════════════════
    # 섹션 2 — HBL별 손익 요약
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("#### HBL별 손익 요약")

    # 기본값 — linked 배치 없을 때 섹션 3에서 참조
    _rmc_mode    = "FIFO 우선"
    _default_rmc = 0.0

    _linked_pnl = [r for r in _ph_all if r.get("shipment_id","")]
    if not _linked_pnl:
        st.info("재고·임가공 > 임가공사·배치 > 세부 내역에서 배치를 HBL과 연결하면 선적 단위 손익이 표시됩니다.")
    else:
        # ── 컨트롤 ──────────────────────────────────────────────────────────
        _hc1, _hc2, _hc3 = st.columns([3, 2, 3])
        with _hc1:
            _rmc_mode = st.radio(
                "원료단가 기준",
                ["FIFO 우선", "이동평균 우선"],
                horizontal=True,
                key="rmc_mode_toggle",
                help="FIFO: 출고기록 Lot 원가 → 수동 → 이동평균  |  이동평균: 선적일 기준 → 수동 → FIFO",
            )
        with _hc2:
            _default_rmc = st.number_input(
                "원료단가 기본값 ($/kg)",
                value=0.0, step=0.001, format="%.4f", key="pnl_rmc_default",
                help="이동평균·FIFO 없는 배치에 적용. 0 = 미반영.",
            )

        # ── HBL별 집계 ──────────────────────────────────────────────────────
        _hbl_agg = {}
        for _rr in _linked_pnl:
            _hid    = _rr["shipment_id"]
            _hs     = _sm_pnl.get(_hid, {})
            _hb     = _bm_pnl.get(_hs.get("buyer_id",""), {})
            _op_r   = float(_rr.get("output_kg") or 0)
            _ip_r   = _ph_input_kg(_rr)
            _pf_r   = float(_rr.get("processing_fee_per_kg") or 0) * _ip_r
            _sc_r   = float(_rr.get("scrap_sale_per_kg") or 0) * _ip_r
            _eu_r   = _ph_export_usd(_rr, cfg)
            _bp_r   = float(_rr.get("bp_sale_per_kg") or 0) * _op_r
            # 스크랩 매각수익 ↔ 재매입원가의 스크랩 부분은 상계 →
            # 배치 손익 요소 = bp(매출) − pf(임가공비 순) − eu(수출비) − raw − stor
            _trade_r  = _bp_r - _pf_r - _eu_r
            if _rmc_mode == "이동평균 우선":
                _ermc_r, _rmc_src = _get_rmc_mavg(_rr, _default_rmc)
            else:
                _ermc_r, _rmc_src = _get_rmc_fifo(_rr, _default_rmc)
            _raw_r    = _ermc_r * _ip_r
            _stor_r   = _eff_storage(_rr)
            _stor_src = "수동" if _ph_storage_cost(_rr, cfg) else ("FIFO 자동" if _stor_r else "—")
            _real_r   = _trade_r - _raw_r - _stor_r
            _proc_nm  = _pm_pnl.get(_rr.get("processor_id",""), {}).get("name","—")
            _sc_nm    = _scm_pnl.get(_rr.get("scrap_type_id",""), {}).get("name","—")

            if _hid not in _hbl_agg:
                _hbl_agg[_hid] = {
                    "hbl":       _hs.get("hbl","—"),
                    "load_date": _hs.get("loading_date","—"),
                    "매입사":    f"{_hb.get('name','?')} ({_hb.get('product','?')})",
                    "procs":     set(),
                    "scrap_ids": set(),   # FIFO Lot 조회용
                    "out":  0.0, "bp_rev": 0.0, "pf": 0.0,
                    "eu":   0.0, "raw":    0.0,  "stor": 0.0,
                    "batches": [],
                }
            _h = _hbl_agg[_hid]
            _h["out"]    += _op_r
            _h["bp_rev"] += _bp_r;  _h["pf"]  += _pf_r
            _h["eu"]     += _eu_r;  _h["raw"] += _raw_r
            _h["stor"]   += _stor_r
            if _proc_nm != "—": _h["procs"].add(_proc_nm)
            if _rr.get("scrap_type_id"): _h["scrap_ids"].add(_rr["scrap_type_id"])
            _h["batches"].append({
                "임가공사":   _proc_nm,
                "스크랩":     _sc_nm,
                "BP(kg)":     round(_op_r, 0),
                "BP매각":     round(_bp_r, 2),
                "임가공비":   round(_pf_r, 2),
                "수출비":     round(_eu_r, 2),
                "원료비":     round(_raw_r, 2),
                "원가기준":   _rmc_src,
                "보관비":     round(_stor_r, 2) if _stor_r else None,
                "실질손익":   round(_real_r, 2),
            })

        # ── 요약 테이블 ──────────────────────────────────────────────────────
        _sum_rows = []
        for _hid, _h in sorted(_hbl_agg.items(),
                                key=lambda x: x[1]["load_date"], reverse=True):
            _hgp    = _h["bp_rev"] - _h["raw"] - _h["pf"]          # 매출총이익
            _hreal  = _hgp - _h["eu"] - _h["stor"]                 # 실질 손익
            _hmgr   = _hreal / _h["bp_rev"] * 100 if _h["bp_rev"] > 0 else None
            _sum_rows.append({
                "HBL":         _h["hbl"],
                "선적일":      _h["load_date"],
                "매입사":      _h["매입사"],
                "임가공사":    "·".join(sorted(_h["procs"])) or "—",
                "BP생산(kg)":  round(_h["out"], 0),
                "매출(BP)":    round(_h["bp_rev"], 2),
                "원료 매입비":  round(_h["raw"], 2),
                "임가공비(순)": round(_h["pf"], 2),
                "매출총이익":  round(_hgp, 2),
                "수출비":      round(_h["eu"], 2),
                "보관비":      round(_h["stor"], 2) if _h["stor"] else None,
                "실질 손익":   round(_hreal, 2),
                "마진율(%)":   round(_hmgr, 2) if _hmgr is not None else None,
            })

        st.dataframe(
            pd.DataFrame(_sum_rows), use_container_width=True, hide_index=True,
            column_config=_cc_money("매출(BP)", "원료 매입비", "임가공비(순)", "매출총이익", "수출비",
                                    "보관비", "실질 손익", kg=("BP생산(kg)",), pct=("마진율(%)",)),
        )

        # Excel 다운로드
        try:
            _xl_buf = BytesIO()
            with pd.ExcelWriter(_xl_buf, engine="openpyxl") as _xew:
                pd.DataFrame(_sum_rows).to_excel(_xew, index=False, sheet_name="HBL손익요약")
            _xl_buf.seek(0)
            st.download_button(
                "📥 Excel 다운로드",
                data=_xl_buf,
                file_name=f"HBL_손익요약_{date.today():%Y%m%d}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception:
            pass

        _tot_real_hbl = sum(
            (_h["bp_rev"] - _h["pf"] - _h["eu"]) - _h["raw"] - _h["stor"]
            for _h in _hbl_agg.values()
        )
        _fm1, _fm2 = st.columns(2)
        _fh_col = "#4ade80" if _tot_real_hbl >= 0 else "#f87171"
        _unlinked = len(_ph_all) - len(_linked_pnl)
        _fm1.markdown(_kpi_card("전체 HBL 합산 실질 손익", f"${_tot_real_hbl:+,.0f}", val_color=_fh_col), unsafe_allow_html=True)
        _fm2.markdown(_kpi_card_badge("미연결 배치", f"{_unlinked}건", "#fb923c" if _unlinked else "#4ade80",
                                  f"{_unlinked}건", "재고·임가공 > 임가공사·배치에서 HBL 연결"), unsafe_allow_html=True)

        _pv = st.radio("보기 기준", ["HBL별", "매입사별", "임가공사별"], horizontal=True, key="pnl_view")
        if _pv == "HBL별":
            # ── HBL별 카드 ──────────────────────────────────────────────────────
            st.markdown("---")
            for _hid, _h in sorted(_hbl_agg.items(),
                                    key=lambda x: x[1]["load_date"], reverse=True):
                _hgp    = _h["bp_rev"] - _h["raw"] - _h["pf"]   # 매출총이익
                _hreal  = _hgp - _h["eu"] - _h["stor"]          # 실질 손익
                _hmgr   = _hreal / _h["bp_rev"] * 100 if _h["bp_rev"] > 0 else 0
                _icon   = "🟢" if _hreal >= 0 else "🔴"
                _pnl_color = "🟢" if _hreal >= 0 else "🔴"
                with st.expander(
                    f"{_pnl_color}  {_h['hbl']}  ·  {_h['매입사']}"
                    f"  │  {_h['load_date']}"
                    f"  │  임가공비 \\${_h['pf']:,.0f}"
                    f"  │  실질손익 \\${_hreal:+,.0f}  ({_hmgr:+.1f}%)",
                    expanded=False,
                ):
                    _cl, _cr = st.columns([5, 7])
                    with _cl:
                        st.markdown("**손익 분해**")
                        _wf_df = pd.DataFrame([
                            ("BP 매각 (매출)",       _h["bp_rev"]),
                            ("  (−) 원료 매입비",    -_h["raw"]),
                            ("  (−) 임가공비 (순)",  -_h["pf"]),
                            ("= 매출총이익",          _hgp),
                            ("  (−) 수출비",         -_h["eu"]),
                            ("  (−) 보관비",         -_h["stor"]),
                            ("= 실질 손익",           _hreal),
                        ], columns=["항목", "금액 (USD)"])

                        def _hl_wf(row):
                            lbl = row["항목"]
                            v   = row["금액 (USD)"]
                            if "실질 손익" in lbl:
                                bg = "#1E8449" if v >= 0 else "#922b21"
                                return ["font-weight:700",
                                        f"background-color:{bg};color:white;font-weight:700"]
                            if lbl.startswith("="):
                                return ["font-weight:700", "font-weight:700"]
                            return ["color:#666", ""]

                        st.dataframe(
                            _wf_df.style.apply(_hl_wf, axis=1)
                                  .format({"금액 (USD)": "${:+,.2f}"}),
                            use_container_width=True, hide_index=True, height=280,
                        )
                        _mk1, _mk2 = st.columns(2)
                        _mg_col = "#4ade80" if _hreal >= 0 else "#f87171"
                        _mk1.markdown(_kpi_card("BP 생산",  f"{_h['out']/1000:.2f} MT"), unsafe_allow_html=True)
                        _mk2.markdown(_kpi_card("수익률",   f"{_hmgr:+.1f}%", val_color=_mg_col), unsafe_allow_html=True)
                    with _cr:
                        st.markdown("**배치 상세**")
                        _df_bat = pd.DataFrame(_h["batches"])

                        def _hl_bat(row):
                            styles = [""] * len(row)
                            _bc = list(row.index)
                            v   = row.get("실질손익", 0) or 0
                            src = row.get("원가기준", "")
                            if "실질손익" in _bc:
                                styles[_bc.index("실질손익")] = (
                                    "color:#1E8449;font-weight:600" if v >= 0
                                    else "color:#922b21;font-weight:600")
                            if "원가기준" in _bc:
                                styles[_bc.index("원가기준")] = (
                                    "color:#1565c0;font-weight:600" if src == "FIFO"
                                    else "color:#6c757d")
                            return styles

                        st.dataframe(
                            _df_bat.style.apply(_hl_bat, axis=1).format(na_rep="—", formatter={
                                "BP(kg)":   "{:,.0f}",
                                "BP매각":   "${:,.2f}",
                                "임가공비": "${:,.2f}",
                                "수출비":   "${:,.2f}",
                                "원료비":   "${:,.2f}",
                                "보관비":   lambda v: f"${v:,.2f}" if v else "—",
                                "실질손익": "${:+,.2f}",
                            }),
                            use_container_width=True, hide_index=True,
                        )

                        # ── 원료 Lot 구성 ──────────────────────────────────────
                        st.markdown("**📦 원료 Lot 구성 (FIFO)**")
                        _lot_any = False
                        for _lot_scid in sorted(_h.get("scrap_ids", set())):
                            _lot_sc_nm = _scm_pnl.get(_lot_scid, {}).get("name", "?")
                            try:
                                _lot_bl, _, _ = _fifo_lot_trace(cfg, _lot_scid)
                                _lot_data = _lot_bl.get(_hid, {}).get("lots", {})
                                if not _lot_data:
                                    continue
                                _lot_total_qty = sum(v["qty"] for v in _lot_data.values())
                                _lot_rows = []
                                for _lot_lbl, _lv in sorted(
                                    _lot_data.items(),
                                    key=lambda x: x[1].get("lot_date") or ""
                                ):
                                    _lot_qty  = _lv["qty"]
                                    _lot_pct  = _lot_qty / _lot_total_qty * 100 if _lot_total_qty else 0
                                    _lot_date = (_lv.get("lot_date") or "")[:7] or ("기초재고" if "기초재고" in _lot_lbl else "—")
                                    _lot_uc   = _lv.get("unit_cost")
                                    _lot_rows.append({
                                        "입고월":     _lot_date,
                                        "Lot":        _lot_lbl,
                                        "소진량(kg)": round(_lot_qty, 0),
                                        "비중(%)":    round(_lot_pct, 1),
                                        "원료단가":   _lot_uc,
                                    })
                                if _lot_rows:
                                    _lot_any = True
                                    if len(_h.get("scrap_ids", set())) > 1:
                                        st.caption(f"**{_lot_sc_nm}**")
                                    st.dataframe(
                                        pd.DataFrame(_lot_rows).style.format(na_rep="—", formatter={
                                            "소진량(kg)": "{:,.0f}",
                                            "비중(%)":    "{:.1f}%",
                                            "원료단가":   lambda v: f"${v:.4f}" if v is not None else "—",
                                        }),
                                        use_container_width=True, hide_index=True,
                                    )
                            except Exception:
                                pass
                        if not _lot_any:
                            st.caption("FIFO Lot 정보 없음 (원료 입출고 서브페이지에서 출고 기록 입력 필요)")

        if _pv == "매입사별":
            # ── 매입사별 수익성 비교 ─────────────────────────────────────────────
            # HBL 집계(_hbl_agg)를 매입사 단위로 재집계 — 원료단가 기준(FIFO/이동평균)
            # 토글이 이미 반영된 값이므로 위 HBL 요약과 항상 일치한다.
            st.markdown("---")
            st.markdown("#### 매입사별 수익성 비교")
            st.caption("HBL 연결 배치 기준. kg당 수치는 BP 생산량 기준이며, 판관비는 제외됩니다.")

            _by_agg = defaultdict(lambda: {"hbl": 0, "out": 0.0, "bp": 0.0, "pf": 0.0,
                                           "eu": 0.0, "raw": 0.0, "stor": 0.0})
            for _h in _hbl_agg.values():
                _ba = _by_agg[_h["매입사"]]
                _ba["hbl"]  += 1
                _ba["out"]  += _h["out"]
                _ba["bp"]   += _h["bp_rev"]
                _ba["pf"]   += _h["pf"]
                _ba["eu"]   += _h["eu"]
                _ba["raw"]  += _h["raw"]
                _ba["stor"] += _h["stor"]

            _by_rows = []
            for _bn, _bv in _by_agg.items():
                _bgp   = _bv["bp"] - _bv["raw"] - _bv["pf"]
                _breal = _bgp - _bv["eu"] - _bv["stor"]
                _by_rows.append({
                    "매입사":       _bn,
                    "HBL":          _bv["hbl"],
                    "BP생산(kg)":   round(_bv["out"], 0),
                    "매출(BP)":     round(_bv["bp"], 2),
                    "매출총이익":   round(_bgp, 2),
                    "실질 손익":    round(_breal, 2),
                    "매출단가/kg":  round(_bv["bp"] / _bv["out"], 4) if _bv["out"] > 0 else None,
                    "실질손익/kg":  round(_breal / _bv["out"], 4) if _bv["out"] > 0 else None,
                    "마진율(%)":    round(_breal / _bv["bp"] * 100, 2) if _bv["bp"] > 0 else None,
                })
            _by_rows.sort(key=lambda r: (r["실질손익/kg"] is None, -(r["실질손익/kg"] or 0)))

            st.dataframe(
                pd.DataFrame(_by_rows), use_container_width=True, hide_index=True,
                column_config=_cc_money("매출(BP)", "매출총이익", "실질 손익",
                                        kg=("BP생산(kg)",), pct=("마진율(%)",),
                                        perkg=("매출단가/kg", "실질손익/kg")),
            )

            # 실질손익/kg 막대 차트 — 매입사 간 단위 수익성 비교
            try:
                import plotly.graph_objects as go
                _bc_names = [r["매입사"] for r in _by_rows if r["실질손익/kg"] is not None]
                _bc_vals  = [r["실질손익/kg"] for r in _by_rows if r["실질손익/kg"] is not None]
                if len(_bc_names) >= 2:
                    _fig_by = go.Figure(go.Bar(
                        x=_bc_names, y=_bc_vals,
                        marker_color=[_C_POS if v >= 0 else _C_NEG for v in _bc_vals],
                        text=[f"${v:+.4f}" for v in _bc_vals],
                        textposition="outside", textfont=dict(size=10),
                        hovertemplate="%{x}<br>$%{y:+.4f}/kg<extra></extra>",
                    ))
                    _fig_by.add_hline(y=0, line_color="rgba(255,255,255,0.25)", line_width=1)
                    st.plotly_chart(_fig_style(_fig_by, height=280, legend=False, y_fmt="$,.2f",
                                               title="실질 손익 ($/kg BP) — 매입사별"),
                                    use_container_width=True)
            except ImportError:
                pass

        if _pv == "임가공사별":
            # ── 임가공사별 수익성 비교 ─────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### 임가공사별 수익성 비교")
            st.caption("HBL 연결 배치 기준 · 위 원료단가 기준 토글 반영 · 판관비 제외")
            _pr_src = [x for x in _batch_pnl_rows(cfg, _pctx, _rmc_mode, _default_rmc) if x["sid"]]
            _pr_rows = []
            for _pn, _pv in _pnl_agg(_pr_src, lambda x: x["proc_nm"]).items():
                _pgp   = _pv["bp"] - _pv["raw"] - _pv["pf"]
                _preal = _pgp - _pv["eu"] - _pv["stor"]
                _pr_rows.append({
                    "임가공사": _pn, "배치": _pv["cnt"],
                    "투입(kg)": round(_pv["inp"], 0), "생산(kg)": round(_pv["out"], 0),
                    "실제 전환율(%)": round(_pv["out"] / _pv["inp"] * 100, 2) if _pv["inp"] > 0 else None,
                    "임가공비(순)":   round(_pv["pf"], 2),
                    "임가공비/kg BP": round(_pv["pf"] / _pv["out"], 4) if _pv["out"] > 0 else None,
                    "매출총이익":     round(_pgp, 2),
                    "실질 손익":      round(_preal, 2),
                    "실질손익/kg":    round(_preal / _pv["out"], 4) if _pv["out"] > 0 else None,
                })
            _pr_rows.sort(key=lambda r: (r["실질손익/kg"] is None, -(r["실질손익/kg"] or 0)))
            if _pr_rows:
                st.dataframe(pd.DataFrame(_pr_rows), use_container_width=True, hide_index=True,
                             column_config=_cc_money("임가공비(순)", "매출총이익", "실질 손익",
                                                     kg=("투입(kg)", "생산(kg)"),
                                                     perkg=("임가공비/kg BP", "실질손익/kg"),
                                                     pct=("실제 전환율(%)",)))
                st.caption("임가공비 단가 변동 시나리오는 손익·시나리오 > 민감도에서 계산할 수 있습니다.")

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # 섹션 3 — 실질 손익 분석 (전체)
    # ══════════════════════════════════════════════════════════════════════════
    with st.expander("실질 손익 분석 (전체) — 판관비 반영 · 원료단가 수동 기본값", expanded=False):
        # 손익 요약 서브페이지와 같은 합계 (서브페이지가 분리되어 여기서 다시 계산)
        _tot_pf = sum((r.get("processing_fee_per_kg",0) or 0) * _ph_input_kg(r) for r in _ph_all)
        _tot_eu = sum(_ph_export_usd(r, cfg) for r in _ph_all)
        _tot_bp = sum((r.get("bp_sale_per_kg",0) or 0) * (r.get("output_kg",0) or 0) for r in _ph_all)
        st.caption("매출총이익(매출 − 원료 취득원가 − 임가공비 순)에서 수출비·보관비·판관비를 차감한 "
                   "영업이익(실질 손익)입니다. 원료단가 기준은 위 HBL 요약과 동기화됩니다.")

        if not _ph_all:
            st.info("처리 이력을 입력하면 실질 손익 분석이 가능합니다.")
        else:
            # ── 원료 원가 기준 안내 ──
            _inv_avail_pnl = {}
            for _isc_p in cfg.get("scrap_types", []):
                _avg_p, _ = _inv_moving_avg(cfg, _isc_p["id"])
                if _avg_p is not None:
                    _inv_avail_pnl[_isc_p["name"]] = (_isc_p["id"], _avg_p)
            _has_dispatch_any = bool(cfg.get("dispatch_records", []))
            if _has_dispatch_any:
                st.info("📦 원료단가 적용 우선순위: **FIFO** (출고 기록 탭) → 수동 입력 → 이동평균 → 수동 기본값  \n"
                        "출고 기록이 완전히 입력된 B/L은 FIFO 원가가 자동 적용됩니다.")
            elif _inv_avail_pnl:
                _avg_parts = [f"**{nm}** \\${avg:.4f}/kg" for nm, (_, avg) in _inv_avail_pnl.items()]
                st.info("📊 이동평균 자동 적용 중 — " + " | ".join(_avg_parts)
                        + "  _(출고 기록 탭에서 임가공 출고를 입력하면 FIFO 원가로 자동 전환됩니다)_")

            # 간접 판관비·기타 원가 — cfg에 월별로 저장된 값의 합계 (예전엔 세션 입력값이라 접속마다 0으로 리셋됐음)
            _sga_total, _other_cost = _sga_totals(cfg)
            _sga_months = len(cfg.get("sga_monthly", []))
            st.caption(f"간접 판관비 **\\${_sga_total:,.0f}** · 기타 원가 **\\${_other_cost:,.0f}** "
                       f"({_sga_months}개월 등록 — 마스터·동기화 > INDEX·환율·판관비에서 월별 입력)"
                       + ("  ⚠️ 판관비 미등록: 영업이익이 판관비 0으로 계산됩니다." if not _sga_months else ""))

            # 배치별 원료비 집계 (_rmc_mode·_default_rmc 는 섹션 2 컨트롤과 동기화)
            if _rmc_mode == "이동평균 우선":
                _tot_raw = sum(_get_rmc_mavg(r, _default_rmc)[0] * _ph_input_kg(r) for r in _ph_all)
            else:
                _tot_raw = sum(_get_rmc_fifo(r, _default_rmc)[0] * _ph_input_kg(r) for r in _ph_all)
            _tot_storage = sum(_eff_storage(r) for r in _ph_all)
            _auto_stor_cnt = sum(1 for r in _ph_all
                                 if not _ph_storage_cost(r, cfg)
                                 and _auto_storage_for_batch(r) > 0)

            # 적용 기준별 카운트
            _rmc_fifo_cnt   = sum(1 for r in _ph_all
                                  if _fifo_rmc_map.get((r.get("scrap_type_id",""),
                                      r.get("shipment_id","") or f"__no_ship__{r.get('id','')}"
                                  )) is not None)
            _rmc_stored_cnt = sum(1 for r in _ph_all
                                  if r.get("raw_material_cost_per_kg") is not None
                                  and _fifo_rmc_map.get((r.get("scrap_type_id",""),
                                      r.get("shipment_id","") or f"__no_ship__{r.get('id','')}"
                                  )) is None)
            _rmc_auto_cnt   = sum(1 for r in _ph_all
                                  if r.get("raw_material_cost_per_kg") is None
                                  and _fifo_rmc_map.get((r.get("scrap_type_id",""),
                                      r.get("shipment_id","") or f"__no_ship__{r.get('id','')}"
                                  )) is None
                                  and _inv_moving_avg(
                                      cfg, r.get("scrap_type_id",""),
                                      _sm_pnl.get(r.get("shipment_id",""),{}).get("loading_date")
                                  )[0] is not None)
            _rmc_dflt_cnt   = len(_ph_all) - _rmc_fifo_cnt - _rmc_stored_cnt - _rmc_auto_cnt

            # 관리회계 단계 (섹션1과 동일 기준 — 스크랩 매각·재매입 상계)
            _gp_r        = _tot_bp - _tot_raw - _tot_pf                       # 매출총이익
            _real_net_r  = _gp_r - _tot_eu - _tot_storage - _sga_total - _other_cost   # 영업이익(실질)
            _real_pct_r  = _real_net_r / _tot_bp * 100 if _tot_bp > 0 else 0
            _gp_pct_r    = _gp_r / _tot_bp * 100 if _tot_bp > 0 else 0

            # 원료비 적용 현황 안내
            _rmc_parts = []
            if _rmc_fifo_cnt   > 0: _rmc_parts.append(f"**{_rmc_fifo_cnt}건 FIFO**")
            if _rmc_stored_cnt > 0: _rmc_parts.append(f"{_rmc_stored_cnt}건 수동 입력")
            if _rmc_auto_cnt   > 0: _rmc_parts.append(f"{_rmc_auto_cnt}건 이동평균 자동")
            if _rmc_dflt_cnt   > 0 and _default_rmc > 0:
                _rmc_parts.append(f"{_rmc_dflt_cnt}건 수동 기본값(${_default_rmc:.4f})")
            if _rmc_parts:
                st.caption("📌 원료비 적용 기준: " + " / ".join(_rmc_parts)
                           + "  _(FIFO = 출고 기록 탭 dispatch_records 기반)_")
            if _rmc_dflt_cnt > 0 and _default_rmc == 0 and not _inv_avail_pnl and not _fifo_sc_ids_avail:
                st.warning(f"⚠️ {_rmc_dflt_cnt}건의 배치에 원료 원료단가가 없습니다. "
                           "출고 기록 탭에서 임가공 출고를 입력하거나, 스크랩 유형 관리 탭에서 기초재고를 설정하세요.")

            st.markdown("---")
            _ra1, _ra2, _ra3, _ra4, _ra5, _ra6 = st.columns(6)
            _gp_sub  = f"매출 대비 {_gp_pct_r:+.1f}%" if _tot_bp > 0 else ""
            _stor_sub = f"{_auto_stor_cnt}건 FIFO 자동" if _auto_stor_cnt else "미입력"
            _rn_col  = "#4ade80" if _real_net_r >= 0 else "#f87171"
            _gp_col  = "#4ade80" if _gp_r >= 0 else "#f87171"
            _ra1.markdown(_kpi_card("매출총이익",         f"${_gp_r:+,.0f}", _gp_sub,
                                    val_color=_gp_col), unsafe_allow_html=True)
            _ra2.markdown(_kpi_card("수출비",             f"−${_tot_eu:,.0f}"),      unsafe_allow_html=True)
            _ra3.markdown(_kpi_card("보관비",             f"−${_tot_storage:,.0f}", _stor_sub), unsafe_allow_html=True)
            _ra4.markdown(_kpi_card("간접 판관비",        f"−${_sga_total:,.0f}"),  unsafe_allow_html=True)
            _ra5.markdown(_kpi_card("기타 원가",          f"−${_other_cost:,.0f}"), unsafe_allow_html=True)
            _ra6.markdown(_kpi_card("영업이익 (실질)",    f"${_real_net_r:+,.0f}",
                                    f"영업이익률 {_real_pct_r:+.1f}%", val_color=_rn_col), unsafe_allow_html=True)
            st.caption("매출총이익 = 매출 − 원료 취득원가 − 임가공비(순). "
                       "원료 취득원가 상세는 위 HBL별 손익 요약의 원료단가 기준(FIFO/이동평균)을 따릅니다.")

if _page == PG_PNL and _sub == SUB_PNL_TH:

    # ══════════════════════════════════════════════════════════════════════════
    # 섹션 4 — 이론 마진
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("#### 이론 마진")

    # INDEX 월 선택
    _th_idx_opts = [h["month"] for h in sorted(
        cfg.get("index_history", []), key=lambda x: x["month"], reverse=True)]
    _th_c1, _th_c2, _th_c3 = st.columns([2, 2, 4])
    with _th_c1:
        _th_ref = st.selectbox("INDEX 기준월", _th_idx_opts if _th_idx_opts else ["—"], key="pnl_th_ref")
    _hm = {h["month"]: h for h in cfg.get("index_history", [])}
    if _th_ref in _hm:
        _th_NI = _hm[_th_ref]["ni_index"]
        _th_CO = _hm[_th_ref]["co_index"]
    else:
        _th_NI, _th_CO = NI, CO
    with _th_c2:
        st.markdown(_kpi_card("Ni INDEX", f"${_th_NI:,.2f}"), unsafe_allow_html=True)
    with _th_c3:
        st.markdown(_kpi_card("Co INDEX", f"${_th_CO:,.2f}"), unsafe_allow_html=True)

    st.caption(
        "💡 스크랩 매각 ↔ BP 재매입이 상계되므로  "
        "**순 재매입 원가 = 임가공비 ÷ 전환율** (스크랩 단가 무관)  →  "
        "**이론 마진 = 매입사 BP 매각단가 − 임가공비/전환율**  "
        "⚠️ 이론 마진에는 **수출비·원료비 미포함**. 이론 vs 실적 비교는 동일 기준(수출비 제외)으로 계산됩니다."
    )

    if not active_buyers or not active_procs:
        st.info("매입사와 임가공사를 등록하면 이론 마진이 표시됩니다.")
    else:
        # 스크랩 → 출력 제품 결정 (양극 → BP, 나머지 → BM)
        def _sc_product(sc):
            # 스크랩 유형 관리의 '생산 제품' 필드 우선, 없으면 이름 추정(구데이터 호환)
            return sc.get("product") or ("BP" if ("양극" in sc.get("name","") or sc.get("id","") == "cathode") else "BM")

        # 매입사별 현재 단가 사전 계산 (product별 분리, 선택 INDEX 적용)
        _buyer_sale_bp = {}   # BP 매입사
        _buyer_sale_bm = {}   # BM 매입사
        for _b in active_buyers:
            _, _, _, _bskg = bp_price(_th_NI, _th_CO, _b["ni_content"], _b["co_content"],
                                      _b["ni_payable"], _b["co_payable"])
            _entry = (_b["name"], _b["product"], round(_bskg, 5))
            if _b["product"] == "BP":
                _buyer_sale_bp[_b["id"]] = _entry
            else:
                _buyer_sale_bm[_b["id"]] = _entry

        def _color_margin(val):
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return ""
            return ("background-color:#1E5C35;color:#A8F0C0;font-weight:600" if val > 0
                    else "background-color:#5C1E1E;color:#F0A8A8;font-weight:600")

        def _build_th_table(scraps, buyer_map, label):
            """임가공사×스크랩 조합 + 매입사별 마진 테이블 생성"""
            if not scraps or not buyer_map:
                return
            _buyer_cols_local = [f"{n} [{p}]" for _, (n, p, _) in buyer_map.items()]
            _rows = []
            for _proc in active_procs:
                for _sc in scraps:
                    _cnd = _proc.get("conditions", {}).get(_sc["id"], {})
                    _pf  = _cnd.get("processing_fee"); _cv = _cnd.get("conversion_rate")
                    # 순 재매입 원가 = 임가공비 ÷ 전환율 (스크랩 상계)
                    _bmc = _pf / (_cv/100) if (_pf is not None and _cv and _cv>0) else None
                    row  = {
                        "임가공사":           _proc["name"],
                        "스크랩 유형":        _sc["name"],
                        "전환율(%)":          _cv,
                        "임가공비($/kg 투입)": _pf,
                        "순 재매입원가/kg BP": round(_bmc, 4) if _bmc is not None else None,
                    }
                    for _bid, (_bname, _bprod, _bskg) in buyer_map.items():
                        _col = f"{_bname} [{_bprod}]"
                        row[_col] = round(_bskg - _bmc, 4) if _bmc is not None else None
                    _rows.append(row)
            if not _rows:
                return
            _df = pd.DataFrame(_rows)
            _fmt = {
                "전환율(%)":           lambda v: f"{v}%" if v is not None else "—",
                "임가공비($/kg 투입)": lambda v: f"${v}" if v is not None else "—",
                "순 재매입원가/kg BP": lambda v: f"${v:.4f}" if v is not None else "—",
            }
            for _bc in _buyer_cols_local:
                _fmt[_bc] = lambda v: f"${v:+.4f}" if v is not None else "—"
            st.markdown(f"**{label}**")
            st.dataframe(
                _df.style.map(_color_margin, subset=_buyer_cols_local)
                         .format(na_rep="—", formatter=_fmt),
                use_container_width=True, hide_index=True
            )
            return _rows   # 이론 vs 실적 비교에서 재사용

        st.divider()
        _bp_scraps = [s for s in active_scraps if _sc_product(s) == "BP"]
        _bm_scraps = [s for s in active_scraps if _sc_product(s) == "BM"]
        _th_rows_bp = _build_th_table(_bp_scraps, _buyer_sale_bp, "🔵 BP 계열 (양극)")
        _th_rows_bm = _build_th_table(_bm_scraps, _buyer_sale_bm, "🟢 BM 계열 (젤리롤 · 셀 · 모듈)")
        _th_rows_all = (_th_rows_bp or []) + (_th_rows_bm or [])

        # ── 이론 vs 실적 비교 ───────────────────────────────────────────────
        if _linked_pnl:
            st.divider()
            st.markdown("##### 이론 vs 실적 비교")
            st.caption("실제 선적 이력 기준 — HBL에 연결된 매입사의 현재 단가를 이론값으로 사용")
            _cmp_rows = []
            for _rp2 in _linked_pnl:
                _pp2   = _pm_pnl.get(_rp2.get("processor_id",""), {})
                _ss2   = _scm_pnl.get(_rp2.get("scrap_type_id",""), {})
                _ship2 = _sm_pnl.get(_rp2.get("shipment_id",""), {})
                _actual_bid   = _rp2.get("buyer_id") or _ship2.get("buyer_id","")
                _actual_buyer = _bm_pnl.get(_actual_bid, {})
                # 이론 BP/BM 단가 (실제 매입사 기준, 선택 INDEX 적용)
                _th_bskg = None
                if _actual_buyer.get("ni_payable"):
                    _, _, _, _th_bskg = bp_price(
                        _th_NI, _th_CO,
                        _actual_buyer.get("ni_content", 0),
                        _actual_buyer.get("co_content", 0),
                        _actual_buyer["ni_payable"],
                        _actual_buyer["co_payable"],
                    )
                # 이론 재매입 원가 = 임가공비 ÷ 전환율 (스크랩 상계)
                _cnd2 = _pp2.get("conditions",{}).get(_ss2.get("id",""),{}) if _pp2 else {}
                _pf_c = _cnd2.get("processing_fee"); _cv_c = _cnd2.get("conversion_rate")
                _bmc2 = _pf_c / (_cv_c/100) if (_pf_c is not None and _cv_c and _cv_c>0) else None
                _th_mg2 = round(_th_bskg - _bmc2, 5) if (_th_bskg and _bmc2) else None
                # 실적 — 수출비 포함/미포함 마진 분리 계산
                _op2  = _rp2.get("output_kg",0) or 0
                _ip2  = _ph_input_kg(_rp2)
                _sc2  = (_rp2.get("scrap_sale_per_kg",0) or 0) * _ip2
                _pf2  = (_rp2.get("processing_fee_per_kg",0) or 0) * _ip2
                _repr2= _sc2 + _pf2   # BP 재매입원가
                _eu2_total = _ph_export_usd(_rp2, cfg)
                _epk2 = _eu2_total / _op2 if _op2>0 else 0
                _bp2  = _rp2.get("bp_sale_per_kg",0) or 0
                # 실적 마진(수출비 제외) — 이론 마진과 동일 기준으로 비교
                _repr2_per_kg = _repr2 / _op2 if _op2>0 else 0
                _sc2_per_kg   = _sc2 / _op2 if _op2>0 else 0
                _act_mg2_noex = _bp2 + _sc2_per_kg - _repr2_per_kg   # 수출비 미포함
                _act_mg2      = _act_mg2_noex - _epk2                 # 수출비 포함
                _diff2 = round(_act_mg2_noex - _th_mg2, 5) if _th_mg2 is not None else None
                _cmp_rows.append({
                    "HBL":                  _ship2.get("hbl","—"),
                    "매입사":               f"{_actual_buyer.get('name','?')} ({_actual_buyer.get('product','?')})",
                    "임가공사":             _pp2.get("name","—"),
                    "스크랩":               _ss2.get("name","—"),
                    "이론 BP단가":          round(_th_bskg,5) if _th_bskg else None,
                    "이론 재매입원가/kg":   round(_bmc2,5) if _bmc2 else None,
                    "이론 마진($/kg)":      _th_mg2,
                    "실적 마진/kg(수출 제외)": round(_act_mg2_noex,5),
                    "수출비/kg":            round(_epk2,5),
                    "실적 마진/kg(수출 포함)": round(_act_mg2,5),
                    "이론대비 차이":        _diff2,
                })
            _df_cmp = pd.DataFrame(_cmp_rows)
            st.caption("💡 **이론 마진** = 매입사 단가 − 임가공비/전환율 (수출비 미포함)  "
                       "| **차이** = 실적 마진(수출 제외) − 이론 마진  (양수 = 이론보다 좋음)")
            def _hl_cmp(row):
                v = row.get("이론대비 차이")
                if v is None: return [""]*len(row)
                c = ("background-color:#1E5C35;color:#A8F0C0;font-weight:600" if v>=0
                     else "background-color:#5C1E1E;color:#F0A8A8;font-weight:600")
                return [""]*(len(row)-1) + [c]
            st.dataframe(_df_cmp.style.apply(_hl_cmp, axis=1).format(na_rep="—", formatter={
                "이론 BP단가":             lambda v: f"${v:.4f}" if v else "—",
                "이론 재매입원가/kg":      lambda v: f"${v:.4f}" if v else "—",
                "이론 마진($/kg)":         lambda v: f"${v:+.4f}" if v else "—",
                "실적 마진/kg(수출 제외)": "${:+.4f}",
                "수출비/kg":               "${:.4f}",
                "실적 마진/kg(수출 포함)": "${:+.4f}",
                "이론대비 차이":           lambda v: f"${v:+.4f}" if v else "—",
            }), use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════════════════
    # 섹션 5 — 직접 판매 손익
    # ══════════════════════════════════════════════════════════════════════════
if _page == PG_PNL and _sub == SUB_PNL_DS:
    st.markdown("#### 직접 판매 손익")
    st.caption("직접 판매 스크랩의 매각 수익 및 FIFO 원가 대비 손익을 분석합니다.")

    _ds_all = cfg.get("direct_sales", [])
    if not _ds_all:
        st.info("직접 판매 이력이 없습니다. 원료 입출고 서브페이지에서 추가하세요.")
    else:
        _ds_with_price = [ds for ds in _ds_all if ds.get("sale_price_per_kg") is not None]
        if not _ds_with_price:
            st.info("직접 판매 단가(sale_price_per_kg)가 등록된 건이 없습니다. "
                    "원료 입출고 서브페이지의 직접 판매 섹션에서 단가를 입력하세요.")
        else:
            # FIFO 원가 계산 (기초재고 있는 유형만)
            _ds_fifo_sc_ids = {
                ds.get("scrap_type_id","") for ds in _ds_with_price
                if cfg.get("raw_material_inventory",{}).get(ds.get("scrap_type_id",""),{}).get("opening")
            }
            _ds_fifo_cost_map = {}   # (sc_id, ds_id) → FIFO $/kg (from bl_result)
            for _dsc in _ds_fifo_sc_ids:
                _, _d_events, _ = _fifo_lot_trace(cfg, _dsc)
                for _dev in _d_events:
                    if _dev["type"] == "직접판매":
                        # sum weighted FIFO cost for this direct_sale event
                        _d_total_qty = sum(a["qty"] for a in _dev["attributions"])
                        _d_total_amt = sum(a["qty"] * a.get("unit_cost", 0) for a in _dev["attributions"])
                        if _d_total_qty > 0:
                            _ds_fifo_cost_map[(_dsc, _dev.get("id",""))] = _d_total_amt / _d_total_qty

            _ds_rows_pnl = []
            _ds_scm = {s["id"]: s["name"] for s in cfg.get("scrap_types", [])}
            for ds in sorted(_ds_with_price, key=lambda x: x.get("date","")):
                _dqty   = float(ds.get("quantity_kg", 0))
                _dspkg  = float(ds.get("sale_price_per_kg", 0) or 0)
                _drev   = _dspkg * _dqty
                _sc_id  = ds.get("scrap_type_id","")
                # FIFO 원가 — 이벤트 ref_id 매칭
                _fifo_cpkg = _ds_fifo_cost_map.get((_sc_id, ds.get("id","")))
                # 이동평균 단가 fallback
                _mavg_cpkg, _ = _inv_moving_avg(cfg, _sc_id)
                _cost_cpkg = _fifo_cpkg if _fifo_cpkg is not None else (_mavg_cpkg or 0)
                _cost_src  = "FIFO" if _fifo_cpkg is not None else ("이동평균" if _mavg_cpkg else "—")
                _dcost  = _cost_cpkg * _dqty
                _dnet   = _drev - _dcost
                _dmg    = _dnet / _drev * 100 if _drev > 0 else None
                _ds_rows_pnl.append({
                    "판매일":        ds.get("date",""),
                    "스크랩 유형":   _ds_scm.get(_sc_id, "—"),
                    "판매량 (kg)":   _dqty,
                    "단가 ($/kg)":   _dspkg,
                    "매출액 (USD)":  round(_drev, 2),
                    "원가 ($/kg)":   round(_cost_cpkg, 4) if _cost_cpkg else None,
                    "원가 산출":     _cost_src,
                    "원가 합계 (USD)": round(_dcost, 2) if _dcost else None,
                    "거래 마진 (USD)": round(_dnet, 2),
                    "거래 마진률 (%)": round(_dmg, 2) if _dmg is not None else None,
                })

            _df_ds_pnl = pd.DataFrame(_ds_rows_pnl)
            def _hl_ds(row):
                v = row.get("거래 마진 (USD)", 0) or 0
                c = ("background-color:#1E8449;color:white;font-weight:600" if v >= 0
                     else "background-color:#922b21;color:white;font-weight:600")
                return [""] * (len(row) - 2) + [c, ""]
            st.dataframe(
                _df_ds_pnl.style.apply(_hl_ds, axis=1).format(na_rep="—", formatter={
                    "판매량 (kg)":      "{:,.0f}",
                    "단가 ($/kg)":      "${:.4f}",
                    "매출액 (USD)":     "${:,.2f}",
                    "원가 ($/kg)":      lambda v: f"${v:.4f}" if v else "—",
                    "원가 합계 (USD)":  lambda v: f"${v:,.2f}" if v else "—",
                    "거래 마진 (USD)":   "${:+,.2f}",
                    "거래 마진률 (%)":   lambda v: f"{v:+.2f}%" if v is not None else "—",
                }),
                use_container_width=True, hide_index=True,
            )
            _ds_tot_rev  = sum(r["매출액 (USD)"]      for r in _ds_rows_pnl)
            _ds_tot_net  = sum(r["거래 마진 (USD)"]     for r in _ds_rows_pnl)
            _ds_tot_cost = sum(r["원가 합계 (USD)"] or 0 for r in _ds_rows_pnl)
            _ds_mg_pct   = _ds_tot_net / _ds_tot_rev * 100 if _ds_tot_rev > 0 else 0
            _dsk1, _dsk2, _dsk3 = st.columns(3)
            _dsk_col = "#4ade80" if _ds_tot_net >= 0 else "#f87171"
            _dsk1.markdown(_kpi_card("직접 판매 매출액",  f"${_ds_tot_rev:,.0f}"), unsafe_allow_html=True)
            _dsk2.markdown(_kpi_card("직접 판매 원가",   f"${_ds_tot_cost:,.0f}"), unsafe_allow_html=True)
            _dsk3.markdown(_kpi_card("직접 판매 매출이익",f"${_ds_tot_net:+,.0f}",
                                     f"마진율 {_ds_mg_pct:+.2f}%", val_color=_dsk_col), unsafe_allow_html=True)
            if any(r["원가 산출"] == "이동평균" for r in _ds_rows_pnl):
                st.caption("⚠️ 일부 항목은 FIFO 추적 데이터 부족으로 **이동평균** 원가를 사용했습니다. "
                           "원료 입출고 서브페이지의 임가공 출고 이력을 입력하면 FIFO 원가로 전환됩니다.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 — 매입사 관리
# ══════════════════════════════════════════════════════════════════════════════
if _page == PG_MASTER and _sub == SUB_BUYER:
    st.subheader("BP/BM 매입사 목록")
    with st.expander("ℹ️ 지불율(Payable) 개념 안내", expanded=False):
        st.markdown("""
**지불율(Payable)**은 매입사가 LME/MB INDEX 기준 금속 가치 중 실제로 지불하는 비율입니다.

- **Ni 지불율 1.00** = LME Ni INDEX × Ni 함유량 × 1.00 (100% 지불)
- **Co 지불율 0.95** = MB Co INDEX × Co 함유량 × 0.95 (95% 지불)

**매각단가($/kg) = (NI × Ni함유량% × Ni지불율 + CO × Co함유량% × Co지불율) ÷ 1,000**

지불율이 낮을수록 매입사에 유리합니다. 계약 협상 시 이 값이 핵심 조건입니다.
""")
    for i,b in enumerate(cfg["buyers"]):
        with st.expander(f"{'✅' if b.get('active',True) else '⛔'}  {b['name']} — {b['product']}"):
            c1,c2,c3,c4,c5,c6=st.columns(6)
            with c1: nn =st.text_input("매입사명",b["name"],key=f"bn_{i}")
            with c2: np_=st.selectbox("품목",["BP","BM"],["BP","BM"].index(b["product"]),key=f"bpr_{i}")
            with c3: nnp=st.number_input("Ni 지불율",value=b["ni_payable"],step=0.01,format="%.2f",key=f"bnp_{i}")
            with c4: ncp=st.number_input("Co 지불율",value=b["co_payable"],step=0.01,format="%.2f",key=f"bcp_{i}")
            with c5: nnc=st.number_input("Ni 함유량(%)",value=b["ni_content"],step=0.01,format="%.2f",key=f"bnc_{i}")
            with c6: ncc=st.number_input("Co 함유량(%)",value=b["co_content"],step=0.01,format="%.2f",key=f"bcc_{i}")
            ba,bb=st.columns(2)
            with ba:
                na=st.checkbox("활성",b.get("active",True),key=f"bact_{i}")
                nrbm=st.checkbox("단가 반올림 후 수분공제 (일부 매입사 방식)",
                    b.get("round_price_before_moisture", False),key=f"brbm_{i}",
                    help="켜면 단가를 소수 2자리로 반올림한 뒤 수분공제 중량과 곱해 정산액을 계산합니다. "
                         "매입사 계산서가 이 방식(예: EcoPro)이면 켜세요. 기본은 꺼짐(반올림 전 원단가 사용).")
                ncix=st.checkbox("자체 INDEX 사용 (표준 LME/MB Mid와 다름)",
                    b.get("custom_index", False),key=f"bcix_{i}",
                    help="켜면 정산 계산 시 표준 INDEX 대신 '마스터·동기화 > INDEX·환율·판관비'에서 "
                         "이 매입사 전용으로 입력한 월별 Ni/Co INDEX만 사용합니다 "
                         "(예: POSCO의 low 기준, 성일의 Co pound 기준). "
                         "해당 월이 매입사 전용 이력에 없으면 미등록으로 처리됩니다.")
                _pt1, _pt2 = st.columns(2)
                npd = _pt1.number_input("가정산 입금 (선적일 후 일수)", value=int(b.get("prov_pay_days") or 0),
                                        min_value=0, step=1, key=f"bppd_{i}",
                                        help="현금 전망의 예상 입금일 계산용. 0 = 기본값 30일")
                nfd = _pt2.number_input("확정산 입금 (ETA 후 일수)", value=int(b.get("final_pay_days") or 0),
                                        min_value=0, step=1, key=f"bfpd_{i}",
                                        help="현금 전망의 예상 입금일 계산용. 0 = 기본값 30일")
            with bb:
                s1,s2,s3,s4=st.columns(4)
                with s1:
                    if st.button("▲",key=f"b_up_{i}",disabled=(i==0),use_container_width=True):
                        cfg["buyers"][i-1],cfg["buyers"][i]=cfg["buyers"][i],cfg["buyers"][i-1]
                        save_cfg(cfg); st.rerun()
                with s2:
                    if st.button("▽",key=f"b_dn_{i}",disabled=(i==len(cfg["buyers"])-1),use_container_width=True):
                        cfg["buyers"][i+1],cfg["buyers"][i]=cfg["buyers"][i],cfg["buyers"][i+1]
                        save_cfg(cfg); st.rerun()
                with s3:
                    if st.button("저장",key=f"bsave_{i}",use_container_width=True):
                        cfg["buyers"][i].update({"name":nn,"product":np_,"ni_payable":nnp,"co_payable":ncp,"ni_content":nnc,"co_content":ncc,"active":na,"round_price_before_moisture":nrbm,"custom_index":ncix,
                                                 "prov_pay_days":int(npd),"final_pay_days":int(nfd)})
                        save_cfg(cfg); st.toast("✅ 저장 완료"); st.rerun()
                with s4:
                    with st.popover("", use_container_width=True):
                        st.warning(f"매입사 **{b['name']}** 삭제")
                        if st.button("삭제 확인", key=f"bdel_cfm_{i}", type="primary", use_container_width=True):
                            cfg["buyers"].pop(i); save_cfg(cfg); st.rerun()
    st.divider()
    st.subheader("새 매입사 추가")
    with st.form("add_buyer"):
        a1,a2,a3,a4,a5,a6=st.columns(6)
        with a1: anm=st.text_input("매입사명")
        with a2: apr=st.selectbox("품목",["BP","BM"])
        with a3: anp=st.number_input("Ni 지불율",value=1.0,step=0.01,format="%.2f")
        with a4: acp=st.number_input("Co 지불율",value=1.0,step=0.01,format="%.2f")
        with a5: anc=st.number_input("Ni 함유량(%)",value=41.93,step=0.01,format="%.2f")
        with a6: acc=st.number_input("Co 함유량(%)",value=7.23,step=0.01,format="%.2f")
        if st.form_submit_button("추가"):
            if not anm: st.error("매입사명을 입력하세요.")
            else:
                cfg["buyers"].append({"id":str(uuid.uuid4())[:8],"name":anm,"product":apr,"ni_payable":anp,"co_payable":acp,"ni_content":anc,"co_content":acc,"active":True})
                save_cfg(cfg); st.success(f"{anm} ({apr}) 추가!"); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 9 — 임가공사 관리
# ══════════════════════════════════════════════════════════════════════════════
if _page == PG_STOCK and _sub == SUB_PROC:
    st.subheader("임가공사 관리")
    scrap_list   = cfg.get("scrap_types", [])
    ph_list      = cfg.get("processing_history", [])
    proc_map_ph  = {p["id"]: p for p in cfg.get("processors", [])}
    scrap_map_ph = {s["id"]: s for s in scrap_list}
    buyer_map_ph = {b["id"]: b for b in cfg.get("buyers", [])}
    ship_list_ph = cfg.get("shipments", [])
    ship_map_ph  = {s["id"]: s for s in ship_list_ph}

    # HBL 연결 옵션 목록
    ship_opts_ph = {"(미연결)": ""}
    for _soi, _sos in enumerate(ship_list_ph):
        _sob    = buyer_map_ph.get(_sos.get("buyer_id",""), {})
        _sohbl  = _sos.get("hbl","").strip() or f"HBL미정 {_sos.get('weight_kg',0):,.0f}kg"
        ship_opts_ph[f"#{_soi+1}  {_sohbl}  ({_sos.get('loading_date','?')} · {_sob.get('name','?')})"] = _sos["id"]

    # ── 서브탭 ──────────────────────────────────────────────────────────────
    proc_tab1, proc_tab2 = st.tabs(["전체 내역", "세부 내역 (HBL)"])

    # ══════════════════════════════════════════════════════════════════════════
    # 서브탭 1 — 전체 내역 : 계약 조건 + 누적 실적
    # ══════════════════════════════════════════════════════════════════════════
    with proc_tab1:
        # ── 배치 누락 경고 ───────────────────────────────────────────────────
        _dr_list_warn = cfg.get("dispatch_records", [])
        _ph_list_warn = cfg.get("processing_history", [])
        _warn_msgs = []
        for _sc_w in scrap_list:
            _scid_w  = _sc_w["id"]
            _dr_qty  = sum(float(r.get("quantity_kg",0)) for r in _dr_list_warn if r.get("scrap_type_id")==_scid_w)
            _ph_inp  = sum(_ph_input_kg(r) for r in _ph_list_warn if r.get("scrap_type_id")==_scid_w)
            _remain  = _dr_qty - _ph_inp
            if _remain > 100:   # 100kg 초과 미처리 시 경고
                _warn_msgs.append(f"**{_sc_w['name']}** — 출고 {_dr_qty:,.0f}kg 중 투입 미기록 {_remain:,.0f}kg (임가공사 보유 추정)")
        if _warn_msgs:
            with st.expander(f"임가공사 작업 중 (처리 결과 미입력) {len(_warn_msgs)}건", expanded=True):
                st.caption("출고 기록 대비 처리 결과(배치)가 아직 없는 스크랩입니다. 임가공이 완료되면 HBL별 탭에서 배치를 추가하세요.")
                for _wm in _warn_msgs:
                    st.markdown(f"- {_wm}")

        if not cfg.get("processors"):
            st.info("등록된 임가공사가 없습니다.")
        else:
            for _proc in cfg.get("processors", []):
                _pname = ('✅ ' if _proc.get('active', True) else '⛔ ') + _proc['name']
                st.markdown(f"#### {_pname}")
                _rows_sum = []
                for _sc in scrap_list:
                    _sid2 = _sc["id"]
                    _cond = _proc.get("conditions", {}).get(_sid2, {})
                    _recs = [p for p in ph_list
                             if p.get("processor_id") == _proc["id"]
                             and p.get("scrap_type_id") == _sid2]
                    _tot_out = sum(r.get("output_kg", 0) or 0 for r in _recs)
                    _tot_in  = sum(_ph_input_kg(r) for r in _recs)
                    _act_cv  = round(_tot_out / _tot_in * 100, 2) if _tot_in > 0 else None
                    _sc_cost = sum((r.get("scrap_sale_per_kg",0) or 0) * _ph_input_kg(r) for r in _recs)
                    _pf_cost = sum((r.get("processing_fee_per_kg",0) or 0) * _ph_input_kg(r) for r in _recs)
                    _bpr_kg  = (_sc_cost + _pf_cost) / _tot_out if _tot_out > 0 else None
                    _rows_sum.append({
                        "스크랩 유형":      _sc["name"],
                        "계약 임임가공비($/kg)": _cond.get("processing_fee"),
                        "계약 전환율(%)":    _cond.get("conversion_rate"),
                        "계약 불순물율(%)":  _cond.get("impurity_rate"),
                        "배치수":           len(_recs),
                        "누적 투입(kg)":    round(_tot_in, 0)  if _tot_in  > 0 else None,
                        "누적 생산(kg)":    round(_tot_out, 0) if _tot_out > 0 else None,
                        "실제 전환율(%)":   _act_cv,
                        "BP 재매입가($/kg)":round(_bpr_kg, 4)  if _bpr_kg  else None,
                    })
                st.dataframe(pd.DataFrame(_rows_sum).style.format(na_rep="—", formatter={
                    "계약 임임가공비($/kg)": lambda v: f"${v}" if v is not None else "—",
                    "계약 전환율(%)":      lambda v: f"{v}%" if v is not None else "—",
                    "계약 불순물율(%)":    lambda v: f"{v}%" if v is not None else "—",
                    "누적 투입(kg)":       lambda v: f"{v:,.0f}" if v is not None else "—",
                    "누적 생산(kg)":       lambda v: f"{v:,.0f}" if v is not None else "—",
                    "실제 전환율(%)":      lambda v: f"{v:.2f}%" if v is not None else "—",
                    "BP 재매입가($/kg)":   lambda v: f"${v:.4f}" if v is not None else "—",
                }), use_container_width=True, hide_index=True)
                st.divider()

        # ── 계약 조건 편집 (접힘) ────────────────────────────────────────
        with st.expander("계약 조건 편집 / 임가공사 추가·삭제", expanded=False):
            for pi, proc in enumerate(cfg.get("processors", [])):
                st.markdown(f"**{proc['name']}**")
                hc1, hc2 = st.columns([3, 1])
                with hc1: pnm  = st.text_input("임가공사명", proc["name"], key=f"pnm_{pi}")
                with hc2: pact = st.checkbox("활성", proc.get("active", True), key=f"pact_{pi}")
                gh = st.columns([1.5, 1.5, 1.5, 1.5])
                for _col, _lbl in zip(gh, ["스크랩 유형","임임가공비($/kg)","전환율(%)","불순물율(%)"]):
                    _col.markdown(f"**{_lbl}**")
                new_conds = {sid: dict(v) for sid, v in proc.get("conditions", {}).items()}
                for scrap in scrap_list:
                    sid  = scrap["id"]
                    cond = new_conds.setdefault(sid, {})
                    rc   = st.columns([1.5, 1.5, 1.5, 1.5])
                    rc[0].markdown(f'<span class="b-sc">{scrap["name"]}</span>', unsafe_allow_html=True)
                    def _ni(col, val, key):
                        raw = col.text_input("_", value="" if val is None else str(val),
                                             key=key, label_visibility="collapsed")
                        try: return float(raw) if raw.strip() else None
                        except: return val
                    cond["processing_fee"]  = _ni(rc[1], cond.get("processing_fee"),  f"ppf_{pi}_{sid}")
                    cond["conversion_rate"] = _ni(rc[2], cond.get("conversion_rate"), f"pcv_{pi}_{sid}")
                    cond["impurity_rate"]   = _ni(rc[3], cond.get("impurity_rate"),   f"pim_{pi}_{sid}")
                pc1, pc2, pc3, pc4 = st.columns(4)
                with pc1:
                    if st.button("▲", key=f"p_up_{pi}", disabled=(pi==0), use_container_width=True):
                        cfg["processors"][pi-1], cfg["processors"][pi] = cfg["processors"][pi], cfg["processors"][pi-1]
                        save_cfg(cfg); st.rerun()
                with pc2:
                    if st.button("▽", key=f"p_dn_{pi}", disabled=(pi==len(cfg["processors"])-1), use_container_width=True):
                        cfg["processors"][pi+1], cfg["processors"][pi] = cfg["processors"][pi], cfg["processors"][pi+1]
                        save_cfg(cfg); st.rerun()
                with pc3:
                    if st.button("저장", key=f"psave_{pi}", use_container_width=True):
                        cfg["processors"][pi].update({"name": pnm, "active": pact, "conditions": new_conds})
                        save_cfg(cfg); st.toast("✅ 저장 완료"); st.rerun()
                with pc4:
                    with st.popover("", use_container_width=True):
                        st.warning(f"임가공사 **{proc['name']}** 삭제")
                        if st.button("삭제 확인", key=f"pdel_cfm_{pi}", type="primary", use_container_width=True):
                            cfg["processors"].pop(pi); save_cfg(cfg); st.rerun()
                st.markdown("---")

            st.markdown("**➕ 새 임가공사 추가**")
            with st.form("add_proc"):
                pnew = st.text_input("임가공사명")
                if st.form_submit_button("추가"):
                    if not pnew: st.error("임가공사명을 입력하세요.")
                    else:
                        blank = {s["id"]: {"processing_fee": None, "conversion_rate": None, "impurity_rate": None}
                                 for s in scrap_list}
                        cfg["processors"].append({"id": str(uuid.uuid4())[:8], "name": pnew,
                                                  "active": True, "conditions": blank})
                        save_cfg(cfg); st.success(f"{pnew} 추가!"); st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    # 서브탭 2 — HBL 중심 배치 관리
    # ══════════════════════════════════════════════════════════════════════════
    with proc_tab2:
        st.caption("HBL을 선택해 연결 배치를 관리합니다. 배치 추가 시 임가공비는 계약 표준값이 자동 적용됩니다.")

        # ── 공통 옵션 ────────────────────────────────────────────────────────
        _pp_opts_t2 = {p["name"]: p["id"] for p in cfg.get("processors",[])}
        _ps_opts_t2 = {s["name"]: s["id"] for s in scrap_list}
        # 선적건 HBL 선택용 (미연결 배치에서 연결할 때 사용)
        _ship_opts_t2 = {"(미연결)": ""}
        for _so in sorted(ship_list_ph, key=lambda x: x.get("loading_date",""), reverse=True):
            _so_hbl = _so.get("hbl","").strip() or f"HBL미정 {_so.get('weight_kg',0):,.0f}kg"
            _ship_opts_t2[f"{_so_hbl} [{_so.get('loading_date','?')[:7]}]"] = _so["id"]


        # ── HBL 선택 ─────────────────────────────────────────────────────────
        # 배치 수 사전 계산
        _t2_batch_cnt = {}
        for _ph_c in ph_list:
            _sid_c = _ph_c.get("shipment_id","")
            if _sid_c:
                _t2_batch_cnt[_sid_c] = _t2_batch_cnt.get(_sid_c, 0) + 1
        _unlinked_cnt = sum(1 for _ph_c in ph_list if not _ph_c.get("shipment_id",""))
        # 고아 배치: shipment_id가 있지만 해당 선적건이 삭제되어 존재하지 않는 배치
        _valid_sids   = {s["id"] for s in ship_list_ph}
        _orphan_cnt   = sum(1 for _ph_c in ph_list
                             if _ph_c.get("shipment_id","") and _ph_c.get("shipment_id","") not in _valid_sids)

        _t2_hbl_d = {"─ HBL 선택 ─": None}
        for _s2 in sorted(ship_list_ph, key=lambda x: x.get("loading_date",""), reverse=True):
            _b2     = buyer_map_ph.get(_s2.get("buyer_id",""), {})
            _icon2  = {"provisional":"🟡","final":"🟢","paid":"🔵"}.get(_s2.get("status",""),"⚪")
            _bcnt2  = _t2_batch_cnt.get(_s2["id"], 0)
            _bcnt_lbl = f"  [{_bcnt2}건]" if _bcnt2 else "  [배치없음]"
            _hbl_lbl = _s2.get("hbl","").strip() or f"HBL미정 {_s2.get('weight_kg',0):,.0f}kg"
            _t2_hbl_d[
                f"{_icon2}  {_hbl_lbl}"
                f"  │  {_b2.get('name','?')} ({_b2.get('product','?')})"
                f"  │  {_s2.get('loading_date','?')[:7]}"
                f"  {_bcnt_lbl}"
            ] = _s2["id"]
        _unlinked_lbl = f"🔖 미연결 배치" + (f"  [{_unlinked_cnt}건]" if _unlinked_cnt else "  [없음]")
        _t2_hbl_d[_unlinked_lbl] = "__unlinked__"
        if _orphan_cnt:
            _t2_hbl_d[f"🔗💥 깨진 연결 (선적건 삭제됨)  [{_orphan_cnt}건]"] = "__orphan__"

        _t2_sel = st.selectbox("HBL 선택", list(_t2_hbl_d.keys()), key="t2_hbl_sel",
                               label_visibility="collapsed")
        _t2_sid = _t2_hbl_d[_t2_sel]

        # ── slim 배치 편집 헬퍼 ──────────────────────────────────────────────
        def _slim_batch_expander(ph_list_ref, idx, rec, fixed_hbl_sid, ship_obj):
            """slim 배치 expander.
            fixed_hbl_sid: 상위 HBL 선택값. None이면 드롭다운으로 HBL 선택 가능 (미연결 배치용).
            """
            _bpo  = proc_map_ph.get(rec.get("processor_id",""), {})
            _bso  = scrap_map_ph.get(rec.get("scrap_type_id",""), {})
            _bout = float(rec.get("output_kg",0) or 0)
            _bbps = float(rec.get("bp_sale_per_kg") or 0)
            _bcv  = float(rec.get("conversion_rate_pct") or rec.get("conversion_rate") or 0)
            _rk   = rec.get("id", str(idx))  # stable key: batch id 사용
            _lbl  = (f"{'🔗' if fixed_hbl_sid else '🔖'}  "
                     f"{_bpo.get('name','?')} × {_bso.get('name','?')}  |  "
                     f"{_bout:,.0f} kg BP  |  ${_bbps:.4f}/kg")
            with st.expander(_lbl, expanded=False):
                # 미연결 배치: HBL 연결 드롭다운 표시
                if fixed_hbl_sid is None:
                    _cur_ship_lbl = next(
                        (k for k,v in _ship_opts_t2.items() if v == rec.get("shipment_id","")),
                        "(미연결)")
                    _e_hbl_link = st.selectbox("HBL 연결",
                        list(_ship_opts_t2.keys()),
                        index=list(_ship_opts_t2.keys()).index(_cur_ship_lbl)
                              if _cur_ship_lbl in _ship_opts_t2 else 0,
                        key=f"slim_hbl_{_rk}")
                    _save_hbl_sid = _ship_opts_t2[_e_hbl_link]
                else:
                    _save_hbl_sid = fixed_hbl_sid

                _ec1, _ec2 = st.columns(2)
                with _ec1:
                    _e_pp = st.selectbox("임가공사", list(_pp_opts_t2.keys()),
                        index=list(_pp_opts_t2.values()).index(rec.get("processor_id",""))
                              if rec.get("processor_id","") in _pp_opts_t2.values() else 0,
                        key=f"slim_proc_{_rk}")
                    _e_ps = st.selectbox("스크랩", list(_ps_opts_t2.keys()),
                        index=list(_ps_opts_t2.values()).index(rec.get("scrap_type_id",""))
                              if rec.get("scrap_type_id","") in _ps_opts_t2.values() else 0,
                        key=f"slim_scrap_{_rk}")
                    _econd = proc_map_ph.get(_pp_opts_t2[_e_pp],{}).get("conditions",{}).get(_ps_opts_t2[_e_ps],{})
                    _e_cv = st.number_input("전환율 (%)",
                        value=float(_bcv or _econd.get("conversion_rate") or 0),
                        min_value=0.0, max_value=100.0, step=0.1, format="%.2f",
                        key=f"slim_conv_{_rk}",
                        help=f"계약값: {_econd.get('conversion_rate')}%" if _econd.get("conversion_rate") else "계약 전환율 미설정")
                with _ec2:
                    _auto_w = float(ship_obj.get("weight_kg",0)) if ship_obj else 0.0
                    _e_out = st.number_input("생산량 kg",
                        value=float(rec.get("output_kg") or _auto_w),
                        step=1.0, format="%.0f", key=f"slim_out_{_rk}")
                    _e_inp = _e_out / (_e_cv/100) if _e_cv > 0 else 0
                    st.markdown(_kpi_card("투입량 (스크랩)", f"{_e_inp:,.0f} kg"), unsafe_allow_html=True)
                    # BP 매각단가: 연결 선적건이 final/paid이면 잠금
                    _ship_stat_lock = ship_obj.get("status","") if ship_obj else ""
                    _bp_locked = _ship_stat_lock in ("final","paid")
                    if _bp_locked:
                        st.markdown(_kpi_card("BP 매각단가 ($/kg) 🔒",
                                              f"${float(rec.get('bp_sale_per_kg') or 0):.4f}",
                                              f"선적 상태 '{_ship_stat_lock}' — 수정 잠금"), unsafe_allow_html=True)
                        _e_bps = float(rec.get("bp_sale_per_kg") or 0)
                    else:
                        _e_bps = st.number_input("BP 매각단가 ($/kg)",
                            value=float(rec.get("bp_sale_per_kg") or 0),
                            step=0.0001, format="%.4f", key=f"slim_bps_{_rk}")
                    _e_scrap_sale = st.number_input(
                        "스크랩 매각단가 ($/kg 투입)",
                        value=float(rec.get("scrap_sale_per_kg") or 0),
                        step=0.0001, format="%.4f", key=f"slim_scs_{_rk}",
                        help="BP 생산 후 부산물(잔여 스크랩) 매각 단가. 손익 탭 '스크랩 매각수익' 항목에 반영됩니다.",
                    )
                    _e_note = st.text_input("비고", rec.get("notes",""), key=f"slim_note_{_rk}")

                _es1, _es2 = st.columns(2)
                with _es1:
                    if st.button("저장", key=f"slim_save_{_rk}", use_container_width=True):
                        ph_list_ref[idx].update({
                            "shipment_id":         _save_hbl_sid,
                            "processor_id":        _pp_opts_t2[_e_pp],
                            "scrap_type_id":       _ps_opts_t2[_e_ps],
                            "conversion_rate_pct": _e_cv if _e_cv > 0 else None,
                            "input_kg":            _e_inp,
                            "output_kg":           _e_out,
                            "bp_sale_per_kg":      _e_bps,
                            "scrap_sale_per_kg":   _e_scrap_sale if _e_scrap_sale > 0 else None,
                            "notes":               _e_note,
                        })
                        save_cfg(cfg); st.toast("✅ 저장"); st.rerun()
                with _es2:
                    with st.popover("", use_container_width=True):
                        st.warning(f"배치 **{_bpo.get('name','?')} × {_bso.get('name','?')}** 삭제")
                        if st.button("삭제 확인", key=f"slim_del_cfm_{_rk}", type="primary", use_container_width=True):
                            ph_list_ref.pop(idx); save_cfg(cfg); st.rerun()

        # ── 뷰 분기 ──────────────────────────────────────────────────────────
        if _t2_sid is None:
            st.info("위에서 HBL을 선택하거나, 선적건이 없으면 위 **새 선적건 등록**을 먼저 펼치세요.")

        elif _t2_sid == "__unlinked__":
            _unlinked = [(i,p) for i,p in enumerate(ph_list) if not p.get("shipment_id","")]
            if not _unlinked:
                st.success("HBL 미연결 배치 없음 ✅  (모든 배치가 선적건에 연결되어 있습니다)")
            else:
                st.warning(f"⚠️ 미연결 배치 {len(_unlinked)}건 — 배치를 열어 HBL을 연결하세요.")
                for _uri, _up in _unlinked:
                    _slim_batch_expander(ph_list, _uri, _up, None, {})

        elif _t2_sid == "__orphan__":
            _orphans = [(i,p) for i,p in enumerate(ph_list)
                        if p.get("shipment_id","") and p.get("shipment_id","") not in _valid_sids]
            if not _orphans:
                st.success("깨진 연결 없음 ✅")
            else:
                st.error(f"💥 연결된 선적건이 삭제되어 고아가 된 배치 {len(_orphans)}건 — "
                         f"손익·시나리오 페이지에 'HBL —' 카드로 표시됩니다. 삭제하거나 다른 HBL에 재연결하세요.")
                for _ori, _op in _orphans:
                    _sc_o = scrap_map_ph.get(_op.get("scrap_type_id",""), {}).get("name","?")
                    _proc_o = proc_map_ph.get(_op.get("processor_id",""), {}).get("name","?")
                    with st.expander(
                        f"💥 {_proc_o} · {_sc_o} · output {_op.get('output_kg',0):,.0f}kg "
                        f"(존재하지 않는 shipment_id: {_op.get('shipment_id','')})",
                        expanded=False,
                    ):
                        st.caption(f"배치 ID: {_op.get('id','')}")
                        _oc1, _oc2 = st.columns(2)
                        with _oc1:
                            _o_relink_sel = st.selectbox(
                                "다른 HBL로 재연결", list(_ship_opts_t2.keys()),
                                key=f"orphan_relink_{_op.get('id','')}",
                            )
                            if st.button("재연결", key=f"orphan_relink_btn_{_op.get('id','')}"):
                                ph_list[_ori]["shipment_id"] = _ship_opts_t2[_o_relink_sel]
                                save_cfg(cfg); st.toast("✅ 재연결 완료"); st.rerun()
                        with _oc2:
                            with st.popover("배치 삭제", use_container_width=True):
                                st.warning("이 고아 배치를 삭제합니다. 되돌릴 수 없습니다.")
                                if st.button("삭제 확인", key=f"orphan_del_cfm_{_op.get('id','')}",
                                             type="primary", use_container_width=True):
                                    ph_list.pop(_ori); save_cfg(cfg); st.rerun()

        else:
            _t2_ship  = ship_map_ph.get(_t2_sid, {})
            _t2_buyer = buyer_map_ph.get(_t2_ship.get("buyer_id",""), {})
            _stat2_lbl= {"provisional":"🟡 Provisional","final":"🟢 최종","paid":"🔵 입금"}.get(
                         _t2_ship.get("status",""),"—")

            # HBL 정보 요약 바
            _ti1,_ti2,_ti3,_ti4,_ti5,_ti6 = st.columns(6)
            _eu_disp = _t2_ship.get("export_cost_usd")
            _ti1.markdown(_kpi_card("선적일",    _t2_ship.get("loading_date","—")), unsafe_allow_html=True)
            _ti2.markdown(_kpi_card("매입사",    f"{_t2_buyer.get('name','?')} ({_t2_buyer.get('product','?')})"), unsafe_allow_html=True)
            _ti3.markdown(_kpi_card("선적 중량", f"{_t2_ship.get('weight_kg',0):,.0f} kg"), unsafe_allow_html=True)
            _ti4.markdown(_kpi_card("Invoice",   f"${_t2_ship.get('invoice_usd',0):,.0f}"), unsafe_allow_html=True)
            _ti5.markdown(_kpi_card("수출비",    f"${_eu_disp:,.0f}" if _eu_disp else "—", "선적 정산 탭에서 입력"), unsafe_allow_html=True)
            _ti6.markdown(_kpi_card("상태",      _stat2_lbl), unsafe_allow_html=True)

            # 연결된 배치 목록
            _t2_batches = [(i,p) for i,p in enumerate(ph_list)
                           if p.get("shipment_id","") == _t2_sid]
            st.markdown(f"**📦 연결 배치 ({len(_t2_batches)}건)**")

            if _t2_batches:
                for _bri2, _bp2 in _t2_batches:
                    _slim_batch_expander(ph_list, _bri2, _bp2, _t2_sid, _t2_ship)
            else:
                st.info("연결된 배치가 없습니다. 아래에서 추가하세요.")

            # ── 배치 추가 폼 ──────────────────────────────────────────────────
            st.markdown("---")
            _fk = _t2_sid[:8]  # form key prefix
            with st.form(f"add_ph2_{_fk}"):
                st.markdown("**➕ 배치 추가**")
                _fa1, _fa2, _fa3 = st.columns(3)
                with _fa1:
                    _fnp = st.selectbox("임가공사",    list(_pp_opts_t2.keys()), key=f"fa_proc_{_fk}")
                    _fns = st.selectbox("스크랩 유형", list(_ps_opts_t2.keys()), key=f"fa_scrap_{_fk}")
                with _fa2:
                    _fn_cond = proc_map_ph.get(_pp_opts_t2.get(_fnp,""),{}).get(
                                   "conditions",{}).get(_ps_opts_t2.get(_fns,""),{})
                    _fn_cv_d = _fn_cond.get("conversion_rate")
                    _fno = st.number_input("생산량 kg",
                        value=float(_t2_ship.get("weight_kg",0)),
                        step=1.0, format="%.0f", key=f"fa_out_{_fk}")
                    _fnv = st.number_input("전환율 (%)",
                        value=float(_fn_cv_d or 0),
                        min_value=0.0, max_value=100.0, step=0.1, format="%.2f",
                        key=f"fa_cv_{_fk}",
                        help=f"계약값 {_fn_cv_d}%" if _fn_cv_d else "계약 전환율 미설정")
                with _fa3:
                    _auto_bps_f = 0.0
                    if _t2_buyer:
                        _, _, _, _auto_bps_f = bp_price(
                            NI, CO,
                            _t2_buyer.get("ni_content",0), _t2_buyer.get("co_content",0),
                            _t2_buyer.get("ni_payable",0), _t2_buyer.get("co_payable",0))
                    _fnbps = st.number_input("BP 매각단가 ($/kg)",
                        value=_auto_bps_f, step=0.0001, format="%.4f", key=f"fa_bps_{_fk}",
                        help=f"현재 INDEX → {_t2_buyer.get('name','?')}: ${_auto_bps_f:.4f}" if _t2_buyer else "")
                    _fn_prod = (_t2_buyer.get("product","") if _t2_buyer else "").upper()
                    _fn_scrap_default = 5.5 if "BP" in _fn_prod else (3.2 if "BM" in _fn_prod else 0.0)
                    _fnscrap = st.number_input("잔여 스크랩 매각단가 ($/kg)",
                        value=_fn_scrap_default, step=0.0001, format="%.4f", key=f"fa_scrapsale_{_fk}",
                        help="BP 생산 후 잔여 스크랩 매각 단가. BP 기본 \\$5.5, BM 기본 \\$3.2")
                    _fnnotes = st.text_input("비고", key=f"fa_notes_{_fk}")
                if st.form_submit_button("추가"):
                    _fn_inp = _fno / (_fnv/100) if _fnv > 0 else 0
                    cfg.setdefault("processing_history",[]).append({
                        "id":                    str(uuid.uuid4())[:8],
                        "shipment_id":           _t2_sid,
                        "processor_id":          _pp_opts_t2.get(_fnp,""),
                        "scrap_type_id":         _ps_opts_t2.get(_fns,""),
                        "output_kg":             _fno,
                        "conversion_rate_pct":   _fnv if _fnv > 0 else None,
                        "input_kg":              _fn_inp,
                        "bp_sale_per_kg":        _fnbps,
                        "scrap_sale_per_kg":     _fnscrap if _fnscrap > 0 else None,
                        "processing_fee_per_kg": _fn_cond.get("processing_fee"),  # 계약값 자동
                        "buyer_id":              _t2_buyer.get("id","") if _t2_buyer else "",
                        "notes":                 _fnnotes,
                    })
                    save_cfg(cfg); st.toast("✅ 추가 완료!"); st.rerun()

            # ── HBL 손익 요약 ─────────────────────────────────────────────────
            if _t2_batches:
                st.markdown("---")
                _h2_bp=0.0; _h2_pf=0.0
                for _, _bph2 in _t2_batches:
                    _h2out = float(_bph2.get("output_kg",0) or 0)
                    _h2inp = _ph_input_kg(_bph2)
                    _h2_bp += float(_bph2.get("bp_sale_per_kg",0) or 0) * _h2out
                    _h2_pf += float(_bph2.get("processing_fee_per_kg",0) or 0) * _h2inp
                # 수출비: HBL 레벨 값 직접 사용
                _h2_eu = float(_t2_ship.get("export_cost_usd") or 0)
                _h2_net = _h2_bp - _h2_pf - _h2_eu
                _h2_mg  = _h2_net / _h2_bp * 100 if _h2_bp > 0 else 0
                _hm1,_hm2,_hm3,_hm4 = st.columns(4)
                _h2_col = "#4ade80" if _h2_net >= 0 else "#f87171"
                _hm1.markdown(_kpi_card("BP 매각",  f"${_h2_bp:,.0f}"), unsafe_allow_html=True)
                _hm2.markdown(_kpi_card("임가공비", f"${_h2_pf:,.0f}", "계약값 자동 적용"), unsafe_allow_html=True)
                _hm3.markdown(_kpi_card("수출비",   f"${_h2_eu:,.0f}"), unsafe_allow_html=True)
                _hm4.markdown(_kpi_card("마진 (원료비·보관비 차감 전)",f"${_h2_net:+,.0f}",
                                        f"마진율 {_h2_mg:+.1f}% · 실질 손익은 손익·시나리오 페이지 참조",
                                        val_color=_h2_col), unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════════════════════
# TAB 10 — 스크랩 유형 관리  (지불율 없음)
# ══════════════════════════════════════════════════════════════════════════════
if _page == PG_MASTER and _sub == SUB_SCRAP:
    st.subheader("스크랩 유형 마스터")
    st.caption("샘플 분석 결과 업데이트 시 함유량을 수정하세요.")
    for si,sc in enumerate(cfg.get("scrap_types",[])):
        with st.expander(f"{'✅' if sc.get('active',True) else '⛔'}  {sc['name']}",expanded=True):
            d1,d2,d3,d4=st.columns(4)
            with d1: snm =st.text_input("유형명",sc["name"],key=f"st_nm_{si}")
            with d2: sni =st.number_input("Ni 함유량(%)",sc["ni_content"],step=0.01,format="%.2f",key=f"st_ni_{si}")
            with d3: sco =st.number_input("Co 함유량(%)",sc["co_content"],step=0.01,format="%.2f",key=f"st_co_{si}")
            with d4: sact=st.checkbox("활성",sc.get("active",True),key=f"st_act_{si}")
            d4b,d5,d6,d7,d8=st.columns(5)
            with d4b:
                _sc_prod_dflt = sc.get("product") or ("BP" if "양극" in sc.get("name","") else "BM")
                sprod=st.selectbox("생산 제품",["BP","BM"],["BP","BM"].index(_sc_prod_dflt),key=f"st_prod_{si}",
                    help="이 스크랩을 임가공하면 나오는 제품. 이론 마진·완제품 분류에 사용 (예전엔 이름에 '양극'이 있으면 BP로 추정)")
            with d5:
                srate=st.number_input("창고비 (EUR/톤백/day)",
                    value=float(sc.get("storage_rate_eur") or 1.5),
                    step=0.1, format="%.2f", key=f"st_rate_{si}",
                    help="FIFO 자동 창고비 계산에 사용. 양극=1.3, 젤리롤=1.0 등 유형별로 설정")
            sa,sb,sc_btn,sd=d6,d7,d8,st.empty()
            with sa:
                if st.button("▲",key=f"st_up_{si}",disabled=(si==0),use_container_width=True):
                    cfg["scrap_types"][si-1],cfg["scrap_types"][si]=cfg["scrap_types"][si],cfg["scrap_types"][si-1]
                    save_cfg(cfg); st.rerun()
            with sb:
                if st.button("▽",key=f"st_dn_{si}",disabled=(si==len(cfg["scrap_types"])-1),use_container_width=True):
                    cfg["scrap_types"][si+1],cfg["scrap_types"][si]=cfg["scrap_types"][si],cfg["scrap_types"][si+1]
                    save_cfg(cfg); st.rerun()
            with sc_btn:
                if st.button("저장",key=f"st_save_{si}",use_container_width=True):
                    cfg["scrap_types"][si].update({"name":snm,"ni_content":sni,"co_content":sco,
                                                   "active":sact,"storage_rate_eur":float(srate),
                                                   "product":sprod})
                    save_cfg(cfg); st.toast("✅ 저장 완료"); st.rerun()
            _sdd1,_sdd2=st.columns([1,3])
            with _sdd1:
                with st.popover("", use_container_width=True):
                    st.warning(f"스크랩 유형 **{sc['name']}** 삭제")
                    if st.button("삭제 확인", key=f"st_del_cfm_{si}", type="primary", use_container_width=True):
                        cfg["scrap_types"].pop(si); save_cfg(cfg); st.rerun()
    st.divider()
    st.subheader("새 스크랩 유형 추가")
    with st.form("add_scrap"):
        e1,e2,e3,e4,e5=st.columns(5)
        with e1: enm  =st.text_input("유형명")
        with e2: eni  =st.number_input("Ni 함유량(%)",value=0.0,step=0.01,format="%.2f")
        with e3: eco  =st.number_input("Co 함유량(%)",value=0.0,step=0.01,format="%.2f")
        with e4: erate=st.number_input("창고비 (EUR/톤백/day)",value=1.5,step=0.1,format="%.2f")
        with e5: eprod=st.selectbox("생산 제품",["BP","BM"])
        if st.form_submit_button("추가"):
            if not enm: st.error("유형명을 입력하세요.")
            else:
                sid=str(uuid.uuid4())[:8]
                cfg["scrap_types"].append({"id":sid,"name":enm,"ni_content":eni,"co_content":eco,
                                           "active":True,"storage_rate_eur":float(erate),"product":eprod})
                for p in cfg["processors"]:
                    p.setdefault("conditions",{})[sid]={"processing_fee":None,"conversion_rate":None,"impurity_rate":None}
                save_cfg(cfg); st.success(f"{enm} 추가!"); st.rerun()

    # (원료 재고 관리 섹션 → 원료 입출고 서브페이지으로 이동)



# ══════════════════════════════════════════════════════════════════════════════
# TAB 10 — 입출고 기록  (입고 이력 + 임가공 출고 + 직접 판매)
# ══════════════════════════════════════════════════════════════════════════════
if _page == PG_STOCK and _sub == SUB_INOUT:
    st.subheader("입출고 기록")
    st.caption("원료 입고 이력과 임가공/직접판매 출고 이력을 관리합니다. "
               "FIFO Lot 추적 및 자동 창고비 계산의 기준 데이터입니다.")

    # ⑤ 창고비율 미설정 스크랩 유형 경고
    _missing_rate = [s["name"] for s in cfg.get("scrap_types", [])
                     if s.get("active", True) and not s.get("storage_rate_eur")]
    if _missing_rate:
        st.warning(f"⚠️ 창고비율(EUR/톤백/day) 미설정 스크랩 유형: **{', '.join(_missing_rate)}** — "
                   "FIFO 자동 창고비 계산 시 기본값(1.5 EUR)이 적용됩니다. "
                   "**스크랩 유형 관리** 탭에서 설정하세요.")

    _of_sc_opts = {s["name"]: s["id"] for s in cfg.get("scrap_types", [])}
    _of_sc_rev  = {v: k for k, v in _of_sc_opts.items()}
    _of_pr_opts = {p["name"]: p["id"] for p in cfg.get("processors", [])}
    _of_pr_rev  = {v: k for k, v in _of_pr_opts.items()}

    # ══════════════════════════════════════════════════════════════════════════
    # 원료 재고 관리 (이동평균법)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### 원료 재고 관리 (이동평균법)")
    st.caption("스크랩 유형별 기초재고와 입고 이력을 등록합니다.  \n"
               "이동평균단가 → 손익·시나리오 실질 손익에 자동 반영.  \n"
               "입고일 **YYYY-MM-DD** + 톤백 수 입력 시 FIFO 창고비 자동 계산 정확도↑")

    if "raw_material_inventory" not in cfg:
        cfg["raw_material_inventory"] = {}
        # 저장은 하지 않음 — 실제 입력 시 save_cfg 호출

    # ── 스크랩 유형별 상세 ────────────────────────────────────────────────────
    _ph_all_inv = cfg.get("processing_history", [])
    for _isc in cfg.get("scrap_types", []):
        _isid = _isc["id"]; _isnm = _isc["name"]
        _stor_rate_disp = float(_isc.get("storage_rate_eur") or 1.5)
        if _isid not in cfg["raw_material_inventory"]:
            cfg["raw_material_inventory"][_isid] = {"opening": None, "purchases": []}
        _inv_i   = cfg["raw_material_inventory"][_isid]
        _avg_cur, _qty_cur = _inv_moving_avg(cfg, _isid)
        _bal_cur = _inv_balance(cfg, _isid, _ph_all_inv)
        if _avg_cur is not None:
            _exp_lbl = (f"📦 **{_isnm}** — 이동평균 ${_avg_cur:.4f}/kg | "
                        f"누적입고 {_qty_cur:,.0f} kg | 잔량 {_bal_cur:,.0f} kg | "
                        f"창고비 EUR {_stor_rate_disp:.2f}/톤백/day")
        else:
            _exp_lbl = f"📦 **{_isnm}** — 기초재고 미설정"
        with st.expander(_exp_lbl, expanded=(_avg_cur is None)):
            st.markdown("##### 기초재고")
            _op_i = _inv_i.get("opening") or {}
            _ic1,_ic2,_ic3,_ic4 = st.columns(4)
            with _ic1:
                _op_date_i = st.text_input("기준일 (YYYY-MM-DD)",
                    value=_op_i.get("date",""), key=f"inv_op_dt_{_isid}", placeholder="예: 2025-11-11")
            with _ic2:
                _op_qty_i = st.number_input("기초 재고량 (kg)",
                    value=float(_op_i.get("quantity_kg") or 0), step=1.0, format="%.0f", key=f"inv_op_qty_{_isid}")
            with _ic3:
                _op_cost_i = st.number_input("기초 평균단가 ($/kg)",
                    value=float(_op_i.get("unit_cost") or 0), step=0.00001, format="%.5f", key=f"inv_op_cost_{_isid}")
            with _ic4:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button("저장", key=f"inv_op_save_{_isid}", use_container_width=True):
                    if _op_date_i and _op_qty_i > 0 and _op_cost_i > 0:
                        cfg["raw_material_inventory"][_isid]["opening"] = {
                            "date": _op_date_i, "quantity_kg": float(_op_qty_i), "unit_cost": float(_op_cost_i)}
                        save_cfg(cfg); st.success("기초재고 저장 완료"); st.rerun()
                    else:
                        st.error("기준일·재고량·단가를 모두 입력하세요.")
            if _avg_cur is not None:
                st.markdown("---")
                _im1,_im2,_im3 = st.columns(3)
                _bal_col = "#f87171" if _bal_cur < 0 else "#e5e5e5"
                _im1.markdown(_kpi_card("현재 이동평균단가", f"${_avg_cur:.4f}/kg"), unsafe_allow_html=True)
                _im2.markdown(_kpi_card("누적 입고량",       f"{_qty_cur:,.0f} kg"), unsafe_allow_html=True)
                _im3.markdown(_kpi_card("잔량 (추정)", f"{_bal_cur:,.0f} kg",
                                        "음수 재고 확인 필요" if _bal_cur < 0 else "", val_color=_bal_col), unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("##### 입고 이력")
            _purs_i = sorted(_inv_i.get("purchases", []), key=lambda x: x.get("date",""))
            if _purs_i:
                _df_pur_i = pd.DataFrame([{
                    "날짜":           p.get("date",""),
                    "입고량 (kg)":    float(p.get("quantity_kg", 0)),
                    "톤백 (개)":      int(p.get("ton_bags",0) or 0),
                    "원료단가 ($/kg)": float(p.get("unit_cost", 0)),
                } for p in _purs_i])
                st.dataframe(_df_pur_i.style.format({
                    "입고량 (kg)": "{:,.0f}", "톤백 (개)": "{:,.0f}", "원료단가 ($/kg)": "${:.4f}",
                }), use_container_width=True, hide_index=True)
                _del_lbls_i = [
                    f"{p.get('date','')}  {float(p.get('quantity_kg',0)):,.0f} kg "
                    f"({int(p.get('ton_bags',0) or 0)}백) @ ${float(p.get('unit_cost',0)):.4f}"
                    for p in _purs_i]
                _deld1, _deld2 = st.columns([4,1])
                with _deld1:
                    # 인덱스를 값으로 사용 — 라벨 중복(동일 날짜·수량·단가) 시 오삭제 방지
                    _di_i = st.selectbox("삭제할 입고 건", range(len(_purs_i)),
                                         format_func=lambda i: _del_lbls_i[i], key=f"inv_del_sel_{_isid}")
                with _deld2:
                    st.markdown("&nbsp;", unsafe_allow_html=True)
                    with st.popover("", use_container_width=True):
                        st.warning(f"입고 건 삭제:\n{_del_lbls_i[_di_i]}")
                        if st.button("삭제 확인", key=f"inv_del_cfm_{_isid}", type="primary", use_container_width=True):
                            _pur_copy_i = list(_purs_i); _pur_copy_i.pop(_di_i)
                            cfg["raw_material_inventory"][_isid]["purchases"] = _pur_copy_i
                            save_cfg(cfg); st.rerun()
            else:
                st.info("등록된 입고 이력이 없습니다.")
            st.markdown("##### 입고 추가")
            _ac1,_ac2,_ac3,_ac4,_ac5 = st.columns(5)
            with _ac1:
                _new_dt_i = st.text_input("입고일 (YYYY-MM-DD)", key=f"inv_add_dt_{_isid}", placeholder="예: 2026-02-15")
            with _ac2:
                _new_qty_i = st.number_input("입고량 (kg)", value=0.0, step=1.0, format="%.0f", key=f"inv_add_qty_{_isid}")
            with _ac3:
                _new_tb_i  = st.number_input("톤백 (개)", value=0, step=1, format="%d", key=f"inv_add_tb_{_isid}",
                                             help="실제 톤백 수 — 비워도 되며 입고량÷510으로 역산")
            with _ac4:
                _new_cost_i = st.number_input("원료단가 ($/kg)", value=0.0, step=0.00001, format="%.5f", key=f"inv_add_cost_{_isid}")
            with _ac5:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                if st.button("추가", key=f"inv_add_btn_{_isid}", use_container_width=True):
                    if _new_dt_i and _new_qty_i > 0 and _new_cost_i > 0:
                        cfg["raw_material_inventory"][_isid]["purchases"].append({
                            "date": _new_dt_i, "quantity_kg": float(_new_qty_i),
                            "ton_bags": int(_new_tb_i), "unit_cost": float(_new_cost_i)})
                        save_cfg(cfg); st.success("입고 추가 완료"); st.rerun()
                    else:
                        st.error("입고일·입고량·단가를 모두 입력하세요.")


        # ── 임가공 출고 이력 ──────────────────────────────────────────────────────
    st.markdown("### 임가공 출고 이력")
    st.caption("스크랩을 임가공사(톨링)로 출고한 날짜와 수량을 기록합니다. "
               "각 B/L 배치가 어느 입고 Lot에서 비롯되었는지 추적하는 기준이 됩니다.")

    if "dispatch_records" not in cfg:
        cfg["dispatch_records"] = []

    _dr_list = cfg["dispatch_records"]

    if _dr_list:
        _dr_rows = []
        for dr in sorted(_dr_list, key=lambda x: x.get("date", ""), reverse=True):
            _dr_rows.append({
                "출고일":      dr.get("date", ""),
                "임가공사":    _of_pr_rev.get(dr.get("processor_id", ""), "—"),
                "스크랩 유형": _of_sc_rev.get(dr.get("scrap_type_id", ""), "—"),
                "출고량 (kg)": float(dr.get("quantity_kg", 0)),
                "톤백 (개)":   int(dr.get("ton_bags", 0) or 0),
                "비고":        dr.get("notes", ""),
            })
        st.dataframe(
            pd.DataFrame(_dr_rows).style.format({"출고량 (kg)": "{:,.0f}", "톤백 (개)": "{:,.0f}"}),
            use_container_width=True, hide_index=True
        )

        _dr_del_opts = [
            f"{dr.get('date','')}  |  {_of_pr_rev.get(dr.get('processor_id',''),'—')}  |  "
            f"{_of_sc_rev.get(dr.get('scrap_type_id',''),'—')}  |  {float(dr.get('quantity_kg',0)):,.0f} kg"
            for dr in _dr_list
        ]
        _drd1, _drd2 = st.columns([4, 1])
        with _drd1:
            # 인덱스를 값으로 사용 — 라벨 중복 시 오삭제 방지
            _dri = st.selectbox("삭제할 출고 건", range(len(_dr_list)),
                                 format_func=lambda i: _dr_del_opts[i], key="dr_del_sel")
        with _drd2:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            with st.popover("", use_container_width=True):
                st.warning(f"임가공 출고 삭제:\n{_dr_del_opts[_dri]}")
                if st.button("삭제 확인", key="dr_del_cfm", type="primary", use_container_width=True):
                    cfg["dispatch_records"].pop(_dri)
                    save_cfg(cfg); st.rerun()
    else:
        st.info("등록된 임가공 출고 기록이 없습니다.")

    with st.expander("임가공 출고 수동 추가", expanded=False):
        with st.form("add_dr"):
            _dr_a1, _dr_a2, _dr_a3, _dr_a4, _dr_a5 = st.columns(5)
            with _dr_a1: _dr_date  = st.text_input("출고일 (YYYY-MM-DD)", placeholder="예: 2025-11-15", key="dr_date")
            with _dr_a2: _dr_proc  = st.selectbox("임가공사", list(_of_pr_opts.keys()), key="dr_proc")
            with _dr_a3: _dr_sc    = st.selectbox("스크랩 유형", list(_of_sc_opts.keys()), key="dr_sc")
            with _dr_a4: _dr_qty   = st.number_input("출고량 (kg)", value=0.0, step=100.0, format="%.0f", key="dr_qty")
            with _dr_a5: _dr_notes = st.text_input("비고", placeholder="배치번호, 차량번호 등", key="dr_notes")
            if st.form_submit_button("출고 추가"):
                if not _dr_date or _dr_qty <= 0:
                    st.error("출고일과 출고량을 입력하세요.")
                elif not _of_pr_opts:
                    st.error("임가공사를 먼저 등록하세요.")
                else:
                    cfg["dispatch_records"].append({
                        "id":            str(uuid.uuid4())[:8],
                        "date":          _dr_date.strip(),
                        "processor_id":  _of_pr_opts[_dr_proc],
                        "scrap_type_id": _of_sc_opts[_dr_sc],
                        "quantity_kg":   float(_dr_qty),
                        "notes":         _dr_notes,
                    })
                    save_cfg(cfg); st.success("임가공 출고 추가 완료"); st.rerun()

    # ── 직접 판매 출고 이력 ───────────────────────────────────────────────────
    st.divider()
    st.markdown("### 직접 판매 출고 이력")
    st.caption("임가공(톨링) 없이 스크랩을 직접 판매한 경우 여기에 기록합니다. "
               "FIFO Lot 추적 계산 시 소진 이벤트로 반영됩니다.")

    if "direct_sales" not in cfg:
        cfg["direct_sales"] = []

    _ds_list    = cfg["direct_sales"]

    if _ds_list:
        _ds_rows = []
        for ds in sorted(_ds_list, key=lambda x: x.get("date", ""), reverse=True):
            _spkg = ds.get("sale_price_per_kg")
            _dqty = float(ds.get("quantity_kg", 0))
            _ds_rows.append({
                "판매일":        ds.get("date", ""),
                "스크랩 유형":   _of_sc_rev.get(ds.get("scrap_type_id", ""), "—"),
                "판매량 (kg)":   _dqty,
                "톤백 (개)":     int(ds.get("ton_bags", 0) or 0),
                "단가 ($/kg)":   float(_spkg) if _spkg is not None else None,
                "매출액 (USD)":  round(float(_spkg) * _dqty, 2) if _spkg is not None else None,
                "비고":          ds.get("notes", ""),
            })
        st.dataframe(
            pd.DataFrame(_ds_rows).style.format({
                "판매량 (kg)":  "{:,.0f}",
                "톤백 (개)":    "{:,.0f}",
                "단가 ($/kg)":  lambda v: f"${v:.4f}" if v is not None else "—",
                "매출액 (USD)": lambda v: f"${v:,.2f}" if v is not None else "—",
            }),
            use_container_width=True, hide_index=True
        )

        _ds_del_opts = [
            f"{ds.get('date','')}  |  {_of_sc_rev.get(ds.get('scrap_type_id',''),'—')}  |  "
            f"{float(ds.get('quantity_kg',0)):,.0f} kg"
            for ds in _ds_list
        ]
        _dsd1, _dsd2 = st.columns([4, 1])
        with _dsd1:
            # 인덱스를 값으로 사용 — 라벨 중복 시 오삭제 방지
            _dsi = st.selectbox("삭제할 판매 건", range(len(_ds_list)),
                                 format_func=lambda i: _ds_del_opts[i], key="ds_del_sel")
        with _dsd2:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            with st.popover("", use_container_width=True):
                st.warning(f"직접 판매 삭제:\n{_ds_del_opts[_dsi]}")
                if st.button("삭제 확인", key="ds_del_cfm", type="primary", use_container_width=True):
                    cfg["direct_sales"].pop(_dsi)
                    save_cfg(cfg); st.rerun()
    else:
        st.info("등록된 직접 판매 출고 이력이 없습니다.")

    with st.expander("직접 판매 수동 추가", expanded=False):
        with st.form("add_ds"):
            _ds_a1, _ds_a2, _ds_a3, _ds_a4, _ds_a5 = st.columns(5)
            with _ds_a1: _ds_date  = st.text_input("판매일 (YYYY-MM-DD)", placeholder="예: 2026-02-10", key="ds_date")
            with _ds_a2: _ds_sc    = st.selectbox("스크랩 유형", list(_of_sc_opts.keys()), key="ds_sc")
            with _ds_a3: _ds_qty   = st.number_input("판매량 (kg)", value=0.0, step=1.0, format="%.0f", key="ds_qty")
            with _ds_a4: _ds_price = st.number_input("단가 ($/kg)", value=0.0, step=0.01, format="%.4f", key="ds_price",
                                                      help="직접 판매 단가 ($/kg 스크랩). 0 입력 시 미등록.")
            with _ds_a5: _ds_notes = st.text_input("비고", placeholder="거래처, 용도 등", key="ds_notes")
            if st.form_submit_button("추가"):
                if not _ds_date or _ds_qty <= 0:
                    st.error("판매일과 수량을 입력하세요.")
                else:
                    cfg["direct_sales"].append({
                        "id":               str(uuid.uuid4())[:8],
                        "date":             _ds_date.strip(),
                        "scrap_type_id":    _of_sc_opts[_ds_sc],
                        "quantity_kg":      float(_ds_qty),
                        "sale_price_per_kg": float(_ds_price) if _ds_price > 0 else None,
                        "notes":            _ds_notes,
                    })
                    save_cfg(cfg); st.success("추가 완료"); st.rerun()


    # ══════════════════════════════════════════════════════════════════════════
    # 원료 Lot 추적 (FIFO)
    # ══════════════════════════════════════════════════════════════════════════
    st.divider()
    st.markdown("### 원료 Lot 추적 (FIFO)")
    st.caption("임가공 출고 기록을 기준으로 2단계 FIFO를 적용해 각 B/L이 어느 입고 Lot의 스크랩으로 "
               "생산되었는지 추적합니다.")

    _lt_inv_types = [s for s in cfg.get("scrap_types", [])
                     if cfg.get("raw_material_inventory", {}).get(s["id"], {}).get("opening")]
    if not _lt_inv_types:
        st.info("스크랩 유형 관리 탭에서 기초재고를 설정하면 Lot 추적이 가능합니다.")
    else:
        _ltc1, _ltc2 = st.columns([2, 3])
        with _ltc1:
            _lt_sc_opts = {s["name"]: s["id"] for s in _lt_inv_types}
            _lt_sc_sel  = st.selectbox("스크랩 유형 선택", list(_lt_sc_opts.keys()), key="lt_sc_sel")
            _lt_sc_id   = _lt_sc_opts[_lt_sc_sel]

        # 2단계 FIFO 계산
        _lt_bl_result, _lt_events, _lt_remaining = _fifo_lot_trace(cfg, _lt_sc_id)

        # dispatch_records 미입력 경고
        _has_dispatch = any(dr.get("scrap_type_id") == _lt_sc_id
                            for dr in cfg.get("dispatch_records", []))
        _has_ph = any(r.get("scrap_type_id") == _lt_sc_id
                      for r in cfg.get("processing_history", []))
        if _has_ph and not _has_dispatch:
            st.warning("⚠️ 임가공 출고 기록이 없습니다. 위 **임가공 출고 이력** 섹션에서 먼저 출고를 입력하세요.")

        with _ltc2:
            _lt_view_opts = {"📋 출고 이벤트 흐름": "__all__"}
            for _sid, _sdata in _lt_bl_result.items():
                if not _sid.startswith("__no_ship__") and _sdata.get("hbl", "미연결") != "미연결":
                    _k = f"🚢 {_sdata['hbl']}"
                    if _k not in _lt_view_opts:
                        _lt_view_opts[_k] = _sid
            if any(e["type"] == "직접판매" for e in _lt_events):
                _lt_view_opts["🏷️ 직접 판매"] = "__direct__"
            _lt_view_sel = st.selectbox("B/L 또는 보기 선택", list(_lt_view_opts.keys()), key="lt_view_sel")
            _lt_view_id  = _lt_view_opts[_lt_view_sel]

        if not _lt_events and not _lt_bl_result:
            st.info("이 스크랩 유형의 출고 이벤트가 없습니다.")

        # ── 출고 이벤트 흐름 (Level 1 결과) ─────────────────────────────────
        elif _lt_view_id == "__all__":
            _lt_all_rows = []
            for _lev in _lt_events:
                _ev_date = _lev["date"]
                for _attr in _lev["attributions"]:
                    # 보관일수: 출고일 - Lot 입고일
                    _lot_dt = _attr.get("lot_date", "")
                    _stor_d = None
                    if _lot_dt and _ev_date and _ev_date != "9999-12-31":
                        try:
                            _stor_d = max(0, (
                                datetime.strptime(_ev_date, "%Y-%m-%d") -
                                datetime.strptime(_lot_dt[:10], "%Y-%m-%d")
                            ).days)
                        except Exception:
                            _stor_d = None
                    _lt_all_rows.append({
                        "출고일":         _ev_date,
                        "유형":           _lev["type"],
                        "임가공사":       _lev["processor"],
                        "소진 Lot":       _attr["lot_label"],
                        "소진량 (kg)":    _attr["qty"],
                        "보관일수":       _stor_d,
                        "원료단가($/kg)": _attr["unit_cost"],
                        "원가 (USD)":     _attr["amount"],
                        "비고":           _lev.get("notes", ""),
                    })
            if _lt_all_rows:
                st.dataframe(pd.DataFrame(_lt_all_rows).style.format(na_rep="—", formatter={
                    "소진량 (kg)":    "{:,.1f}",
                    "보관일수":       lambda v: f"{int(v)}일" if v is not None else "—",
                    "원료단가($/kg)": lambda v: f"${v:.4f}" if v is not None else "—",
                    "원가 (USD)":     lambda v: f"${v:,.2f}" if v is not None else "—",
                }), use_container_width=True, hide_index=True)
            else:
                st.info("출고 이벤트가 없습니다.")
            _lt_rem_rows = [{"Lot": l["label"], "잔량 (kg)": round(l["remain"], 1),
                              "원료단가": l["unit_cost"]}
                             for l in _lt_remaining if l["remain"] > 0.001]
            if _lt_rem_rows:
                st.markdown("**📦 미소진 Lot 잔량** (모든 출고 차감 후)")
                st.dataframe(pd.DataFrame(_lt_rem_rows).style.format({
                    "잔량 (kg)": "{:,.1f}", "원료단가": "${:.4f}"}),
                    use_container_width=True, hide_index=True)

        # ── 직접 판매 ─────────────────────────────────────────────────────────
        elif _lt_view_id == "__direct__":
            _lt_ds_evs = [e for e in _lt_events if e["type"] == "직접판매"]
            _lt_ds_rows = []
            for _lev in _lt_ds_evs:
                for _attr in _lev["attributions"]:
                    _lt_ds_rows.append({
                        "판매일":         _lev["date"],
                        "소진 Lot":       _attr["lot_label"],
                        "소진량 (kg)":    _attr["qty"],
                        "원료단가($/kg)": _attr["unit_cost"],
                        "원가 (USD)":     _attr["amount"],
                        "비고":           _lev.get("notes", ""),
                    })
            if _lt_ds_rows:
                st.dataframe(pd.DataFrame(_lt_ds_rows).style.format(na_rep="—", formatter={
                    "소진량 (kg)":    "{:,.1f}",
                    "원료단가($/kg)": lambda v: f"${v:.4f}" if v is not None else "—",
                    "원가 (USD)":     lambda v: f"${v:,.2f}" if v is not None else "—",
                }), use_container_width=True, hide_index=True)
            else:
                st.info("직접 판매 이력이 없습니다.")

        # ── 특정 B/L 상세 ─────────────────────────────────────────────────────
        else:
            _lt_bl_data = _lt_bl_result.get(_lt_view_id)
            if not _lt_bl_data:
                st.info("해당 B/L에 연결된 처리 이력이 없습니다.")
            else:
                _lot_dict   = _lt_bl_data["lots"]
                _total_qty  = sum(v["qty"] for v in _lot_dict.values())
                _total_amt  = sum(v["amount"] for v in _lot_dict.values()
                                  if v.get("unit_cost") is not None)
                _total_stor = _lt_bl_data.get("storage_cost", 0.0)
                _wavg_cost  = _total_amt / _total_qty if _total_qty > 0 else 0
                _bm1, _bm2, _bm3, _bm4, _bm5 = st.columns(5)
                _bm1.markdown(_kpi_card("HBL",               _lt_bl_data["hbl"]), unsafe_allow_html=True)
                _bm2.markdown(_kpi_card("투입 스크랩",        f"{_lt_bl_data['input_kg']:,.0f} kg"), unsafe_allow_html=True)
                _bm3.markdown(_kpi_card("가중평균 원료단가",  f"${_wavg_cost:.4f}/kg"), unsafe_allow_html=True)
                _bm4.markdown(_kpi_card("총 원료비 (추정)",   f"${_total_amt:,.2f}"), unsafe_allow_html=True)
                _bm5.markdown(_kpi_card("FIFO 자동 보관비",  f"${_total_stor:,.2f}",
                                        "입고일→출고일 기준"), unsafe_allow_html=True)
                _lt_bl_rows = []
                for _lbl, _v in _lot_dict.items():
                    _qty = _v["qty"]
                    # 가중평균 보관일수: storage_days_wsum / qty
                    _wsum = _v.get("storage_days_wsum", 0.0)
                    _avg_days = round(_wsum / _qty, 1) if _qty > 0 else None  # wsum=0도 유효(당일 출고=0일)
                    _lt_bl_rows.append({
                        "입고 Lot":        _lbl,
                        "입고일":          _v.get("lot_date") or "—",
                        "원료단가($/kg)":  _v.get("unit_cost"),
                        "소진량 (kg)":     round(_qty, 1),
                        "비중 (%)":        round(_qty / _total_qty * 100, 1) if _total_qty else 0,
                        "원가 (USD)":      round(_v["amount"], 2) if _v.get("unit_cost") else None,
                        "보관일수 (평균)": _avg_days,
                        "보관비 (USD)":    round(_v["storage_cost"], 2) if _v.get("storage_cost") else None,
                    })
                st.dataframe(pd.DataFrame(_lt_bl_rows).style.format(na_rep="—", formatter={
                    "원료단가($/kg)":  lambda v: f"${v:.4f}" if v is not None else "—",
                    "소진량 (kg)":    "{:,.1f}",
                    "비중 (%)":       "{:.1f}%",
                    "원가 (USD)":     lambda v: f"${v:,.2f}" if v is not None else "—",
                    "보관일수 (평균)":lambda v: f"{v:.0f}일" if v is not None else "—",
                    "보관비 (USD)":   lambda v: f"${v:,.2f}" if v is not None else "—",
                }), use_container_width=True, hide_index=True)
                st.caption("보관일수 = Lot 입고일 → 임가공 출고일 (기초재고 Lot은 기준일부터 기산)  "
                           "| 복수 출고에 걸친 Lot은 가중평균으로 표시")

        # ── 임가공 출고 합계 (임가공사별) ─────────────────────────────────────
        st.divider()
        st.markdown("##### 임가공 출고 합계 (임가공사별)")

        _proc_map_lt = {p["id"]: p["name"] for p in cfg.get("processors", [])}
        _dp_by_proc  = defaultdict(float)
        for _dr in cfg.get("dispatch_records", []):
            if _dr.get("scrap_type_id") == _lt_sc_id:
                _dp_by_proc[_dr.get("processor_id", "__없음__")] += float(_dr.get("quantity_kg", 0))
        _ph_by_proc = defaultdict(float)
        for _r in cfg.get("processing_history", []):
            if _r.get("scrap_type_id") == _lt_sc_id:
                _ph_by_proc[_r.get("processor_id", "__없음__")] += _ph_input_kg(_r)

        _lt_inv_total_in  = _inv_moving_avg(cfg, _lt_sc_id)[1]
        _lt_inv_remaining = sum(l["remain"] for l in _lt_remaining if l["remain"] > 0.001)
        _lt_total_disp    = sum(_dp_by_proc.values())
        _lt_total_proc    = sum(_ph_by_proc.values())

        _dm1, _dm2, _dm3, _dm4 = st.columns(4)
        _dm1.markdown(_kpi_card("누적 입고량",     f"{_lt_inv_total_in:,.0f} kg"), unsafe_allow_html=True)
        _dm2.markdown(_kpi_card("총 임가공 출고",  f"{_lt_total_disp:,.0f} kg", "dispatch_records 합계"), unsafe_allow_html=True)
        _dm3.markdown(_kpi_card("총 B/L 투입",    f"{_lt_total_proc:,.0f} kg", "processing_history 합계"), unsafe_allow_html=True)
        _dm4.markdown(_kpi_card("창고 미출고 잔량",f"{_lt_inv_remaining:,.0f} kg", "임가공사 미발송 재고"), unsafe_allow_html=True)

        _all_proc_ids = set(list(_dp_by_proc.keys()) + list(_ph_by_proc.keys()))
        if _all_proc_ids:
            _disp_rows = []
            for _pid in sorted(_all_proc_ids, key=lambda x: _proc_map_lt.get(x, "ㅎ")):
                _disp   = _dp_by_proc.get(_pid, 0)
                _proced = _ph_by_proc.get(_pid, 0)
                _disp_rows.append({
                    "임가공사":               _proc_map_lt.get(_pid, "미연결"),
                    "출고 누적 (kg)":         round(_disp, 0),
                    "B/L 투입 누적 (kg)":     round(_proced, 0),
                    "임가공사 보유 추정 (kg)": round(_disp - _proced, 0),
                })
            def _hl_disp(row):
                v = row.get("임가공사 보유 추정 (kg)", 0) or 0
                if v < -1:  return ["", "", "", "color:#b71c1c;font-weight:600"]
                if v > 0.5: return ["", "", "", "color:#1565c0;font-weight:600"]
                return [""] * 4
            st.dataframe(
                pd.DataFrame(_disp_rows).style
                .apply(_hl_disp, axis=1)
                .format({
                    "출고 누적 (kg)":          "{:,.0f}",
                    "B/L 투입 누적 (kg)":      "{:,.0f}",
                    "임가공사 보유 추정 (kg)":  "{:+,.0f}",
                }),
                use_container_width=True, hide_index=True
            )
            st.caption(
                "ℹ️ **창고 미출고 잔량** + **임가공사 보유 추정** = 원료 재고 관리의 추정 잔량  \n"
                "⚠️ 음수이면 출고 기록보다 B/L 투입량이 많음 → 출고 기록 누락 확인 필요"
            )

# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# Google Sheets 동기화 헬퍼
# ══════════════════════════════════════════════════════════════════════════════
# _GSHEET_CREDS는 파일 상단에 정의됨
_GSHEET_NAME  = "bp_calculator_sync"
_GSHEET_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource(ttl=3600, show_spinner=False)
def _gsheet_connect():
    """gspread 클라이언트 반환 (세션 간 공유, 1시간 캐시). 실패 시 예외 발생."""
    import gspread
    creds = _get_gcp_creds(_GSHEET_SCOPES)
    return gspread.Client(auth=creds)

def _match_buyer_id(cell_val, buyers):
    """'ECOPRO (BP)' 형식 문자열 → buyer_id. 대소문자 무관."""
    v = cell_val.strip()
    # "NAME (PRODUCT)" 파싱
    if "(" in v and v.endswith(")"):
        name_part = v[:v.rfind("(")].strip().upper()
        prod_part = v[v.rfind("(")+1:-1].strip().upper()
        for b in buyers:
            if b["name"].upper() == name_part and b["product"].upper() == prod_part:
                return b["id"]
    # 이름만으로 fallback — 정확히 일치하는 것을 우선, 그래도 없으면 가장 긴(구체적인) 이름 매칭
    vu = v.upper()
    for b in buyers:
        if b["name"].upper() == vu:
            return b["id"]
    _sub_matches = [b for b in buyers if b["name"].upper() in vu]
    if _sub_matches:
        return max(_sub_matches, key=lambda b: len(b["name"]))["id"]
    return None

def _to_float(s):
    """시트 셀 문자열 → float. 천 단위 쉼표 허용. 빈 문자열/None → 0.0."""
    if not s:
        return 0.0
    return float(str(s).replace(",", "").strip())

def _sync_from_gsheets(cfg_ref):
    """Google Sheets 3개 탭 → config 동기화 (덮어쓰기).
    반환: (성공 여부, 메시지 문자열)
    """
    try:
        gc = _gsheet_connect()
        sh = gc.open(_GSHEET_NAME)
    except Exception as e:
        return False, f"연결 실패: {e}"

    buyers    = cfg_ref.get("buyers", [])
    scrap_map = {s["name"]: s["id"] for s in cfg_ref.get("scrap_types", [])}
    proc_map  = {p["name"].lower(): p["id"] for p in cfg_ref.get("processors", [])}
    log = []

    # ── ① 선적 탭 ────────────────────────────────────────────────────────────
    try:
        rows = sh.worksheet("선적").get_all_values()
        if len(rows) > 1:
            # BUG FIX: 빈 HBL 선적건이 같은 키("")로 충돌하지 않도록 제외
            hbl_idx = {s["hbl"].strip(): i for i, s in enumerate(cfg_ref.get("shipments", []))
                       if s.get("hbl","").strip()}
            added, updated = 0, 0
            _status_trans  = {}   # "provisional→final" 같은 전이 건수
            _snap_reset_cnt = 0
            _SRC_OK = ("매입사값", "당사값", "평균")
            def _xf(v):            # 숫자 셀 → float, 빈칸 → None
                return _to_float(v) if v.strip() else None
            _x_bad = 0
            for row in rows[1:]:
                # 열 수 보정 — 기본 12열: HBL/Invoice No/출하일/매입사/중량/Invoice금액/
                # Provisional월/Final월/상태/ETD/ETA/수출비
                # 확장 12열(선택, 빈칸=기존값 유지): 수분(%)/매입사Ni/매입사Co/Ni기준/Co기준/
                # 기타조정(USD)/조정사유/가정산입금일/가정산입금액/확정산입금일/확정산입금액/계약ID
                row = [c.strip().replace("\r","") for c in row] + [""] * 25
                hbl, inv_no, ld, buyer_str, wkg, iusd, pm, fm, status, etd, eta, eu_cost = row[:12]
                _x = row[12:24]
                _extra = {}
                if row[24].strip():                       # 25열: 비고 (빈칸=기존값 유지)
                    _extra["notes"] = row[24].strip()
                try:
                    if _x[0].strip():  _extra["moisture_pct"]     = _xf(_x[0]) or None
                    if _x[1].strip():  _extra["buyer_ni_content"] = _xf(_x[1])
                    if _x[2].strip():  _extra["buyer_co_content"] = _xf(_x[2])
                    if _x[3].strip() in _SRC_OK: _extra["ni_content_src"] = _x[3].strip()
                    if _x[4].strip() in _SRC_OK: _extra["co_content_src"] = _x[4].strip()
                    if _x[5].strip():  _extra["other_adj_usd"]    = _xf(_x[5]) or None
                    if _x[6].strip():  _extra["other_adj_desc"]   = _x[6].strip()
                    if _valid_date_str(_x[7].strip()):  _extra["prov_paid_date"]  = _x[7].strip()
                    if _x[8].strip():  _extra["prov_paid_usd"]    = _xf(_x[8]) or None
                    if _valid_date_str(_x[9].strip()):  _extra["final_paid_date"] = _x[9].strip()
                    if _x[10].strip(): _extra["final_paid_usd"]   = _xf(_x[10]) or None
                    if _x[11].strip(): _extra["linked_contract_id"] = _x[11].strip()
                except Exception:
                    _x_bad += 1
                    _extra = {}
                # 날짜 형식 검증(YYYY-MM-DD) — 형식이 깨진 값이 그대로 저장되면
                # 이후 화면에서 날짜로 자동 변환하다 OutOfBoundsDatetime 등으로 크래시함
                if not _valid_date_str(ld):
                    continue  # 출하일이 없거나 형식이 이상한 행은 건너뜀
                if not _valid_date_str(etd):
                    etd = ""
                if not _valid_date_str(eta):
                    eta = ""
                buyer_id = _match_buyer_id(buyer_str, buyers)
                entry = {
                    "hbl":         hbl,
                    "invoice_no":  inv_no,
                    "loading_date": ld,
                    "etd":         etd,
                    "eta":         eta,
                    "export_cost_usd": _to_float(eu_cost) if eu_cost else None,
                    "buyer_id":    buyer_id or "",
                    "weight_kg":   _to_float(wkg),
                    "invoice_usd": _to_float(iusd),
                    "prov_month":  pm or "—",
                    "final_month": fm or "—",
                    "status":      status or "provisional",
                }
                entry.update(_extra)          # 확장 열: 채워진 값만 반영
                if hbl and hbl in hbl_idx:
                    # HBL 있고 기존 항목 존재 → 업데이트
                    _sync_idx = hbl_idx[hbl]
                    _prev_status = cfg_ref["shipments"][_sync_idx].get("status","provisional")
                    # provisional로 되돌아가면 확정 스냅샷 제거 (수동 폼과 동일 로직)
                    if entry.get("status") == "provisional" and _prev_status != "provisional":
                        entry["final_amount_usd"] = None
                        _snap_reset_cnt += 1
                    if entry.get("status") != _prev_status:
                        _tk = f"{_prev_status}→{entry.get('status')}"
                        _status_trans[_tk] = _status_trans.get(_tk, 0) + 1
                    cfg_ref["shipments"][_sync_idx].update(entry)
                    updated += 1
                else:
                    # HBL 공란이거나, HBL이 새로 채워졌는데 기존엔 공란이었던 경우
                    # → 선적일+buyer_id+중량 복합키로 기존 항목(공란 HBL) 탐색
                    _match_idx = None
                    _wkg_f = _to_float(wkg)
                    for _ci, _cs in enumerate(cfg_ref.get("shipments", [])):
                        if (not _cs.get("hbl","").strip()
                                and _cs.get("loading_date","") == ld
                                and _cs.get("buyer_id","") == (buyer_id or "")
                                and abs(float(_cs.get("weight_kg",0)) - _wkg_f) < 1):
                            _match_idx = _ci
                            break
                    if _match_idx is not None:
                        _prev_status = cfg_ref["shipments"][_match_idx].get("status","provisional")
                        # provisional로 되돌아가면 확정 스냅샷 제거 (수동 폼과 동일 로직)
                        if entry.get("status") == "provisional" and _prev_status != "provisional":
                            entry["final_amount_usd"] = None
                            _snap_reset_cnt += 1
                        if entry.get("status") != _prev_status:
                            _tk = f"{_prev_status}→{entry.get('status')}"
                            _status_trans[_tk] = _status_trans.get(_tk, 0) + 1
                        cfg_ref["shipments"][_match_idx].update(entry)
                        if hbl:
                            hbl_idx[hbl] = _match_idx
                        updated += 1
                    else:
                        entry["id"] = str(uuid.uuid4())[:8]
                        for _dk, _dv in {"notes": "", "moisture_pct": None, "buyer_ni_content": None,
                                         "buyer_co_content": None, "other_adj_usd": None,
                                         "other_adj_desc": ""}.items():
                            entry.setdefault(_dk, _dv)      # 확장 열로 이미 채워진 값은 유지
                        cfg_ref.setdefault("shipments", []).append(entry)
                        if hbl:
                            hbl_idx[hbl] = len(cfg_ref["shipments"]) - 1
                        added += 1
            log.append(f"선적: 추가 {added}건 / 업데이트 {updated}건"
                       + (f" ⚠️ 확장 열 숫자 오류로 무시 {_x_bad}행" if _x_bad else ""))
            if _status_trans:
                _trans_str = ", ".join(f"{k} {v}건" for k, v in sorted(_status_trans.items()))
                log.append(f"상태 전이: {_trans_str}")
            if _snap_reset_cnt:
                log.append(f"확정 스냅샷 초기화: {_snap_reset_cnt}건 (재계산 필요 — 선적 정산 탭에서 확인)")
    except Exception as e:
        log.append(f"선적 탭 오류: {e}")

    # ── ①-b 컨테이너 탭 (선택) ────────────────────────────────────────────────
    # 열: HBL / 컨테이너번호 / 중량(kg) / Invoice(USD) / Ni(%) / Co(%) / 수분(%)
    # HBL별로 중량·Invoice 합계, Ni·Co·수분은 '정산중량' 가중평균(컨테이너 계산기와 동일 식,
    # 소수 4자리)으로 산출해 선적건에 반영하고, 원본 행은 container_calc 에 저장한다.
    # 이 탭에 있는 HBL은 선적 탭의 중량·Invoice·분석값보다 우선한다.
    try:
        rows = sh.worksheet("컨테이너").get_all_values()
    except Exception:
        rows = []
    if len(rows) > 1:
        try:
            _hbl_to_ship = {s.get("hbl","").strip(): s for s in cfg_ref.get("shipments", []) if s.get("hbl","").strip()}
            _ctr_by_hbl  = {}
            _ctr_skip    = set()
            for row in rows[1:]:
                row = [c.strip() for c in row] + [""] * 7
                hbl, cno, w, inv, ni, co, mo = row[:7]
                if not hbl or not w:
                    continue
                if hbl not in _hbl_to_ship:
                    _ctr_skip.add(hbl)
                    continue
                _ctr_by_hbl.setdefault(hbl, []).append({
                    "no": cno, "w": _to_float(w), "inv": _to_float(inv) if inv else 0.0,
                    "ni": _to_float(ni) if ni else None, "co": _to_float(co) if co else None,
                    "moist": _to_float(mo) if mo else 0.0, "has_moist": bool(mo),
                })
            _ctr_hbl_cnt = 0
            for hbl, cl in _ctr_by_hbl.items():
                s = _hbl_to_ship[hbl]
                gw = sum(c["w"] for c in cl)
                if gw <= 0:
                    continue
                s["weight_kg"] = round(gw, 3)
                inv_sum = sum(c["inv"] for c in cl)
                if inv_sum > 0:
                    s["invoice_usd"] = round(inv_sum, 2)
                sw = sum(c["w"] * (1 - c["moist"] / 100) for c in cl)
                if sw > 0:
                    # 수분·Ni·Co 는 채워진 행이 있을 때만 반영 (전부 빈칸이면 기존값 유지)
                    if any(c["has_moist"] for c in cl):
                        s["moisture_pct"] = round((1 - sw / gw) * 100, 4) or None
                    _ni_rows = [c for c in cl if c["ni"] is not None]
                    _co_rows = [c for c in cl if c["co"] is not None]
                    if _ni_rows:
                        _swn = sum(c["w"] * (1 - c["moist"] / 100) for c in _ni_rows)
                        s["buyer_ni_content"] = round(sum(c["ni"] * c["w"] * (1 - c["moist"] / 100) for c in _ni_rows) / _swn, 4)
                    if _co_rows:
                        _swc = sum(c["w"] * (1 - c["moist"] / 100) for c in _co_rows)
                        s["buyer_co_content"] = round(sum(c["co"] * c["w"] * (1 - c["moist"] / 100) for c in _co_rows) / _swc, 4)
                s["container_calc"] = {"containers": [
                    {"no": c["no"], "w": c["w"], "ni": c["ni"] or 0.0, "co": c["co"] or 0.0, "moist": c["moist"]}
                    for c in cl]}
                _ctr_hbl_cnt += 1
            _ctr_msg = f"컨테이너: {sum(len(v) for v in _ctr_by_hbl.values())}행 → HBL {_ctr_hbl_cnt}건 합산·가중평균 반영"
            if _ctr_skip:
                _ctr_msg += f" ⚠️ 선적 탭에 없는 HBL 스킵: {', '.join(sorted(_ctr_skip)[:5])}"
            log.append(_ctr_msg)
        except Exception as e:
            log.append(f"컨테이너 탭 오류: {e}")

    # ── ② 입고 탭 ────────────────────────────────────────────────────────────
    try:
        rows = sh.worksheet("입고").get_all_values()
        if len(rows) > 1:
            new_purchases = {}  # scrap_id → [purchase list]
            _pur_skip = set()
            for row in rows[1:]:
                row = [c.strip() for c in row] + [""] * 6
                sc_nm, dt, qty, tb, price, notes = row[:6]
                if not sc_nm or not qty:
                    continue
                scid = scrap_map.get(sc_nm)
                if not scid:
                    _pur_skip.add(sc_nm)
                    continue
                new_purchases.setdefault(scid, []).append({
                    "date":        dt,
                    "quantity_kg": _to_float(qty),
                    "ton_bags":    int(_to_float(tb)),
                    "unit_cost":   _to_float(price),
                    "notes":       notes,
                })
            cnt = 0
            for scid, plist in new_purchases.items():
                if scid not in cfg_ref.get("raw_material_inventory", {}):
                    cfg_ref.setdefault("raw_material_inventory", {})[scid] = {
                        "opening": None, "purchases": []
                    }
                cfg_ref["raw_material_inventory"][scid]["purchases"] = plist
                cnt += len(plist)
            _pur_msg = f"입고: {cnt}건 동기화"
            if _pur_skip:
                _pur_msg += f" ⚠️ 스크랩명 미매핑 스킵: {', '.join(sorted(_pur_skip))}"
            log.append(_pur_msg)
    except Exception as e:
        log.append(f"입고 탭 오류: {e}")

    # ── ③ 출고 탭 ────────────────────────────────────────────────────────────
    try:
        rows = sh.worksheet("출고").get_all_values()
        if len(rows) > 1:
            new_dr, new_ds = [], []
            seen_dr_sc, seen_ds_sc = set(), set()
            _out_skip_sc, _out_skip_proc = set(), set()
            for row in rows[1:]:
                row = [c.strip() for c in row] + [""] * 8
                otype, dt, sc_nm, proc_nm, qty, tb, notes = row[:7]
                if not otype or not qty:
                    continue
                scid  = scrap_map.get(sc_nm)
                if not scid:
                    if sc_nm:
                        _out_skip_sc.add(sc_nm)
                    continue
                qty_f = _to_float(qty)
                tb_i  = int(_to_float(tb))
                if otype == "임가공출고":
                    pid = proc_map.get(proc_nm.lower())
                    if not pid:
                        if proc_nm:
                            _out_skip_proc.add(proc_nm)
                        continue
                    seen_dr_sc.add(scid)
                    new_dr.append({
                        "id": str(uuid.uuid4())[:8],
                        "date": dt, "processor_id": pid,
                        "scrap_type_id": scid,
                        "quantity_kg": qty_f, "ton_bags": tb_i, "notes": notes,
                    })
                elif otype == "직접판매":
                    seen_ds_sc.add(scid)
                    new_ds.append({
                        "id": str(uuid.uuid4())[:8],
                        "date": dt, "scrap_type_id": scid,
                        "quantity_kg": qty_f, "ton_bags": tb_i,
                        "sale_price_per_kg": None, "notes": notes,
                    })
            # 시트에 나온 조합만 교체, 나머지는 보존
            cfg_ref["dispatch_records"] = [
                r for r in cfg_ref.get("dispatch_records", [])
                if r.get("scrap_type_id") not in seen_dr_sc
            ] + new_dr
            cfg_ref["direct_sales"] = [
                r for r in cfg_ref.get("direct_sales", [])
                if r.get("scrap_type_id") not in seen_ds_sc
            ] + new_ds
            _out_msg = f"출고: 임가공 {len(new_dr)}건 / 직접판매 {len(new_ds)}건 동기화"
            if _out_skip_sc:
                _out_msg += f" ⚠️ 스크랩명 미매핑: {', '.join(sorted(_out_skip_sc))}"
            if _out_skip_proc:
                _out_msg += f" ⚠️ 임가공사명 미매핑: {', '.join(sorted(_out_skip_proc))}"
            log.append(_out_msg)
    except Exception as e:
        log.append(f"출고 탭 오류: {e}")

    # ── ④ 배치 탭 (선택) ─────────────────────────────────────────────────────
    # 열: HBL / 임가공사 / 스크랩 유형 / 투입(kg) / 생산(kg) / 임가공비($/kg) /
    #     BP매각단가($/kg) / 스크랩매각단가($/kg) / 비고   (9열)
    # (HBL, 임가공사, 스크랩) 조합 기준 upsert — 같은 조합이 여러 행이면 순서대로
    # 기존 배치와 짝지어 갱신하고 남는 행은 추가. 시트에 없는 기존 배치는 유지.
    # 빈 셀은 기존 값을 보존(단가류)하거나 계약 조건으로 채움(임가공비·전환율).
    try:
        rows = sh.worksheet("배치").get_all_values()
    except Exception:
        rows = []          # 배치 탭이 없으면 조용히 건너뜀
    if len(rows) > 1:
        try:
            _hbl_to_sid = {s.get("hbl","").strip(): s["id"] for s in cfg_ref.get("shipments", [])
                           if s.get("hbl","").strip() and s.get("id")}
            _ship_by_id = {s["id"]: s for s in cfg_ref.get("shipments", []) if s.get("id")}
            _proc_cond  = {p["id"]: p.get("conditions", {}) for p in cfg_ref.get("processors", [])}
            ph_ref   = cfg_ref.setdefault("processing_history", [])
            _grouped = {}   # (sid, pid, scid) → [행]
            _b_skip  = []
            for row in rows[1:]:
                row = [c.strip() for c in row] + [""] * 9
                hbl, proc_nm, sc_nm, inp, out, fee, bps, scs, notes = row[:9]
                if not hbl or not out:
                    continue
                sid  = _hbl_to_sid.get(hbl)
                pid  = proc_map.get(proc_nm.lower())
                scid = scrap_map.get(sc_nm)
                if not sid or not pid or not scid:
                    _b_skip.append(f"{hbl}/{proc_nm}/{sc_nm}")
                    continue
                _grouped.setdefault((sid, pid, scid), []).append({
                    "inp": _to_float(inp), "out": _to_float(out),
                    "fee": _to_float(fee) if fee else None,
                    "bps": _to_float(bps) if bps else None,
                    "scs": _to_float(scs) if scs else None,
                    "notes": notes,
                })
            b_add = b_upd = b_adopt = 0
            for (sid, pid, scid), srows in _grouped.items():
                cond     = (_proc_cond.get(pid, {}) or {}).get(scid, {}) or {}
                existing = [r for r in ph_ref if r.get("shipment_id") == sid
                            and r.get("processor_id") == pid and r.get("scrap_type_id") == scid]
                for i, sr in enumerate(srows):
                    inp_v, out_v = sr["inp"], sr["out"]
                    if inp_v > 0 and out_v > 0:
                        conv = round(out_v / inp_v * 100, 2)
                    elif cond.get("conversion_rate"):
                        conv  = float(cond["conversion_rate"])          # 투입 미기재 → 계약 전환율로 역산
                        inp_v = out_v / (conv / 100) if conv > 0 else 0.0
                    else:
                        conv = None
                    upd = {"input_kg": inp_v if inp_v > 0 else None,
                           "output_kg": out_v, "conversion_rate_pct": conv}
                    if sr["fee"] is not None: upd["processing_fee_per_kg"] = sr["fee"]
                    if sr["bps"] is not None: upd["bp_sale_per_kg"]       = sr["bps"]
                    if sr["scs"] is not None: upd["scrap_sale_per_kg"]    = sr["scs"]
                    if sr["notes"]:           upd["notes"]                = sr["notes"]
                    if i < len(existing):
                        existing[i].update(upd); b_upd += 1
                        continue
                    # 신규 추가 전: 같은 임가공사·스크랩의 '미연결(또는 고아)' 배치가 생산량 2% 이내로
                    # 일치하면 새로 만들지 않고 그 배치를 이 HBL에 연결한다 (앱에서 먼저 입력해 둔
                    # 배치와 시트 행이 중복되는 것을 방지).
                    _adopt = next((r for r in ph_ref
                                   if r.get("processor_id") == pid and r.get("scrap_type_id") == scid
                                   and (not r.get("shipment_id") or r.get("shipment_id") not in _ship_by_id)
                                   and out_v > 0 and abs(float(r.get("output_kg") or 0) - out_v) / out_v <= 0.02),
                                  None)
                    if _adopt is not None:
                        _adopt.update(upd); _adopt["shipment_id"] = sid
                        if not _adopt.get("buyer_id"):
                            _adopt["buyer_id"] = _ship_by_id.get(sid, {}).get("buyer_id", "")
                        b_adopt += 1
                    else:
                        # BP 매각단가 미기재 시 선적건 Invoice 단가(총액÷중량)를 기본값으로 — 앱 수동 입력 관행과 동일
                        _sh_new = _ship_by_id.get(sid, {})
                        _bp_dflt = (round(float(_sh_new.get("invoice_usd") or 0) / float(_sh_new.get("weight_kg") or 0), 4)
                                    if float(_sh_new.get("invoice_usd") or 0) > 0 and float(_sh_new.get("weight_kg") or 0) > 0 else 0.0)
                        ph_ref.append({
                            "id": str(uuid.uuid4())[:8], "shipment_id": sid,
                            "processor_id": pid, "scrap_type_id": scid,
                            "output_kg": out_v, "input_kg": upd["input_kg"],
                            "conversion_rate_pct": conv,
                            "processing_fee_per_kg": sr["fee"] if sr["fee"] is not None else cond.get("processing_fee"),
                            "bp_sale_per_kg": sr["bps"] if sr["bps"] is not None else _bp_dflt,
                            "scrap_sale_per_kg": sr["scs"],
                            "buyer_id": _ship_by_id.get(sid, {}).get("buyer_id", ""),
                            "notes": sr["notes"],
                        })
                        b_add += 1
            _b_msg = f"배치: 추가 {b_add}건 / 업데이트 {b_upd}건"
            if b_adopt:
                _b_msg += f" / 미연결 배치 {b_adopt}건을 HBL에 연결"
            _b_msg += " (시트에 없는 기존 배치는 유지)"
            if _b_skip:
                _b_msg += f" ⚠️ HBL·임가공사·스크랩명 매핑 실패 {len(_b_skip)}건: {', '.join(_b_skip[:5])}"
            log.append(_b_msg)
        except Exception as e:
            log.append(f"배치 탭 오류: {e}")

    # ── ⑤ INDEX 탭 (선택): 기준월 / Ni / Co / 매입사(빈칸=표준) ───────────────
    try:
        rows = sh.worksheet("INDEX").get_all_values()
    except Exception:
        rows = []
    if len(rows) > 1:
        try:
            _ix_std = _ix_alt = 0; _ix_skip = set(); _ix_hint = set()
            _buyer_by_id = {b["id"]: b for b in buyers}
            for row in rows[1:]:
                row = [c.strip() for c in row] + [""] * 4
                mo, ni, co, byr = row[:4]
                if not mo or not ni or not co:
                    continue
                try:
                    datetime.strptime(mo, "%Y-%m")
                except ValueError:
                    _ix_skip.add(mo); continue
                rec = {"month": mo, "ni_index": _to_float(ni), "co_index": _to_float(co)}
                if byr:
                    bid = _match_buyer_id(byr, buyers)
                    if not bid:
                        _ix_skip.add(byr); continue
                    alt = cfg_ref.setdefault("index_history_alt", {}).setdefault(bid, [])
                    alt[:] = sorted([h for h in alt if h["month"] != mo] + [rec], key=lambda x: x["month"])
                    if not _buyer_by_id.get(bid, {}).get("custom_index"):
                        _ix_hint.add(_buyer_by_id.get(bid, {}).get("name", byr))
                    _ix_alt += 1
                else:
                    hist = cfg_ref.setdefault("index_history", [])
                    hist[:] = sorted([h for h in hist if h["month"] != mo] + [rec], key=lambda x: x["month"])
                    _ix_std += 1
            _ix_msg = f"INDEX: 표준 {_ix_std}건 / 매입사별 {_ix_alt}건"
            if _ix_hint:
                _ix_msg += f" ⚠️ 매입사 관리에서 '자체 INDEX 사용'을 켜야 적용: {', '.join(sorted(_ix_hint))}"
            if _ix_skip:
                _ix_msg += f" ⚠️ 형식·매입사 오류 스킵: {', '.join(sorted(_ix_skip)[:5])}"
            log.append(_ix_msg)
        except Exception as e:
            log.append(f"INDEX 탭 오류: {e}")

    # ── ⑥ 환율 탭 (선택): 기준월 / EUR-USD / USD-KRW ──────────────────────────
    try:
        rows = sh.worksheet("환율").get_all_values()
    except Exception:
        rows = []
    if len(rows) > 1:
        try:
            _fx_e = _fx_k = 0
            for row in rows[1:]:
                row = [c.strip() for c in row] + [""] * 3
                mo, eur, krw = row[:3]
                if not mo:
                    continue
                try:
                    datetime.strptime(mo, "%Y-%m")
                except ValueError:
                    continue
                if eur:
                    lst = cfg_ref.setdefault("eur_usd_rates", [])
                    lst[:] = sorted([r for r in lst if r["month"] != mo] + [{"month": mo, "rate": round(_to_float(eur), 4)}],
                                    key=lambda x: x["month"]); _fx_e += 1
                if krw:
                    lst = cfg_ref.setdefault("usd_krw_rates", [])
                    lst[:] = sorted([r for r in lst if r["month"] != mo] + [{"month": mo, "rate": _to_float(krw)}],
                                    key=lambda x: x["month"]); _fx_k += 1
            log.append(f"환율: EUR/USD {_fx_e}건 / USD/KRW {_fx_k}건")
        except Exception as e:
            log.append(f"환율 탭 오류: {e}")

    # ── ⑦ 판관비 탭 (선택): 기준월 / 간접 판관비 / 기타 원가 ───────────────────
    try:
        rows = sh.worksheet("판관비").get_all_values()
    except Exception:
        rows = []
    if len(rows) > 1:
        try:
            _sg_n = 0
            for row in rows[1:]:
                row = [c.strip() for c in row] + [""] * 3
                mo, sga, oth = row[:3]
                if not mo or not (sga or oth):
                    continue
                try:
                    datetime.strptime(mo, "%Y-%m")
                except ValueError:
                    continue
                lst = cfg_ref.setdefault("sga_monthly", [])
                lst[:] = sorted([r for r in lst if r["month"] != mo]
                                + [{"month": mo, "sga": _to_float(sga) if sga else 0.0, "other": _to_float(oth) if oth else 0.0}],
                                key=lambda x: x["month"]); _sg_n += 1
            log.append(f"판관비: {_sg_n}개월")
        except Exception as e:
            log.append(f"판관비 탭 오류: {e}")

    # ── ⑧ 기초재고 탭 (선택): 스크랩유형 / 기준일 / 수량(kg) / 단가($/kg) / 톤백 ──
    try:
        rows = sh.worksheet("기초재고").get_all_values()
    except Exception:
        rows = []
    if len(rows) > 1:
        try:
            _op_n = 0; _op_skip = set()
            for row in rows[1:]:
                row = [c.strip() for c in row] + [""] * 5
                sc_nm, dt, qty, uc, tb = row[:5]
                if not sc_nm or not qty:
                    continue
                scid = scrap_map.get(sc_nm)
                if not scid or not _valid_date_str(dt) or not uc:
                    _op_skip.add(sc_nm); continue
                inv = cfg_ref.setdefault("raw_material_inventory", {}).setdefault(scid, {"opening": None, "purchases": []})
                inv["opening"] = {"date": dt, "quantity_kg": _to_float(qty), "unit_cost": _to_float(uc),
                                  "ton_bags": int(_to_float(tb)) if tb else 0}
                _op_n += 1
            _op_msg = f"기초재고: {_op_n}건"
            if _op_skip:
                _op_msg += f" ⚠️ 스크랩명·기준일·단가 오류 스킵: {', '.join(sorted(_op_skip))}"
            log.append(_op_msg)
        except Exception as e:
            log.append(f"기초재고 탭 오류: {e}")

    return True, "\n".join(log)


# TAB 11 — INDEX 이력
# ══════════════════════════════════════════════════════════════════════════════
if _page == PG_MASTER and _sub == SUB_SYNC:
    # ── Google Sheets 동기화 ─────────────────────────────────────────────────
    st.subheader("Google Sheets 동기화")
    if READ_ONLY:
        st.caption(f"시트: **{_GSHEET_NAME}**  |  탭: 선적 / 입고 / 출고")
    else:
        try:
            _svc_email = _get_gcp_creds(_GSHEET_SCOPES).service_account_email
        except Exception:
            _svc_email = "—"
        st.caption(
            f"시트: **{_GSHEET_NAME}**  |  탭: 선적 / 입고 / 출고  |  "
            f"서비스 계정: `{_svc_email}`"
        )

    _gs_c1, _gs_c2 = st.columns([2, 3])
    with _gs_c1:
        # ── 미리보기 ──────────────────────────────────────────────────────
        if st.button("미리보기", use_container_width=True,
                     help="실제 데이터를 변경하지 않고 동기화될 내용을 확인합니다"):
            import copy as _copy
            _preview_cfg = _copy.deepcopy(cfg)
            with st.spinner("미리보기 계산 중..."):
                _ok_p, _msg_p = _sync_from_gsheets(_preview_cfg)
            if _ok_p:
                st.session_state["sync_preview_log"] = _msg_p
                st.session_state["sync_preview_ready"] = True
                # 변경사항 요약
                _old_dr  = len(cfg.get("dispatch_records", []))
                _new_dr  = len(_preview_cfg.get("dispatch_records", []))
                _old_pur = sum(len(v.get("purchases",[])) for v in cfg.get("raw_material_inventory",{}).values())
                _new_pur = sum(len(v.get("purchases",[])) for v in _preview_cfg.get("raw_material_inventory",{}).values())
                _old_sh  = len(cfg.get("shipments", []))
                _new_sh  = len(_preview_cfg.get("shipments", []))
                _old_ph  = len(cfg.get("processing_history", []))
                _new_ph  = len(_preview_cfg.get("processing_history", []))
                st.info(
                    f"**미리보기 결과 (저장되지 않음)**  \n"
                    f"선적: {_old_sh}건 → {_new_sh}건  ·  "
                    f"출고: {_old_dr}건 → {_new_dr}건  ·  "
                    f"입고: {_old_pur}건 → {_new_pur}건  ·  "
                    f"배치: {_old_ph}건 → {_new_ph}건"
                )
            else:
                st.error(f"미리보기 실패: {_msg_p}")
        _preview_log = st.session_state.get("sync_preview_log")
        if _preview_log and st.session_state.get("sync_preview_ready"):
            with st.expander("미리보기 상세", expanded=True):
                for _pl in _preview_log.split("\n"):
                    st.caption(_pl)

        # ── 실제 동기화 ───────────────────────────────────────────────────
        st.markdown("---")
        if st.button("지금 동기화", type="primary", use_container_width=True):
            if not st.session_state.get("sync_preview_ready"):
                st.warning("⚠️ 동기화 전에 **미리보기**를 먼저 확인하세요.")
            else:
                with st.spinner("Google Sheets에서 데이터 가져오는 중..."):
                    _ok, _msg = _sync_from_gsheets(cfg)
                if _ok:
                    save_cfg(cfg)
                    from datetime import datetime as _dt
                    _now_str = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
                    st.session_state["last_sync_time"] = _now_str
                    st.session_state["last_sync_log"] = _msg
                    st.session_state["sync_preview_ready"] = False
                    st.session_state["sync_preview_log"] = None
                    st.toast("✅ 동기화 완료")
                    st.rerun()
                else:
                    st.error(f"동기화 실패: {_msg}")
        _last_sync = st.session_state.get("last_sync_time")
        if _last_sync:
            st.caption(f"마지막 동기화: {_last_sync}")
        _last_log = st.session_state.get("last_sync_log")
        if _last_log:
            with st.expander("동기화 결과 상세", expanded=False):
                for _ll in _last_log.split("\n"):
                    st.caption(_ll)
    with _gs_c2:
        st.info(
            "**동기화 범위**  \n"
            "- 선적: HBL 기준 upsert (정산 상세·수분 등은 보존)  \n"
            "- 입고: 스크랩 유형별 구매 이력 전체 교체 (기초재고 보존)  \n"
            "- 출고: (출고유형, 스크랩유형) 조합 단위 교체  \n"
            "- 배치(선택): (HBL, 임가공사, 스크랩) 조합 기준 upsert — 시트에 없는 배치는 유지  \n"
            "- 컨테이너(선택): HBL별 중량·Invoice 합산, Ni·Co·수분 가중평균 → 선적건 반영  \n"
            "- INDEX / 환율 / 판관비 / 기초재고(선택): 월·유형 기준 upsert  \n"
            "  \n"
            "**선적 탭 (12열 + 확장 12열, 빈칸=기존값 유지)**  \n"
            "HBL / Invoice No / 출하일 / 매입사 / 중량 / Invoice금액 / Prov월 / Final월 / 상태 / ETD / ETA / 수출비 / "
            "수분(%) / 매입사Ni / 매입사Co / Ni기준 / Co기준 / 기타조정 / 조정사유 / "
            "가정산입금일 / 가정산입금액 / 확정산입금일 / 확정산입금액 / 계약ID / 비고(25열)  \n"
            "**배치 탭 (9열)** HBL / 임가공사 / 스크랩 유형 / 투입(kg) / 생산(kg) / 임가공비 / BP매각단가 / 스크랩매각단가 / 비고  \n"
            "**컨테이너 탭 (7열)** HBL / 컨테이너번호 / 중량(kg) / Invoice(USD) / Ni(%) / Co(%) / 수분(%)  \n"
            "**INDEX 탭** 기준월 / Ni / Co / 매입사(빈칸=표준) · **환율 탭** 기준월 / EUR-USD / USD-KRW · "
            "**판관비 탭** 기준월 / 판관비 / 기타 · **기초재고 탭** 스크랩유형 / 기준일 / 수량 / 단가 / 톤백  \n"
            "  \n"
            "시트에서 상태를 final로 바꾼 건은 동기화 후 선적·계약 > 선적 정산의 '확정액 미확정' 목록에서 일괄 확정하세요.  \n"
            "ℹ️ **미리보기** 후 실제 동기화 버튼이 활성화됩니다."
        )

if _page == PG_MASTER and _sub == SUB_INDEX:
    st.subheader("월별 INDEX 이력")
    history=cfg.get("index_history",[])
    if history:
        df_h=pd.DataFrame(sorted(history,key=lambda x:x["month"],reverse=True))
        df_h.columns=["기준월","Ni INDEX($/ton)","Co INDEX($/ton)"]
        st.dataframe(df_h.style.format({"Ni INDEX($/ton)":"${:,.2f}","Co INDEX($/ton)":"${:,.2f}"}),
                     use_container_width=True,hide_index=True)
        _idx_del_c1, _idx_del_c2 = st.columns([4, 1])
        with _idx_del_c1:
            dm=st.selectbox("삭제할 월",[h["month"] for h in sorted(history,key=lambda x:x["month"],reverse=True)])
        with _idx_del_c2:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            with st.popover("", use_container_width=True):
                st.warning(f"INDEX **{dm}** 삭제")
                if st.button("삭제 확인", key="idx_del_cfm", type="primary", use_container_width=True):
                    cfg["index_history"]=[h for h in history if h["month"]!=dm]
                    save_cfg(cfg); st.toast(f"✅ {dm} 삭제"); st.rerun()
    else: st.info("저장된 INDEX 이력이 없습니다.")
    st.divider()
    _idx_dflt_ni = _latest_idx[0]["ni_index"] if _latest_idx else 17093.18
    _idx_dflt_co = _latest_idx[0]["co_index"] if _latest_idx else 56598.72
    with st.expander("표준 INDEX 추가 / 수정", expanded=False):
        with st.form("add_idx"):
            i1,i2,i3=st.columns(3)
            with i1: im =st.text_input("기준월 (YYYY-MM)",placeholder="2026-04")
            with i2: ini=st.number_input("Ni INDEX($/ton)",value=_idx_dflt_ni,step=10.0,format="%.2f")
            with i3: ico=st.number_input("Co INDEX($/ton)",value=_idx_dflt_co,step=10.0,format="%.2f")
            if st.form_submit_button("저장"):
                try: datetime.strptime(im,"%Y-%m")
                except: st.error("YYYY-MM 형식으로 입력하세요.")
                else:
                    rest=[h for h in cfg["index_history"] if h["month"]!=im]
                    rest.append({"month":im,"ni_index":ini,"co_index":ico})
                    cfg["index_history"]=sorted(rest,key=lambda x:x["month"])
                    save_cfg(cfg); st.success(f"{im} 저장 — Ni \\${ini:,.2f} / Co \\${ico:,.2f}"); st.rerun()

    # ── 매입사별 자체 INDEX (예외) ─────────────────────────────────────────────
    st.divider()
    st.subheader("매입사별 자체 INDEX")
    _cix_buyers = [b for b in cfg.get("buyers", []) if b.get("custom_index")]
    if not _cix_buyers:
        st.caption("'자체 INDEX 사용'으로 설정된 매입사가 없습니다. "
                   "매입사 관리 탭에서 해당 매입사의 옵션을 켜면 여기에 표시됩니다.")
    else:
        cfg.setdefault("index_history_alt", {})
        _cix_names = {b["id"]: f"{b['name']} ({b['product']})" for b in _cix_buyers}
        _cix_sel_lbl = st.selectbox("매입사 선택", list(_cix_names.values()), key="idx_alt_buyer_sel")
        _cix_bid = next(bid for bid, lbl in _cix_names.items() if lbl == _cix_sel_lbl)
        _cix_hist = cfg["index_history_alt"].get(_cix_bid, [])
        if _cix_hist:
            _df_cix = pd.DataFrame(sorted(_cix_hist, key=lambda x: x["month"], reverse=True))
            _df_cix.columns = ["기준월", "Ni INDEX($/ton)", "Co INDEX($/ton)"]
            st.dataframe(_df_cix.style.format({"Ni INDEX($/ton)": "${:,.2f}", "Co INDEX($/ton)": "${:,.2f}"}),
                         use_container_width=True, hide_index=True)
            _cix_del_c1, _cix_del_c2 = st.columns([4, 1])
            with _cix_del_c1:
                _cix_dm = st.selectbox("삭제할 월", [h["month"] for h in sorted(_cix_hist, key=lambda x: x["month"], reverse=True)], key="idx_alt_del_m")
            with _cix_del_c2:
                st.markdown("&nbsp;", unsafe_allow_html=True)
                with st.popover("", use_container_width=True):
                    st.warning(f"{_cix_sel_lbl} 전용 INDEX **{_cix_dm}** 삭제")
                    if st.button("삭제 확인", key="idx_alt_del_cfm", type="primary", use_container_width=True):
                        cfg["index_history_alt"][_cix_bid] = [h for h in _cix_hist if h["month"] != _cix_dm]
                        save_cfg(cfg); st.toast(f"✅ {_cix_dm} 삭제"); st.rerun()
        else:
            st.caption(f"{_cix_sel_lbl} 전용 INDEX 이력이 없습니다 — 아래에서 등록하세요.")
        _cix_dflt_ni = _cix_hist[-1]["ni_index"] if _cix_hist else _idx_dflt_ni
        _cix_dflt_co = _cix_hist[-1]["co_index"] if _cix_hist else _idx_dflt_co
        with st.expander("매입사별 INDEX 추가 / 수정", expanded=False):
            with st.form("add_idx_alt"):
                st.caption(f"대상: {_cix_sel_lbl}  ·  표준 INDEX와 동일한 월이어도 반드시 이 매입사 값을 별도로 입력하세요.")
                j1, j2, j3 = st.columns(3)
                with j1: jm = st.text_input("기준월 (YYYY-MM)", placeholder="2026-04", key="idx_alt_m")
                with j2: jni = st.number_input("Ni INDEX($/ton)", value=_cix_dflt_ni, step=10.0, format="%.2f", key="idx_alt_ni")
                with j3: jco = st.number_input("Co INDEX($/ton)", value=_cix_dflt_co, step=10.0, format="%.2f", key="idx_alt_co")
                if st.form_submit_button("저장"):
                    try: datetime.strptime(jm, "%Y-%m")
                    except: st.error("YYYY-MM 형식으로 입력하세요.")
                    else:
                        _jrest = [h for h in cfg["index_history_alt"].get(_cix_bid, []) if h["month"] != jm]
                        _jrest.append({"month": jm, "ni_index": jni, "co_index": jco})
                        cfg["index_history_alt"][_cix_bid] = sorted(_jrest, key=lambda x: x["month"])
                        save_cfg(cfg); st.success(f"{_cix_sel_lbl}  {jm} 저장 — Ni \\${jni:,.2f} / Co \\${jco:,.2f}"); st.rerun()

    # ── EUR/USD 환율 관리 ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("월별 EUR/USD 환율")
    st.caption("scrap보관비 계산에 사용됩니다. (EUR 1.5/톤백/day → USD 자동환산)\n"
               "미등록 월은 직전 월 환율을 적용하며, 등록 환율이 없으면 기본값 1.10을 사용합니다.")

    eur_rates = cfg.get("eur_usd_rates", [])
    if eur_rates:
        _df_eur = pd.DataFrame(sorted(eur_rates, key=lambda x: x["month"], reverse=True))
        _df_eur.columns = ["기준월", "EUR/USD"]
        st.dataframe(
            _df_eur.style.format({"EUR/USD": "{:.4f}"}),
            use_container_width=True, hide_index=True
        )
        _eur_del_c1, _eur_del_c2 = st.columns([4, 1])
        with _eur_del_c1:
            _eur_del_m = st.selectbox(
                "삭제할 월",
                [r["month"] for r in sorted(eur_rates, key=lambda x: x["month"], reverse=True)],
                key="eur_del_sel"
            )
        with _eur_del_c2:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            with st.popover("", use_container_width=True):
                st.warning(f"EUR/USD **{_eur_del_m}** 삭제")
                if st.button("삭제 확인", key="eur_del_cfm", type="primary", use_container_width=True):
                    cfg["eur_usd_rates"] = [r for r in eur_rates if r["month"] != _eur_del_m]
                    save_cfg(cfg); st.toast(f"✅ {_eur_del_m} 삭제"); st.rerun()
    else:
        st.info("등록된 EUR/USD 환율이 없습니다. 기본값 1.10이 적용됩니다.")

    st.divider()

    # ── 자동 조회 (Frankfurter API) ───────────────────────────────────────────
    st.subheader("EUR/USD · USD/KRW 자동 조회")
    st.caption("Frankfurter.app (무료 API, 유럽중앙은행 기준) — API 키 불필요. 두 환율을 한 번에 월별 저장합니다.")

    _af1, _af2, _af3 = st.columns([2, 2, 3])
    with _af1:
        _fetch_months = st.number_input(
            "조회 개월 수 (최근 N개월)",
            value=3, min_value=1, max_value=24, step=1,
            help="현재 월 포함 최근 N개월의 말일 EUR/USD를 일괄 조회합니다."
        )
    with _af2:
        _overwrite = st.checkbox("기존 값 덮어쓰기", value=False,
                                 help="체크 해제 시 이미 등록된 월은 유지합니다.")
    with _af3:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        if st.button("자동 조회 & 저장", use_container_width=True, type="primary"):
            import requests as _req
            _existing_months = {r["month"] for r in cfg.get("eur_usd_rates", [])}
            _saved, _skipped, _failed = [], [], []
            _today = date.today()
            for _mi in range(int(_fetch_months)):
                # N개월 전부터 이번 달까지 역순 순회
                _y = _today.year
                _m = _today.month - _mi
                while _m <= 0:
                    _m += 12; _y -= 1
                _month_str = f"{_y}-{_m:02d}"
                if not _overwrite and _month_str in _existing_months:
                    _skipped.append(_month_str)
                    continue
                # 해당 월 마지막 날 환율 조회
                import calendar
                _last_day = calendar.monthrange(_y, _m)[1]
                # 미래 월이면 오늘 날짜 기준
                _fetch_date = min(date(_y, _m, _last_day), _today).isoformat()
                try:
                    _resp = _req.get(
                        f"https://api.frankfurter.app/{_fetch_date}?from=EUR&to=USD",
                        timeout=8
                    )
                    if _resp.status_code == 200:
                        _rate_val = _resp.json()["rates"]["USD"]
                        _actual_date = _resp.json()["date"][:7]  # 실제 데이터 월
                        # 말일이 주말이면 직전 영업일 데이터 반환 → 해당 월로 저장
                        _rest2 = [r for r in cfg.get("eur_usd_rates",[]) if r["month"] != _month_str]
                        _rest2.append({"month": _month_str, "rate": round(_rate_val, 4)})
                        cfg["eur_usd_rates"] = sorted(_rest2, key=lambda x: x["month"])
                        _saved.append(f"{_month_str}: EUR/USD {_rate_val:.4f} (기준일 {_actual_date})")
                    else:
                        _failed.append(f"{_month_str} (HTTP {_resp.status_code})")
                    # USD/KRW 도 같은 소스(ECB 기준)에서 함께 저장
                    _resp_k = _req.get(
                        f"https://api.frankfurter.app/{_fetch_date}?from=USD&to=KRW",
                        timeout=8
                    )
                    if _resp_k.status_code == 200:
                        _krw_val = _resp_k.json()["rates"]["KRW"]
                        _rest3 = [r for r in cfg.get("usd_krw_rates",[]) if r["month"] != _month_str]
                        _rest3.append({"month": _month_str, "rate": round(_krw_val, 2)})
                        cfg["usd_krw_rates"] = sorted(_rest3, key=lambda x: x["month"])
                        _saved.append(f"{_month_str}: USD/KRW {_krw_val:,.2f}")
                except Exception as _fe:
                    _failed.append(f"{_month_str} ({_fe})")
            if _saved:
                save_cfg(cfg)
                st.success(f"✅ {len(_saved)}개월 저장 완료\n" + "\n".join(_saved))
            if _skipped:
                st.info(f"⏭️ 기존값 유지 {len(_skipped)}개월: {', '.join(_skipped)}")
            if _failed:
                st.error(f"❌ 조회 실패: {', '.join(_failed)}")
            if _saved:
                st.rerun()

    st.divider()
    with st.expander("EUR/USD 수동 추가 / 수정", expanded=False):
        with st.form("add_eur"):
            _ec1, _ec2 = st.columns(2)
            with _ec1: _eur_m = st.text_input("기준월 (YYYY-MM)", placeholder="2026-05")
            with _ec2: _eur_r = st.number_input("EUR/USD", value=1.10, step=0.0001, format="%.4f")
            if st.form_submit_button("저장"):
                try: datetime.strptime(_eur_m, "%Y-%m")
                except: st.error("YYYY-MM 형식으로 입력하세요.")
                else:
                    _eur_rest = [r for r in cfg.get("eur_usd_rates",[]) if r["month"] != _eur_m]
                    _eur_rest.append({"month": _eur_m, "rate": _eur_r})
                    cfg["eur_usd_rates"] = sorted(_eur_rest, key=lambda x: x["month"])
                    save_cfg(cfg); st.success(f"{_eur_m} 저장 — EUR/USD {_eur_r:.4f}"); st.rerun()

    # ── 월별 USD/KRW 환율 ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("월별 USD/KRW 환율")
    st.caption("원화 환산 KPI·엑셀 보고서에 사용. 기본값은 가장 최근 월 값이며 세션에서 덮어쓸 수 있습니다.")
    _krw_rates = sorted(cfg.get("usd_krw_rates", []), key=lambda x: x["month"], reverse=True)
    if _krw_rates:
        st.dataframe(pd.DataFrame([{"기준월": r["month"], "USD/KRW": float(r["rate"])} for r in _krw_rates])
                     .style.format({"USD/KRW": "{:,.0f}"}), use_container_width=True, hide_index=True)
        _kd1, _kd2 = st.columns([4, 1])
        with _kd1:
            _krw_dm = st.selectbox("삭제할 월", [r["month"] for r in _krw_rates], key="krw_del_sel")
        with _kd2:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            with st.popover("", use_container_width=True):
                st.warning(f"USD/KRW **{_krw_dm}** 삭제")
                if st.button("삭제 확인", key="krw_del_cfm", type="primary", use_container_width=True):
                    cfg["usd_krw_rates"] = [r for r in cfg.get("usd_krw_rates", []) if r["month"] != _krw_dm]
                    save_cfg(cfg); st.rerun()
    else:
        st.info("등록된 USD/KRW 환율이 없습니다. 기본값 1,380이 적용됩니다.")
    with st.expander("USD/KRW 수동 추가 / 수정", expanded=False):
        with st.form("add_krw"):
            _kw1, _kw2 = st.columns(2)
            with _kw1: _krw_m = st.text_input("기준월 (YYYY-MM)", placeholder="2026-09")
            with _kw2: _krw_r = st.number_input("USD/KRW", value=1380.0, step=1.0, format="%.0f")
            if st.form_submit_button("저장"):
                try: datetime.strptime(_krw_m, "%Y-%m")
                except ValueError: st.error("YYYY-MM 형식으로 입력하세요.")
                else:
                    _krw_rest = [r for r in cfg.get("usd_krw_rates", []) if r["month"] != _krw_m]
                    _krw_rest.append({"month": _krw_m, "rate": float(_krw_r)})
                    cfg["usd_krw_rates"] = sorted(_krw_rest, key=lambda x: x["month"])
                    save_cfg(cfg); st.success(f"{_krw_m} 저장 — USD/KRW {_krw_r:,.0f}"); st.rerun()

    # ── 월별 간접 판관비·기타 원가 ───────────────────────────────────────────
    st.divider()
    st.subheader("월별 간접 판관비·기타 원가")
    st.caption("손익·시나리오 페이지의 영업이익(실질 손익)에 기간 합계로 차감됩니다. BP 사업 배분 기준이 정해지기 전까지는 "
               "BP 귀속분만 입력하세요. (월별 배분은 미반영 — 합계로만 차감)")
    _sga_rows = sorted(cfg.get("sga_monthly", []), key=lambda x: x["month"], reverse=True)
    if _sga_rows:
        st.dataframe(pd.DataFrame([{"기준월": r["month"],
                                    "간접 판관비(USD)": float(r.get("sga") or 0),
                                    "기타 원가(USD)":   float(r.get("other") or 0)} for r in _sga_rows])
                     .style.format({"간접 판관비(USD)": "${:,.2f}", "기타 원가(USD)": "${:,.2f}"}),
                     use_container_width=True, hide_index=True)
        _sga_d1, _sga_d2 = st.columns([4, 1])
        with _sga_d1:
            _sga_dm = st.selectbox("삭제할 월", [r["month"] for r in _sga_rows], key="sga_del_sel")
        with _sga_d2:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            with st.popover("", use_container_width=True):
                st.warning(f"판관비 **{_sga_dm}** 삭제")
                if st.button("삭제 확인", key="sga_del_cfm", type="primary", use_container_width=True):
                    cfg["sga_monthly"] = [r for r in cfg.get("sga_monthly", []) if r["month"] != _sga_dm]
                    save_cfg(cfg); st.rerun()
    else:
        st.info("등록된 판관비가 없습니다 — 손익 분석의 영업이익이 판관비 0으로 계산됩니다.")
    with st.expander("판관비 수동 추가 / 수정", expanded=False):
        with st.form("add_sga"):
            _sg1, _sg2, _sg3 = st.columns(3)
            with _sg1: _sga_m = st.text_input("기준월 (YYYY-MM)", placeholder="2026-06")
            with _sg2: _sga_v = st.number_input("간접 판관비 (USD)", value=0.0, step=100.0, format="%.2f")
            with _sg3: _sga_o = st.number_input("기타 원가 (USD)",   value=0.0, step=100.0, format="%.2f")
            if st.form_submit_button("저장"):
                try: datetime.strptime(_sga_m, "%Y-%m")
                except ValueError: st.error("YYYY-MM 형식으로 입력하세요.")
                else:
                    _sga_rest = [r for r in cfg.get("sga_monthly", []) if r["month"] != _sga_m]
                    _sga_rest.append({"month": _sga_m, "sga": float(_sga_v), "other": float(_sga_o)})
                    cfg["sga_monthly"] = sorted(_sga_rest, key=lambda x: x["month"])
                    save_cfg(cfg); st.success(f"{_sga_m} 저장"); st.rerun()
if _page == PG_MASTER and _sub == SUB_SYNC:
    # ── 데이터 백업·복원 ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("데이터 백업·복원")
    st.caption("전체 설정·거래 데이터(config.json)를 파일로 내려받거나 되돌립니다. "
               "복원은 미리보기 확인 후 버튼을 눌러야 적용됩니다.")
    _bk1, _bk2 = st.columns(2)
    with _bk1:
        st.download_button("백업 다운로드 (JSON)",
                           data=json.dumps(cfg, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name=f"bp_config_backup_{date.today():%Y%m%d}.json",
                           mime="application/json", use_container_width=True)
    with _bk2:
        _bk_file = st.file_uploader("복원할 백업 파일", type=["json"], key="bk_upload")
    if _bk_file is not None:
        try:
            _bk_cfg = json.loads(_bk_file.read().decode("utf-8"))
            if not (isinstance(_bk_cfg, dict) and "buyers" in _bk_cfg and "shipments" in _bk_cfg):
                raise ValueError("buyers/shipments 키가 없는 파일")
        except Exception as _bk_err:
            st.error(f"백업 파일을 읽을 수 없습니다: {_bk_err}")
        else:
            _bk_keys = ["buyers", "processors", "scrap_types", "shipments", "processing_history",
                        "dispatch_records", "direct_sales", "contracts", "index_history"]
            st.markdown("**복원 미리보기 (현재 → 백업)**  \n" + "  ·  ".join(
                f"{_k} {len(cfg.get(_k, []) or [])}→{len(_bk_cfg.get(_k, []) or [])}" for _k in _bk_keys))
            st.warning("확인을 누르면 현재 데이터가 백업 파일 내용으로 완전히 교체됩니다. "
                       "되돌리려면 지금 상태를 먼저 백업하세요.")
            if st.button("복원 확인 — 현재 데이터를 백업으로 교체", key="bk_restore_btn", type="primary"):
                save_cfg(_bk_cfg, force=True); st.toast("복원 완료"); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# Excel 보고서 생성 함수
# ══════════════════════════════════════════════════════════════════════════════
def generate_excel_report(cfg, ni, co, xr, ref_month, sel_buyer_id, todo=None, cash=None):
    """todo / cash: 요약 보고서의 할 일 패널·미수 현금 전망 행 (대시보드와 동일 기준으로 엑셀에 포함)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()
    ws = wb.active
    ws.title = "요약 보고서"

    # ── 스타일 헬퍼 ──
    def thin_border():
        s = Side(style="thin", color="CCCCCC")
        return Border(left=s, right=s, top=s, bottom=s)

    def cell(r, c, val=None, bold=False, size=10, color="000000",
             bg=None, align="center", fmt=None, wrap=False):
        cl = ws.cell(row=r, column=c, value=val)
        cl.font = Font(name="Arial", size=size, bold=bold, color=color)
        if bg: cl.fill = PatternFill("solid", fgColor=bg)
        cl.alignment = Alignment(horizontal=align, vertical="center", wrap_text=wrap)
        cl.border = thin_border()
        if fmt: cl.number_format = fmt
        return cl

    def merge_cell(r, c1, c2, val, bold=True, size=11, color="FFFFFF",
                   bg="1F4E79", align="left"):
        ws.merge_cells(start_row=r, start_column=c1, end_row=r, end_column=c2)
        cl = ws.cell(row=r, column=c1, value=val)
        cl.font = Font(name="Arial", size=size, bold=bold, color=color)
        cl.fill = PatternFill("solid", fgColor=bg)
        cl.alignment = Alignment(horizontal=align, vertical="center", indent=1)
        ws.row_dimensions[r].height = 22
        return cl

    COLS = 10
    ROW = 1

    # ── 타이틀 ──
    ws.merge_cells(start_row=ROW, start_column=1, end_row=ROW, end_column=COLS)
    t = ws.cell(row=ROW, column=1, value="BP / BM 단가 요약 보고서")
    t.font = Font(name="Arial", size=18, bold=True, color="FFFFFF")
    t.fill = PatternFill("solid", fgColor="1F4E79")
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[ROW].height = 40
    ROW += 1

    # ── 기준 정보 ──
    ws.merge_cells(start_row=ROW, start_column=1, end_row=ROW, end_column=COLS)
    info = (f"기준월: {ref_month}   |   Ni INDEX: ${ni:,.2f}/ton   |   "
            f"Co INDEX: ${co:,.2f}/ton   |   환율: {xr:,.0f} KRW/USD   |   작성일: {date.today()}")
    t2 = ws.cell(row=ROW, column=1, value=info)
    t2.font = Font(name="Arial", size=10, color="FFFFFF")
    t2.fill = PatternFill("solid", fgColor="2E75B6")
    t2.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[ROW].height = 20
    ROW += 2

    # ════ SECTION 1: BP/BM 매각 단가 ════
    merge_cell(ROW, 1, 6, "  ① BP/BM 매각 단가 현황", bg="2E75B6")
    ROW += 1
    for ci, h in enumerate(["매입사","품목","Ni 지불율","Co 지불율","단가 ($/kg)","단가 (원/kg)"], 1):
        cell(ROW, ci, h, bold=True, color="FFFFFF", bg="4472C4", size=10)
    ws.row_dimensions[ROW].height = 18
    ROW += 1

    ab = [b for b in cfg["buyers"] if b.get("active", True)]
    for b in ab:
        _, _, tot, pkg = bp_price(ni, co, b["ni_content"], b["co_content"], b["ni_payable"], b["co_payable"])
        bg = "D6E4F0" if b["product"] == "BP" else "D5F5E3"
        cell(ROW, 1, b["name"],        bg=bg, align="left")
        cell(ROW, 2, b["product"],     bg=bg)
        cell(ROW, 3, b["ni_payable"],  bg=bg, fmt="0.00")
        cell(ROW, 4, b["co_payable"],  bg=bg, fmt="0.00")
        cell(ROW, 5, round(pkg, 5),    bg=bg, fmt='"$"#,##0.0000')
        cell(ROW, 6, round(pkg*xr, 0), bg=bg, fmt='"₩"#,##0')
        ROW += 1
    ROW += 1

    # ════ SECTION 2: 원가·마진 매트릭스 ════
    ap  = [p for p in cfg.get("processors", []) if p.get("active", True)]
    as_ = [s for s in cfg.get("scrap_types", []) if s.get("active", True)]
    sel_b = next((b for b in ab if b["id"] == sel_buyer_id), ab[0] if ab else None)

    if ap and as_:
        n_proc = len(ap)
        merge_cell(ROW, 1, 1+n_proc, "  ② 원가 매트릭스  — 재매입 순원가 ($/kg, 임가공비 ÷ 전환율)", bg="2E75B6")
        ROW += 1
        cell(ROW, 1, "스크랩 유형", bold=True, color="FFFFFF", bg="4472C4")
        for ci, p in enumerate(ap, 2):
            cell(ROW, ci, p["name"], bold=True, color="FFFFFF", bg="4472C4")
        ws.row_dimensions[ROW].height = 18
        ROW += 1
        for scrap in as_:
            cell(ROW, 1, scrap["name"], bold=True, bg="F0F2F6", align="left")
            for ci, proc in enumerate(ap, 2):
                cond = proc.get("conditions", {}).get(scrap["id"], {})
                pf = cond.get("processing_fee"); conv = cond.get("conversion_rate")
                bmc = round(pf / (conv / 100), 4) if (pf is not None and conv and conv > 0) else None
                if bmc is not None:
                    cell(ROW, ci, bmc, fmt='"$"#,##0.0000', bg="FDEBD0")
                else:
                    cell(ROW, ci, "—", color="AAAAAA")
            ROW += 1
        ROW += 1

        if sel_b:
            _, _, _, sell_pkg = bp_price(ni, co, sel_b["ni_content"], sel_b["co_content"],
                                         sel_b["ni_payable"], sel_b["co_payable"])
            lbl = (f"  ③ 마진 매트릭스  ($/kg)  —  "
                   f"매각: {sel_b['name']} ({sel_b['product']}) ${sell_pkg:.4f}/kg 기준")
            merge_cell(ROW, 1, 1+n_proc, lbl, bg="2E75B6")
            ROW += 1
            cell(ROW, 1, "스크랩 유형", bold=True, color="FFFFFF", bg="4472C4")
            for ci, p in enumerate(ap, 2):
                cell(ROW, ci, p["name"], bold=True, color="FFFFFF", bg="4472C4")
            ws.row_dimensions[ROW].height = 18
            ROW += 1
            best_margin = -999; best_combo = ""
            for scrap in as_:
                cell(ROW, 1, scrap["name"], bold=True, bg="F0F2F6", align="left")
                for ci, proc in enumerate(ap, 2):
                    cond = proc.get("conditions", {}).get(scrap["id"], {})
                    pf = cond.get("processing_fee"); conv = cond.get("conversion_rate")
                    bmc = round(pf/(conv/100),4) if (pf is not None and conv and conv>0) else None
                    if bmc is not None:
                        margin = round(sell_pkg - bmc, 4)
                        bg_c = "D5F5E3" if margin >= 0 else "FADBD8"
                        cell(ROW, ci, margin, fmt='"$"#,##0.0000;[Red]"-$"#,##0.0000', bg=bg_c)
                        if margin > best_margin:
                            best_margin = margin
                            best_combo = f"{scrap['name']} × {proc['name']}"
                    else:
                        cell(ROW, ci, "—", color="AAAAAA")
                ROW += 1
            ROW += 1
            if best_combo:
                ws.merge_cells(start_row=ROW, start_column=1, end_row=ROW, end_column=1+n_proc)
                bc = ws.cell(row=ROW, column=1,
                             value=f"★  최고 마진:  {best_combo}  →  ${best_margin:+.4f}/kg  (₩{best_margin*xr:+,.0f}/kg)")
                bc.font = Font(name="Arial", size=11, bold=True, color="1F4E79")
                bc.fill = PatternFill("solid", fgColor="FEF9E7")
                bc.alignment = Alignment(horizontal="center", vertical="center")
                ws.row_dimensions[ROW].height = 22
            ROW += 2

    # ════ SECTION 4: 월별 손익 요약 (관리회계 기준 — 스크랩 매각·재매입 상계) ════
    ph_all_xl = cfg.get("processing_history", [])
    ship_map_xl = {s["id"]: s for s in cfg.get("shipments", [])}

    # 원료비·보관비 — 모듈 레벨 손익 엔진 사용 (손익 탭과 동일 규칙)
    _xctx = _pnl_context(cfg)
    def _xl_raw(r):
        return _xctx["rmc_fifo"](r)[0] * _ph_input_kg(r)
    _xl_stor = _xctx["eff_storage"]

    pnl_mo = defaultdict(lambda: {"bp":0.0,"pf":0.0,"eu":0.0,"raw":0.0,"stor":0.0,"out":0.0,"cnt":0})
    for r in ph_all_xl:
        sh = ship_map_xl.get(r.get("shipment_id",""), {})
        mo = (sh.get("loading_date") or "미연결")[:7]
        out = float(r.get("output_kg",0) or 0)
        inp = _ph_input_kg(r)   # 일관성: 역산 로직 통일
        pnl_mo[mo]["bp"]   += float(r.get("bp_sale_per_kg",0) or 0) * out
        pnl_mo[mo]["pf"]   += float(r.get("processing_fee_per_kg",0) or 0) * inp
        pnl_mo[mo]["eu"]   += _ph_export_usd(r, cfg)   # BUG FIX: HBL 레벨 수출비 포함
        pnl_mo[mo]["raw"]  += _xl_raw(r)
        pnl_mo[mo]["stor"] += _xl_stor(r)
        pnl_mo[mo]["out"]  += out
        pnl_mo[mo]["cnt"]  += 1

    if pnl_mo:
        merge_cell(ROW, 1, 11, "  ④ 월별 손익 요약  (매출총이익 = 매출 − 원료비(FIFO) − 임가공비(순) · "
                               "실질 손익 = 매출총이익 − 수출비 − 보관비, 판관비 제외)", bg="2E75B6")
        ROW += 1
        pnl_hdrs = ["월","배치수","생산(kg)","매출 BP(USD)","원료비(USD)","임가공비(USD)",
                    "매출총이익(USD)","수출비(USD)","보관비(USD)","실질 손익(USD)","누적 실질 손익(USD)"]
        for ci, h in enumerate(pnl_hdrs, 1):
            cell(ROW, ci, h, bold=True, color="FFFFFF", bg="4472C4", size=9)
        ws.row_dimensions[ROW].height = 18
        ROW += 1
        cum = 0.0
        for mo in sorted(pnl_mo.keys()):
            v = pnl_mo[mo]
            gp   = v["bp"] - v["raw"] - v["pf"]
            real = gp - v["eu"] - v["stor"]
            cum += real
            gp_bg  = "D6E4F0" if gp   >= 0 else "FADBD8"
            net_bg = "D5F5E3" if real >= 0 else "FADBD8"
            cum_bg = "D5F5E3" if cum  >= 0 else "FADBD8"
            cell(ROW, 1, mo, align="left")
            cell(ROW, 2, v["cnt"])
            cell(ROW, 3, round(v["out"],0),  fmt="#,##0")
            cell(ROW, 4, round(v["bp"],2),   fmt='"$"#,##0.00')
            cell(ROW, 5, round(v["raw"],2),  fmt='"$"#,##0.00')
            cell(ROW, 6, round(v["pf"],2),   fmt='"$"#,##0.00')
            cell(ROW, 7, round(gp,2),        fmt='"$"#,##0.00;[Red]"-$"#,##0.00', bg=gp_bg, bold=True)
            cell(ROW, 8, round(v["eu"],2),   fmt='"$"#,##0.00')
            cell(ROW, 9, round(v["stor"],2), fmt='"$"#,##0.00')
            cell(ROW,10, round(real,2),      fmt='"$"#,##0.00;[Red]"-$"#,##0.00', bg=net_bg, bold=True)
            cell(ROW,11, round(cum,2),       fmt='"$"#,##0.00;[Red]"-$"#,##0.00', bg=cum_bg, bold=True)
            ROW += 1
        # 합계행
        tot_bp   = sum(v["bp"]   for v in pnl_mo.values())
        tot_pf   = sum(v["pf"]   for v in pnl_mo.values())
        tot_eu   = sum(v["eu"]   for v in pnl_mo.values())
        tot_raw  = sum(v["raw"]  for v in pnl_mo.values())
        tot_stor = sum(v["stor"] for v in pnl_mo.values())
        tot_gp   = tot_bp - tot_raw - tot_pf
        tot_real = tot_gp - tot_eu - tot_stor
        tot_gp_bg = "D6E4F0" if tot_gp   >= 0 else "FADBD8"
        tot_bg    = "D5F5E3" if tot_real >= 0 else "FADBD8"
        for ci, val in enumerate(["합계","","",round(tot_bp,2),round(tot_raw,2),round(tot_pf,2),
                                  round(tot_gp,2),round(tot_eu,2),round(tot_stor,2),round(tot_real,2),""], 1):
            kw = {"bold":True, "bg":"F0F2F6"}
            if ci in (4,5,6,8,9): kw["fmt"]='"$"#,##0.00'
            elif ci==7:  kw["bg"]=tot_gp_bg; kw["fmt"]='"$"#,##0.00;[Red]"-$"#,##0.00'
            elif ci==10: kw["bg"]=tot_bg;    kw["fmt"]='"$"#,##0.00;[Red]"-$"#,##0.00'
            cell(ROW, ci, val, **kw)
        ROW += 2

    # ════ SECTION 5: HBL별 손익 상세 (관리회계 기준) ════
    if ph_all_xl:
        merge_cell(ROW, 1, 13, "  ⑤ HBL별 손익 상세  (매출총이익 = 매출 − 원료비 − 임가공비(순), "
                               "실질 손익 = 매출총이익 − 수출비 − 보관비)", bg="2E75B6")
        ROW += 1
        hbl_hdrs = ["HBL","매입사","선적일","투입(kg)","생산(kg)","전환율(%)","매출 BP",
                    "원료비","임가공비(순)","매출총이익","수출비","보관비","실질 손익"]
        for ci, h in enumerate(hbl_hdrs, 1):
            cell(ROW, ci, h, bold=True, color="FFFFFF", bg="4472C4", size=9)
        ws.row_dimensions[ROW].height = 18
        ROW += 1
        buyer_map_xl = {b["id"]:b for b in cfg["buyers"]}
        hagg = defaultdict(lambda: {"bp":0.0,"pf":0.0,"eu":0.0,"raw":0.0,"stor":0.0,"out":0.0,"inp":0.0,"cnt":0})
        for r in ph_all_xl:
            sid = r.get("shipment_id","")
            if not sid: continue
            out = float(r.get("output_kg",0) or 0)
            inp_v = _ph_input_kg(r)   # 일관성: 역산 로직 통일
            hagg[sid]["bp"]   += float(r.get("bp_sale_per_kg",0) or 0)*out
            hagg[sid]["pf"]   += float(r.get("processing_fee_per_kg",0) or 0)*inp_v
            hagg[sid]["eu"]   += _ph_export_usd(r, cfg)   # BUG FIX: HBL 레벨 수출비 포함
            hagg[sid]["raw"]  += _xl_raw(r)
            hagg[sid]["stor"] += _xl_stor(r)
            hagg[sid]["out"]  += out
            hagg[sid]["inp"]  += float(inp_v or 0)
        for sid in sorted(hagg, key=lambda x: ship_map_xl.get(x,{}).get("loading_date","")):
            v = hagg[sid]
            sh = ship_map_xl.get(sid,{})
            byr = buyer_map_xl.get(sh.get("buyer_id",""),{})
            gp   = v["bp"] - v["raw"] - v["pf"]
            real = gp - v["eu"] - v["stor"]
            gp_bg  = "D6E4F0" if gp   >= 0 else "FADBD8"
            net_bg = "D5F5E3" if real >= 0 else "FADBD8"
            conv = round(v["out"]/v["inp"]*100,2) if v["inp"]>0 else None
            cell(ROW,1, sh.get("hbl","—"),                                     align="left")
            cell(ROW,2, f"{byr.get('name','?')} ({byr.get('product','?')})",   align="left")
            cell(ROW,3, sh.get("loading_date","—"))
            cell(ROW,4, round(v["inp"],0),  fmt="#,##0")
            cell(ROW,5, round(v["out"],0),  fmt="#,##0")
            cell(ROW,6, conv,               fmt='#,##0.00"%"' if conv else None)
            cell(ROW,7, round(v["bp"],2),   fmt='"$"#,##0.00')
            cell(ROW,8, round(v["raw"],2),  fmt='"$"#,##0.00')
            cell(ROW,9, round(v["pf"],2),   fmt='"$"#,##0.00')
            cell(ROW,10,round(gp,2),        fmt='"$"#,##0.00;[Red]"-$"#,##0.00', bg=gp_bg, bold=True)
            cell(ROW,11,round(v["eu"],2),   fmt='"$"#,##0.00')
            cell(ROW,12,round(v["stor"],2), fmt='"$"#,##0.00')
            cell(ROW,13,round(real,2),      fmt='"$"#,##0.00;[Red]"-$"#,##0.00', bg=net_bg, bold=True)
            ROW += 1
        ROW += 1

    # ════ SECTION 6: 선적 정산 현황 ════
    merge_cell(ROW, 1, 8, "  ⑥ 선적 정산 현황", bg="2E75B6")
    ROW += 1
    ships = cfg.get("shipments", [])
    buyer_map_l = {b["id"]: b for b in cfg["buyers"]}
    stats = {}
    for s in ships:
        k = s.get("status","provisional"); stats[k] = stats.get(k,0)+1
    total_w = sum(s.get("weight_kg",0) for s in ships)
    total_inv_s = sum(s.get("invoice_usd",0) for s in ships)
    for ci, (lbl, val) in enumerate([
        ("총 선적건", f"{len(ships)}건"),
        ("총 중량", f"{total_w/1000:,.1f} MT"),
        ("Provisional 정산", f"{stats.get('provisional',0)}건"),
        ("최종정산", f"{stats.get('final',0)}건"),
        ("입금완료", f"{stats.get('paid',0)}건"),
        ("총 Invoice", f"${total_inv_s:,.0f}"),
    ], 1):
        cell(ROW,   ci, lbl, bold=True, color="FFFFFF", bg="4472C4", size=9)
        cell(ROW+1, ci, val, size=11, bold=True, bg="F0F2F6")
    ws.row_dimensions[ROW].height = 16; ws.row_dimensions[ROW+1].height = 22
    ROW += 3
    if ships:
        for ci, h in enumerate(["HBL","매입사","선적일","중량(kg)","Invoice(USD)","Prov월","Final월","상태"], 1):
            cell(ROW, ci, h, bold=True, color="FFFFFF", bg="4472C4", size=9)
        ws.row_dimensions[ROW].height = 16; ROW += 1
        for s in sorted(ships, key=lambda x: x.get("loading_date",""), reverse=True):
            b2 = buyer_map_l.get(s.get("buyer_id"),{})
            sc = {"provisional":"FEF9E7","final":"D5F5E3","paid":"D6E4F0"}.get(s.get("status","provisional"),"FFFFFF")
            cell(ROW,1, s.get("hbl","—"),                                     bg=sc, align="left")
            cell(ROW,2, f"{b2.get('name','?')} ({b2.get('product','?')})",    bg=sc, align="left")
            cell(ROW,3, s.get("loading_date","—"),                            bg=sc)
            cell(ROW,4, s.get("weight_kg",0),    fmt="#,##0",                 bg=sc)
            cell(ROW,5, s.get("invoice_usd",0),  fmt='"$"#,##0.00',          bg=sc)
            cell(ROW,6, s.get("prov_month","—"),                              bg=sc)
            cell(ROW,7, s.get("final_month","—"),                             bg=sc)
            cell(ROW,8, {"provisional":"Provisional 정산","final":"최종정산","paid":"입금완료"}.get(s.get("status",""),"—"), bg=sc)
            ROW += 1

    # ════ SECTION 7~9: 할 일 / 미수 현금 전망 / 완제품 재고 (대시보드 요약과 동일 기준) ════
    ROW += 1
    if todo:
        merge_cell(ROW, 1, 6, "  ⑦ 할 일 (요약 보고서 패널과 동일)", bg="2E75B6"); ROW += 1
        for ci, h in enumerate(["구분", "항목", "상세", "처리 위치"], 1):
            cell(ROW, ci, h, bold=True, color="FFFFFF", bg="4472C4", size=9)
        ROW += 1
        for _dot, _title, _detail, _tab in todo:
            cell(ROW, 1, {"🔴": "긴급", "🟡": "확인"}.get(_dot, ""))
            cell(ROW, 2, _title,  align="left")
            cell(ROW, 3, _detail, align="left", wrap=True)
            cell(ROW, 4, _tab,    align="left")
            ROW += 1
        ROW += 1
    if cash:
        merge_cell(ROW, 1, 9, "  ⑧ 미수 현금 전망 (확정산 잔액 · 가정산은 수령 완료 간주)", bg="2E75B6"); ROW += 1
        _ch = ["구분", "HBL", "매입사", "상태", "Final월", "기준", "가정산 수령", "확정산 잔액", "예상 입금월"]
        for ci, h in enumerate(_ch, 1):
            cell(ROW, ci, h, bold=True, color="FFFFFF", bg="4472C4", size=9)
        ROW += 1
        for r in cash:
            for ci, k in enumerate(_ch, 1):
                cell(ROW, ci, r.get(k, ""),
                     fmt='"$"#,##0' if k in ("가정산 수령", "확정산 잔액") else None,
                     align="left" if ci <= 3 else "center")
            ROW += 1
        cell(ROW, 7, "합계", bold=True, bg="F0F2F6")
        cell(ROW, 8, sum(float(r.get("확정산 잔액", 0) or 0) for r in cash), bold=True, bg="F0F2F6", fmt='"$"#,##0')
        ROW += 2
    _fgx = defaultdict(lambda: {"prod": 0.0, "unlinked": 0.0, "ship_ids": set()})
    for r in ph_all_xl:
        sh   = ship_map_xl.get(r.get("shipment_id", ""))
        bid  = r.get("buyer_id") or (sh or {}).get("buyer_id", "")
        prod = (buyer_map_l.get(bid, {}).get("product") or "미지정").upper()
        out  = float(r.get("output_kg", 0) or 0)
        _fgx[prod]["prod"] += out
        if sh:
            _fgx[prod]["ship_ids"].add(r["shipment_id"])
        else:
            _fgx[prod]["unlinked"] += out
    if _fgx:
        merge_cell(ROW, 1, 5, "  ⑨ 완제품(BP/BM) 재고 추정 = 생산 누계 − 선적 누계 (미연결 배치는 전량 재고)", bg="2E75B6"); ROW += 1
        for ci, h in enumerate(["제품", "생산 누계(kg)", "선적 누계(kg)", "미연결 배치 생산(kg)", "재고 추정(kg)"], 1):
            cell(ROW, ci, h, bold=True, color="FFFFFF", bg="4472C4", size=9)
        ROW += 1
        for prod, v in sorted(_fgx.items()):
            shipped = sum(float(ship_map_xl[s].get("weight_kg", 0) or 0) for s in v["ship_ids"])
            for ci, val in enumerate([prod, round(v["prod"]), round(shipped), round(v["unlinked"]),
                                      round(v["prod"] - shipped)], 1):
                cell(ROW, ci, val, fmt="#,##0" if ci > 1 else None)
            ROW += 1

    # ── 컬럼 너비 및 동결 ──
    from openpyxl.utils import get_column_letter
    col_widths = [18, 20, 12, 13, 14, 13, 14, 16, 14, 14]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A3"

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()


@st.cache_data(show_spinner=False, max_entries=4, hash_funcs={dict: _cfg_fingerprint})
def _excel_report_cached(cfg, ni, co, xr, ref_month, sel_buyer_id, todo=None, cash=None):
    """generate_excel_report 결과를 데이터 지문(cfg 내용)·INDEX·환율·기준월·할 일·현금 전망으로 캐시.
    요약 보고서 코드는 페이지를 조작할 때마다 실행되므로, 캐시가 없으면 클릭마다
    엑셀 워크북을 새로 만든다(측정 약 0.6초). 데이터가 바뀌면 지문이 바뀌어 자동 재생성."""
    return generate_excel_report(cfg, ni, co, xr, ref_month, sel_buyer_id, todo, cash)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 0 — 요약 보고서
# ══════════════════════════════════════════════════════════════════════════════
if _page == PG_HOME:
    st.subheader("홈")

    # ── 헤더 바 ──────────────────────────────────────────────────────────────
    ro1, ro2 = st.columns([2, 1])
    with ro1:
        _rpt_month_opts = hist_opts if hist_opts else [f"{date.today().year}-{date.today().month:02d}"]
        rpt_month = st.selectbox("기준월", _rpt_month_opts, key="rpt_month_sel")
        st.markdown(f"**작성일**: `{date.today()}`  |  **Ni**: `\\${NI:,.2f}/t`  **Co**: `\\${CO:,.2f}/t`  **KRW**: `{XR:,.0f}`")
    with ro2:
        st.caption("엑셀 보고서 다운로드는 아래 '미수 현금 전망' 다음에 있습니다 (할 일·현금 전망을 포함해 생성).")

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # 할 일 패널 — 앱 곳곳에 흩어진 경고를 한 곳에 모은 액션 목록
    # ══════════════════════════════════════════════════════════════════════════
    _td_ships  = cfg.get("shipments", [])
    _td_buyers = {b["id"]: b for b in cfg["buyers"]}
    _td_hm     = {h["month"]: h for h in cfg.get("index_history", [])}
    _td_today  = date.today()

    from urllib.parse import quote as _urlq
    def _td_link(hbl):
        """HBL → 선적 정산 서브페이지의 해당 편집 폼으로 가는 링크 (?page=ship&sub=선적 정산&hbl=…)."""
        return f"[{hbl}](?page=ship&sub={_urlq(SUB_SHIP)}&hbl={_urlq(hbl)})"
    def _td_hbls(ships, limit=4):
        _ls = [s.get("hbl", "").strip() or "HBL미정" for s in ships]
        return ", ".join(_ls[:limit]) + (f" 외 {len(_ls)-limit}건" if len(_ls) > limit else "")
    # 화면 표시 시에만 HBL 문자열을 링크로 바꾼다 (엑셀 보고서에는 평문 그대로 들어가야 함)
    _td_all_hbl = sorted({s.get("hbl", "").strip() for s in _td_ships if s.get("hbl", "").strip()},
                         key=len, reverse=True)
    def _td_linkify(text):
        for _h in _td_all_hbl:
            text = re.sub(rf"(?<![\w\]/=\-]){re.escape(_h)}(?![\w\-])", _td_link(_h), text)
        return text
    _TD_LOC = {   # 처리 위치 라벨 → (page slug, 서브페이지)
        "선적·계약 > 선적 정산":                    ("ship",   SUB_SHIP),
        "재고·임가공 > 임가공사·배치 > 세부 내역":   ("stock",  SUB_PROC),
        "마스터·동기화 > INDEX·환율·판관비":         ("master", SUB_INDEX),
    }
    def _td_loc(label):
        _pg, _sb = _TD_LOC.get(label, (None, None))
        return f"[{label}](?page={_pg}&sub={_urlq(_sb)})" if _pg else f"`{label}`"

    _todo = []   # (심각도 도형, 제목, 상세, 처리 위치)

    # 1) 확정 스냅샷이 최신 계산식과 어긋난 건
    _td_recalc = []
    for _ts in _td_ships:
        if _ts.get("status") in ("final", "paid") and _ts.get("final_amount_usd"):
            _tl = _recompute_final_settlement(cfg, _ts)
            if _tl is not None and abs(_tl - float(_ts["final_amount_usd"])) >= 0.01:
                _td_recalc.append(_ts)
    if _td_recalc:
        _todo.append(("🔴", f"확정액 재계산 필요 {len(_td_recalc)}건",
                      _td_hbls(_td_recalc), "선적·계약 > 선적 정산"))

    # 2) 고아 배치 (삭제된 선적건에 연결된 배치)
    _td_sids   = {s["id"] for s in _td_ships}
    _td_orphan = sum(1 for p in cfg.get("processing_history", [])
                     if p.get("shipment_id", "") and p.get("shipment_id", "") not in _td_sids)
    if _td_orphan:
        _todo.append(("🔴", f"고아 배치 {_td_orphan}건",
                      "삭제된 선적건에 연결된 배치", "재고·임가공 > 임가공사·배치 > 세부 내역"))

    # 3) 전월 INDEX 미등록
    _td_prev_m = (_td_today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    if _td_prev_m not in _td_hm:
        _todo.append(("🟡", f"전월({_td_prev_m}) INDEX 미등록",
                      "확정산 계산에 필요할 수 있음", "마스터·동기화 > INDEX·환율·판관비"))

    # 4) 확정산 진행 가능 (Final월 INDEX가 이미 등록된 provisional 건)
    _td_ready = [s for s in _td_ships
                 if s.get("status") == "provisional"
                 and s.get("final_month", "—") not in ("—", "")
                 and s.get("final_month") in _hm_for(cfg, _td_buyers.get(s.get("buyer_id",""), {}))]
    if _td_ready:
        _todo.append(("🟡", f"확정산 진행 가능 {len(_td_ready)}건",
                      _td_hbls(_td_ready), "선적·계약 > 선적 정산"))

    # 5) 수출비 미입력
    _td_no_eu = [s for s in _td_ships if not s.get("export_cost_usd")]
    if _td_no_eu:
        _todo.append(("🟡", f"수출비 미입력 {len(_td_no_eu)}건",
                      _td_hbls(_td_no_eu), "선적·계약 > 선적 정산"))

    # 6) ETA 14일 이내 도착 예정 (미확정 건)
    _td_eta = [s for s in _td_ships
               if s.get("eta", "") and s.get("eta", "") >= _td_today.isoformat()
               and s.get("eta", "") <= (_td_today + timedelta(days=14)).isoformat()
               and s.get("status", "") != "final"]
    if _td_eta:
        _todo.append(("🟡", f"ETA 14일 이내 도착 예정 {len(_td_eta)}건",
                      _td_hbls(_td_eta), "선적·계약 > 선적 정산"))

    # 7) Invoice 금액이 가정산 단가×중량과 1% 이상 어긋난 건 (입력 오타·기준월 오류 의심)
    _td_inv_bad = []
    for _ts in _td_ships:
        _iv = float(_ts.get("invoice_usd") or 0)
        _ic = _prov_invoice_calc(cfg, _ts) if _iv > 0 else None
        if _ic and abs(_ic - _iv) / _iv > 0.01:
            _td_inv_bad.append(_ts)
    if _td_inv_bad:
        _todo.append(("🟡", f"Invoice 금액 불일치 {len(_td_inv_bad)}건",
                      _td_hbls(_td_inv_bad) + " — 가정산 단가×중량 대비 1% 초과 차이", "선적·계약 > 선적 정산"))

    # 8) 선적 중량 vs 연결 배치 생산량 합이 2% 이상 다른 건 (배치 누락·중복 의심)
    _td_out_by_sid = defaultdict(float)
    for _tp in cfg.get("processing_history", []):
        if _tp.get("shipment_id"):
            _td_out_by_sid[_tp["shipment_id"]] += float(_tp.get("output_kg", 0) or 0)
    _td_wt_bad = [s for s in _td_ships
                  if s.get("id") in _td_out_by_sid and float(s.get("weight_kg") or 0) > 0
                  and abs(_td_out_by_sid[s["id"]] - float(s["weight_kg"])) / float(s["weight_kg"]) > 0.02]
    if _td_wt_bad:
        _todo.append(("🟡", f"선적 중량·배치 생산량 불일치 {len(_td_wt_bad)}건",
                      _td_hbls(_td_wt_bad) + " — 2% 초과 차이", "재고·임가공 > 임가공사·배치 > 세부 내역"))

    # 9) 입금완료 상태인데 확정산 입금 기록이 없는 건
    _td_paid_norec = [s for s in _td_ships if s.get("status") == "paid" and not s.get("final_paid_date")]
    if _td_paid_norec:
        _todo.append(("🟡", f"입금완료 상태인데 입금 기록 없음 {len(_td_paid_norec)}건",
                      _td_hbls(_td_paid_norec) + " — 입금일·금액 입력", "선적·계약 > 선적 정산"))

    if _todo:
        with st.expander(f"할 일 — {len(_todo)}개 항목", expanded=True):
            for _dot, _title, _detail, _tab in _todo:
                st.markdown(f"{_dot} **{_title}** — {_td_linkify(_detail)}  ·  {_td_loc(_tab)}")
    else:
        st.caption("📌 할 일: 처리할 항목이 없습니다.")

    # ══════════════════════════════════════════════════════════════════════════
    # 미수 현금 전망 — 미입금 선적건의 확정산 잔액 (청구 가능 vs INDEX 대기)
    # ══════════════════════════════════════════════════════════════════════════
    _cf_rows = []
    for _cs in _td_ships:
        if _cs.get("status") not in ("provisional", "final"):
            continue
        _cb    = _td_buyers.get(_cs.get("buyer_id", ""), {})
        _cst   = _settle_terms(_get_contract_for_shipment(cfg, _cs.get("id", "")), _cb)
        _cpp   = float(_cs.get("invoice_usd") or 0) * (_cst["prov_pct"] / 100.0)
        _cadj  = float(_cs.get("other_adj_usd") or 0)
        _csnap = _cs.get("final_amount_usd")
        if _csnap:
            _camt, _cbasis = float(_csnap), "확정"
        else:
            _ccalc = _recompute_final_settlement(cfg, _cs)
            if _ccalc is not None:
                _camt, _cbasis = _ccalc, "계산"
            else:
                # Final월 INDEX 미등록 → 최신 INDEX로 추정 (참고치)
                _camt   = _recompute_final_settlement(cfg, _cs, fallback_index=(NI, CO))
                _cbasis = "추정"
        if _camt is None:
            continue  # 매입사/계약 정보 미비 등 — 전망에서 제외
        _cnet = _camt - _cpp + _cadj - float(_cs.get("final_paid_usd") or 0)   # 이미 입금된 확정산 차감
        if abs(_cnet) < 1:
            continue  # 확정산까지 입금 완료
        _cfm  = _cs.get("final_month", "—")
        if _cbasis in ("확정", "계산"):
            _cwhen = "청구 가능"
        elif _cfm not in ("—", ""):
            _cwhen = f"{_cfm} INDEX 대기"
        else:
            _cwhen = "Final월 미지정"
        # 예상 입금일 = (ETA, 없으면 선적일+60일) + 매입사 확정산 입금 조건(미설정 시 30일)
        _cfd = int(_cb.get("final_pay_days") or 0) or 30
        try:
            _cbase = (date.fromisoformat(_cs["eta"]) if _valid_date_str(_cs.get("eta", ""))
                      else date.fromisoformat(_cs["loading_date"]) + timedelta(days=60))
            _cexp = (_cbase + timedelta(days=_cfd)).isoformat()
        except Exception:
            _cexp = ""
        _cf_rows.append({
            "구분":        _cwhen,
            "HBL":         _cs.get("hbl", "").strip() or "HBL미정",
            "매입사":      _cb.get("name", "?"),
            "상태":        _cs.get("status", ""),
            "Final월":     _cfm,
            "기준":        _cbasis,
            "가정산 수령": round(_cpp, 0),
            "확정산 잔액": round(_cnet, 0),
            "예상 입금일": _cexp or "미정",
            "예상 입금월": _cexp[:7] or "미정",
        })

    st.markdown("#### 미수 현금 전망")
    if not _cf_rows:
        st.caption("미입금 선적건이 없습니다.")
    else:
        _cf_now  = sum(r["확정산 잔액"] for r in _cf_rows if r["구분"] == "청구 가능")
        _cf_wait = sum(r["확정산 잔액"] for r in _cf_rows if r["구분"] != "청구 가능")
        _cf_tot  = _cf_now + _cf_wait
        _cfc1, _cfc2, _cfc3 = st.columns(3)
        _cfc1.markdown(_kpi_card("청구 가능 (INDEX 확정)", f"${_cf_now:+,.0f}",
                                 f"{sum(1 for r in _cf_rows if r['구분'] == '청구 가능')}건",
                                 val_color="#4ade80" if _cf_now >= 0 else "#f87171"),
                       unsafe_allow_html=True)
        _cfc2.markdown(_kpi_card("INDEX 대기 (추정)", f"${_cf_wait:+,.0f}",
                                 "최신 INDEX 기준 추정 — Final월 INDEX 등록 시 변동",
                                 val_color="#9b9b9b"),
                       unsafe_allow_html=True)
        _cfc3.markdown(_kpi_card("합계 (미수 확정산)", f"${_cf_tot:+,.0f}",
                                 f"KRW ₩{_cf_tot*XR:+,.0f}",
                                 val_color="#4ade80" if _cf_tot >= 0 else "#f87171"),
                       unsafe_allow_html=True)
        # 월별 예상 입금 일정
        _cf_by_mon = defaultdict(lambda: {"건수": 0, "금액": 0.0})
        for _r in _cf_rows:
            _cf_by_mon[_r["예상 입금월"]]["건수"] += 1
            _cf_by_mon[_r["예상 입금월"]]["금액"] += _r["확정산 잔액"]
        _cf_this_m = date.today().strftime("%Y-%m")
        _cf_mon_rows = [{"예상 입금월": _k, "건수": _v["건수"], "예상 입금액": round(_v["금액"], 0),
                         "비고": "지연" if (_k != "미정" and _k < _cf_this_m) else ""}
                        for _k, _v in sorted(_cf_by_mon.items())]
        st.markdown("**월별 예상 입금 (확정산 잔액)**")
        st.caption("예상 입금일 = (ETA, 없으면 선적일+60일) + 매입사별 확정산 입금 조건(매입사 관리에서 설정, 미설정 시 30일). "
                   "'지연'은 예상월이 이미 지난 건입니다.")
        st.dataframe(pd.DataFrame(_cf_mon_rows).style.format({"예상 입금액": "${:+,.0f}"}),
                     use_container_width=True, hide_index=True)
        with st.expander("선적건별 상세", expanded=False):
            st.caption("가정산은 수령 완료로 간주합니다. '추정'은 최신 INDEX로 계산한 참고치이며 "
                       "실제 입금 시기는 매입사 정산 관행에 따라 다릅니다. 음수는 반환 예정액입니다.")
            _cf_rows.sort(key=lambda r: (r["구분"] != "청구 가능", r["Final월"]))
            st.dataframe(
                pd.DataFrame(_cf_rows), use_container_width=True, hide_index=True,
                column_config=_cc_money("가정산 수령", "확정산 잔액", dec=0),
            )

    # ── 엑셀 보고서 (대시보드 요약과 동일 기준: 할 일·현금 전망·완제품 재고 포함) ──
    if active_buyers:
        _xl_bytes = _excel_report_cached(cfg, NI, CO, XR, rpt_month, active_buyers[0]["id"],
                                         _todo, _cf_rows)
        st.download_button("Excel 보고서 다운로드 (요약·할 일·현금 전망·손익·선적·완제품 재고)",
                           data=_xl_bytes, file_name=f"BP_BM_요약보고서_{rpt_month}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.divider()

    # ── 공통 데이터 준비 ──────────────────────────────────────────────────────
    _rpt_ships    = cfg.get("shipments", [])
    _rpt_ph_all   = cfg.get("processing_history", [])
    _rpt_buyer_m0 = {b["id"]: b for b in cfg["buyers"]}
    _rpt_ship_m0  = {s["id"]: s for s in _rpt_ships}

    # ── 연간 누계 요약 ────────────────────────────────────────────────────────
    _cur_year = date.today().year
    _yr_ph    = [r for r in _rpt_ph_all
                 if (_rpt_ship_m0.get(r.get("shipment_id",""),{}).get("loading_date","") or "")[:4] == str(_cur_year)]
    _yr_ships = [s for s in _rpt_ships if (s.get("loading_date","") or "")[:4] == str(_cur_year)]
    _yr_bp    = sum(float(r.get("bp_sale_per_kg",0) or 0) * float(r.get("output_kg",0) or 0) for r in _yr_ph)
    _yr_pf    = sum(float(r.get("processing_fee_per_kg",0) or 0) * _ph_input_kg(r) for r in _yr_ph)
    _yr_eu    = sum(_ph_export_usd(r, cfg) for r in _yr_ph)
    _yr_out   = sum(float(r.get("output_kg",0) or 0) for r in _yr_ph)
    _yr_inv   = sum(float(s.get("invoice_usd",0) or 0) for s in _yr_ships)
    # 관리회계 기준: 원료비(FIFO 우선)·보관비까지 차감한 실질 손익 (판관비 제외)
    _rctx     = _pnl_context(cfg)          # 손익 탭과 같은 엔진 — 탭 실행 순서 무관
    _yr_raw   = sum(_rctx["rmc_fifo"](r)[0] * _ph_input_kg(r) for r in _yr_ph)
    _yr_stor  = sum(_rctx["eff_storage"](r) for r in _yr_ph)
    _yr_real  = _yr_bp - _yr_raw - _yr_pf - _yr_eu - _yr_stor

    # ── 월별 집계 (카드 전월 대비 배지 + 아래 월별 구성 차트 공용) ──
    _mo_agg = defaultdict(lambda: {"bp": 0.0, "pf": 0.0, "eu": 0.0, "raw": 0.0, "stor": 0.0,
                                   "out": 0.0, "cnt": 0, "inv": 0.0})
    for r in _yr_ph:
        _mo_key = (_rpt_ship_m0.get(r.get("shipment_id",""), {}).get("loading_date","") or "")[:7]
        if not _mo_key:
            continue
        _mo_agg[_mo_key]["bp"]   += float(r.get("bp_sale_per_kg",0) or 0) * float(r.get("output_kg",0) or 0)
        _mo_agg[_mo_key]["pf"]   += float(r.get("processing_fee_per_kg",0) or 0) * _ph_input_kg(r)
        _mo_agg[_mo_key]["eu"]   += _ph_export_usd(r, cfg)
        _mo_agg[_mo_key]["raw"]  += _rctx["rmc_fifo"](r)[0] * _ph_input_kg(r)
        _mo_agg[_mo_key]["stor"] += _rctx["eff_storage"](r)
        _mo_agg[_mo_key]["out"]  += float(r.get("output_kg",0) or 0)
    for s in _yr_ships:
        _mo_key = (s.get("loading_date","") or "")[:7]
        if _mo_key:
            _mo_agg[_mo_key]["cnt"] += 1
            _mo_agg[_mo_key]["inv"] += float(s.get("invoice_usd",0) or 0)
    _mo_rows = []
    for _mk in sorted(_mo_agg.keys()):
        _mv = _mo_agg[_mk]
        _mo_rows.append({"월": _mk, "매출(BP)": round(_mv["bp"], 2), "원료 매입비": round(_mv["raw"], 2),
                         "임가공비(순)": round(_mv["pf"], 2), "수출비": round(_mv["eu"], 2),
                         "보관비": round(_mv["stor"], 2),
                         "실질 손익": round(_mv["bp"] - _mv["raw"] - _mv["pf"] - _mv["eu"] - _mv["stor"], 2),
                         "생산(kg)": _mv["out"], "선적": _mv["cnt"], "Invoice": _mv["inv"]})
    # 전월 대비: 데이터가 있는 최근 두 달을 비교 (이번 달 실적이 아직 없으면 직전 두 달)
    _mo_last, _mo_prev = (_mo_rows[-1], _mo_rows[-2]) if len(_mo_rows) >= 2 else (None, None)
    def _mom_badge(key, fmt_abs, pct=True):
        """(배지 문구, 색) — 최근월 vs 직전월 증감."""
        if not _mo_last:
            return "", "#9b9b9b"
        _d = _mo_last[key] - _mo_prev[key]
        if abs(_d) < 1e-9:
            return f"{_mo_last['월'][5:]}월 보합", "#9b9b9b"
        _arrow = "▲" if _d > 0 else "▼"
        _col   = _C_POS if _d > 0 else _C_NEG
        _txt   = f"{_arrow} {fmt_abs(abs(_d))}"
        if pct and _mo_prev[key]:
            _txt += f" ({_d / abs(_mo_prev[key]) * 100:+.0f}%)"
        return f"{_mo_last['월'][5:]}월 {_txt}", _col
    _b_cnt = _mom_badge("선적",     lambda v: f"{v:.0f}건", pct=False)
    _b_out = _mom_badge("생산(kg)", lambda v: f"{v/1000:.1f} MT")
    _b_inv = _mom_badge("Invoice",  lambda v: f"${v/1000:,.0f}k")
    _b_rl  = _mom_badge("실질 손익", lambda v: f"${v/1000:,.0f}k", pct=False)

    _yr_ships_ly  = [s for s in _rpt_ships if (s.get("loading_date","") or "")[:4] == str(_cur_year - 1)]
    _yoy_sub      = f"전년 동기 {len(_yr_ships) - len(_yr_ships_ly):+d}건"
    _yr_input_kg  = sum(float(r.get("input_kg",0) or 0) for r in _yr_ph) or 1
    _conv_sub     = f"투입 대비 전환율 {_yr_out / _yr_input_kg * 100:.1f}%"
    _inv_sub      = f"평균 ${(_yr_inv / len(_yr_ships) / 1000):.0f}k / 건" if _yr_ships else "선적 없음"
    _margin_pct   = (_yr_real / _yr_bp * 100) if _yr_bp else 0
    _margin_sub   = f"매출 대비 {_margin_pct:+.1f}% · 판관비 제외"
    _margin_col   = "#4ade80" if _yr_real >= 0 else "#f87171"
    _margin_fmt   = (f"${_yr_real/1_000_000:+.1f}M" if abs(_yr_real) >= 1_000_000
                     else f"${_yr_real/1000:+.0f}k")

    st.markdown(f"#### {_cur_year}년 누계")
    _ya1, _ya2, _ya3, _ya4 = st.columns(4)
    _ya1.markdown(_kpi_card_badge("선적 건수",    *_b_cnt, f"{len(_yr_ships)}건",        _yoy_sub),   unsafe_allow_html=True)
    _ya2.markdown(_kpi_card_badge("BP 생산",      *_b_out, f"{_yr_out/1000:.1f} MT",     _conv_sub),  unsafe_allow_html=True)
    _ya3.markdown(_kpi_card_badge("Invoice 합계", *_b_inv, f"${_yr_inv/1_000_000:.1f}M", _inv_sub),   unsafe_allow_html=True)
    _ya4.markdown(_kpi_card_badge("실질 손익",    *_b_rl,  _margin_fmt, _margin_sub, val_color=_margin_col), unsafe_allow_html=True)
    st.caption("배지: 실적이 있는 최근 월과 그 직전 월의 비교")

    st.divider()
    st.markdown("#### 현재 운영 현황")

    # ── 미수금 / ETA 임박 / 계약 잔여 ─────────────────────────────────────────
    _all_ships   = cfg.get("shipments", [])
    _buyer_m_rpt = {b["id"]: b for b in cfg["buyers"]}
    _today_rpt   = date.today()
    _eta14_end   = (_today_rpt + timedelta(days=14)).isoformat()

    # 미수금: 상단 '미수 현금 전망' 패널과 동일 기준 (_cf_rows 재사용 — 확정/계산/추정 통합)
    _ar_total = sum(r["확정산 잔액"] for r in _cf_rows)
    _ar_cnt   = len(_cf_rows)

    _eta_soon = [s for s in _all_ships
                 if s.get("eta","") and _today_rpt.isoformat() <= s.get("eta","") <= _eta14_end
                 and s.get("status","") != "paid"]

    _ct_remaining = 0.0
    for _ctc in cfg.get("contracts", []):
        if _ctc.get("contract_status","active") != "active":
            continue
        _mc = _contract_metrics(cfg, _ctc)
        _ct_remaining += _mc["remaining_mt"]

    _ar_fmt      = (f"${_ar_total/1_000_000:.1f}M" if abs(_ar_total) >= 1_000_000
                    else f"${_ar_total/1000:.0f}k")
    _eta_hbls    = "  ·  ".join(s.get("hbl","—") for s in _eta_soon) or "없음"
    _ct_border   = "#f87171" if _ct_remaining > 0 else ""
    _ct_val_col  = "#f87171" if _ct_remaining > 0 else "#e5e5e5"
    _prov_cnt    = sum(1 for s in _all_ships if s.get("status","") == "provisional")
    _final_cnt   = sum(1 for s in _all_ships if s.get("status","") == "final")

    _yb1, _yb2, _yb3, _yb4 = st.columns(4)
    _yb1.markdown(_kpi_card_badge("미수금 추정", f"{_ar_cnt}건 미정산", "#fb923c",
                                  _ar_fmt, "미수 현금 전망 패널과 동일 기준 (확정산 잔액)"),
                  unsafe_allow_html=True)
    _yb2.markdown(_kpi_card_badge("ETA 14일 이내", f"{len(_eta_soon)}건", "#60a5fa",
                                  f"{len(_eta_soon)}건", _eta_hbls),
                  unsafe_allow_html=True)
    _yb3.markdown(_kpi_card("계약 잔여 의무",
                             f"{_ct_remaining:,.1f} MT",
                             "진행 중 계약 최소 이행 잔량",
                             val_color=_ct_val_col, left_border=_ct_border),
                  unsafe_allow_html=True)
    _yb4.markdown(_kpi_card("미정산 건수",
                             f"{_ar_cnt}건",
                             f"provisional {_prov_cnt} · final {_final_cnt}"),
                  unsafe_allow_html=True)

    # ── 월별 손익 구성 추이 (관리회계 기준 — 원료비·보관비 차감, 판관비 제외) ──
    if _mo_rows:
        try:
            st.markdown(f"#### {_cur_year}년 월별 손익 구성")
            st.caption("매출은 위로, 원료비·임가공비·수출비·보관비는 아래로 쌓고 실질 손익을 선으로 표시 — "
                       "손익·시나리오 > 손익 요약의 월별 추이와 같은 기준")
            st.plotly_chart(_fig_monthly_pnl(_mo_rows, height=340), use_container_width=True)
        except ImportError:
            pass

# ══════════════════════════════════════════════════════════════════════════════
# TAB — 계약 이행
# ══════════════════════════════════════════════════════════════════════════════

if _page == PG_SHIP and _sub == SUB_CONTRACT:
    st.markdown("### 계약 이행 현황")

    _ct_list    = cfg.setdefault("contracts", [])
    _ct_buyers  = {b["id"]: b for b in cfg.get("buyers", [])}
    _ct_scraps  = {s["id"]: s for s in cfg.get("scrap_types", [])}
    _ct_procs   = {p["id"]: p for p in cfg.get("processors", [])}
    _ct_sc_opts = {s["name"]: s["id"] for s in cfg.get("scrap_types", []) if s.get("active", True)}
    _ct_by_opts = {}
    for _b in cfg.get("buyers", []):
        if not _b.get("active", True):
            continue
        _lbl = f"{_b['name']} ({_b['product']})"
        if _lbl in _ct_by_opts:
            _old_id = _ct_by_opts.pop(_lbl)
            _ct_by_opts[f"{_lbl} [{_old_id[:4]}]"] = _old_id
            _lbl = f"{_lbl} [{_b['id'][:4]}]"
        _ct_by_opts[_lbl] = _b["id"]
    _ct_pr_opts = {"전체 (구분 없음)": ""} | {p["name"]: p["id"] for p in cfg.get("processors", []) if p.get("active", True)}

    # ── 계약 등록 ────────────────────────────────────────────────────────────
    with st.expander("계약 등록", expanded=not _ct_list):
        _cf1, _cf2 = st.columns(2)
        _ct_buyer_sel = _cf1.selectbox("매입사",   list(_ct_by_opts), key="ct_buyer")
        _ct_sc_sel    = _cf2.selectbox("원료 유형", list(_ct_sc_opts), key="ct_sc")
        _cf3, _cf4, _cf5 = st.columns(3)
        _ct_qty  = _cf3.number_input("계약량 (MT)", min_value=0.0, step=1.0, format="%.1f", key="ct_qty")
        _ct_tol  = _cf4.number_input("허용 오차 (%)", min_value=0.0, max_value=20.0, value=5.0, step=1.0, format="%.0f", key="ct_tol")
        _ct_prod = _cf5.selectbox("제품", ["BP", "BM"], key="ct_prod")
        _cf6, _cf7, _cf8 = st.columns(3)
        _ct_start  = _cf6.text_input("계약 시작일 (YYYY-MM-DD)", key="ct_start")
        _ct_end    = _cf7.text_input("계약 종료일 (YYYY-MM-DD)", key="ct_end")
        _ct_pr_sel = _cf8.selectbox("임가공사 (선택)", list(_ct_pr_opts), key="ct_proc",
                                     help="지정 시 해당 임가공사 재고만 충당에 반영")
        # ── 가격·정산 조건 ────────────────────────────────────────────────
        st.markdown("**💰 가격·정산 조건** (선택 — 미입력 시 매입사 기본값 사용)")
        _cp1, _cp2, _cp3 = st.columns(3)
        _ct_ni_pay = _cp1.number_input("Ni 지불율 (%)",  min_value=0.0, value=0.0,
                                        step=0.1, format="%.2f", key="ct_ni_pay",
                                        help="0이면 매입사 기본 지불율 사용")
        _ct_co_pay = _cp2.number_input("Co 지불율 (%)",  min_value=0.0, value=0.0,
                                        step=0.1, format="%.2f", key="ct_co_pay",
                                        help="0이면 매입사 기본 지불율 사용")
        _ct_prov_pct = _cp3.number_input("가정산 비율 (%)", min_value=0.0, value=100.0,
                                          step=5.0, format="%.0f", key="ct_prov_pct",
                                          help="예: 80 → Invoice의 80%, 125 → Invoice의 125% 지급")
        _cp4, _cp5 = st.columns(2)
        _prov_idx_map  = {"가정산월 INDEX": "prov", "선적월 INDEX": "loading", "특정월 지정": "custom"}
        _final_idx_map = {"확정정산월 INDEX": "final", "선적월 INDEX": "loading", "가정산월 INDEX": "prov", "특정월 지정": "custom"}
        _ct_prov_idx  = _cp4.selectbox("Provisional INDEX 기준", list(_prov_idx_map),  key="ct_prov_idx")
        _ct_final_idx = _cp5.selectbox("Final INDEX 기준",       list(_final_idx_map), key="ct_final_idx")
        # 특정월 지정 시 월 입력
        _ct_prov_month_fixed = ""
        _ct_final_month_fixed = ""
        if _prov_idx_map[_ct_prov_idx] == "custom":
            _ct_prov_month_fixed = _cp4.text_input("Provisional 기준월 (YYYY-MM)", placeholder="예: 2025-03", key="ct_prov_fixed_m")
        if _final_idx_map[_ct_final_idx] == "custom":
            _ct_final_month_fixed = _cp5.text_input("Final 기준월 (YYYY-MM)", placeholder="예: 2025-06", key="ct_final_fixed_m")
        _ct_notes = st.text_input("메모", key="ct_notes")
        if st.button("계약 등록", key="ct_add_btn"):
            def _is_valid_date(s):
                if not s.strip(): return True
                try: date.fromisoformat(s.strip()); return True
                except ValueError: return False
            _prov_basis_val  = _ct_prov_month_fixed.strip()  if _prov_idx_map[_ct_prov_idx]  == "custom" else _prov_idx_map[_ct_prov_idx]
            _final_basis_val = _ct_final_month_fixed.strip() if _final_idx_map[_ct_final_idx] == "custom" else _final_idx_map[_ct_final_idx]
            if not _ct_buyer_sel or not _ct_sc_sel or _ct_qty <= 0:
                st.error("매입사, 원료 유형, 계약량을 입력하세요.")
            elif not _is_valid_date(_ct_start) or not _is_valid_date(_ct_end):
                st.error("날짜 형식 오류 — YYYY-MM-DD 형식으로 입력하세요. (예: 2026-05-01)")
            elif _prov_idx_map[_ct_prov_idx] == "custom" and (not _prov_basis_val or len(_prov_basis_val) != 7):
                st.error("Provisional 기준월을 YYYY-MM 형식으로 입력하세요. (예: 2025-03)")
            elif _final_idx_map[_ct_final_idx] == "custom" and (not _final_basis_val or len(_final_basis_val) != 7):
                st.error("Final 기준월을 YYYY-MM 형식으로 입력하세요. (예: 2025-06)")
            else:
                _ct_list.append({
                    "id":                str(uuid.uuid4())[:8],
                    "buyer_id":          _ct_by_opts[_ct_buyer_sel],
                    "product":           _ct_prod,
                    "scrap_type_id":     _ct_sc_opts[_ct_sc_sel],
                    "processor_id":      _ct_pr_opts[_ct_pr_sel],
                    "contract_qty_mt":   _ct_qty,
                    "tolerance_pct":     _ct_tol,
                    "start_date":        _ct_start.strip(),
                    "end_date":          _ct_end.strip(),
                    "notes":             _ct_notes.strip(),
                    "contract_status":   "active",
                    "ni_payable_pct":    _ct_ni_pay   if _ct_ni_pay   > 0 else None,
                    "co_payable_pct":    _ct_co_pay   if _ct_co_pay   > 0 else None,
                    "prov_pct":          _ct_prov_pct if _ct_prov_pct != 100.0 else None,
                    "prov_index_basis":  _prov_basis_val,
                    "final_index_basis": _final_basis_val,
                })
                cfg["contracts"] = _ct_list
                save_cfg(cfg)
                st.success("계약 등록 완료")
                st.rerun()

    if not _ct_list:
        st.info("등록된 계약이 없습니다.")
    else:
        # ── 계약 상태 필터 ────────────────────────────────────────────────────
        _ct_status_opts = ["active", "closed", "cancelled"]
        _ct_status_labels = {"active": "진행 중", "closed": "완료", "cancelled": "취소"}
        _ct_stat_filter = st.multiselect(
            "계약 상태 필터", _ct_status_opts,
            default=["active"],
            format_func=lambda s: _ct_status_labels.get(s, s),
            key="ct_stat_filter",
        )
        _ct_list_show = [c for c in _ct_list
                         if c.get("contract_status", "active") in _ct_stat_filter]

        # ── 재고 현황 요약 (임가공사별) ───────────────────────────────────────
        st.markdown("#### 가용 재고 현황")
        _inv_cols = st.columns(len(active_scraps)) if active_scraps else []
        for _ci, _sc in enumerate(active_scraps):
            _cv = _avg_conv_rate(cfg, _sc["id"])
            _, _, _lr = _fifo_lot_trace(cfg, _sc["id"])
            _wh = sum(lot.get("remain", 0) for lot in _lr)
            with _inv_cols[_ci]:
                st.markdown(f"**{_sc['name']}**  `전환율 {_cv:.0f}%`")
                _ic1, _ic2 = st.columns(2)
                _ic1.markdown(_kpi_card("창고 원료",           f"{_wh/1000:,.2f} MT", "FIFO 잔량"), unsafe_allow_html=True)
                # 임가공사별 분류
                _ap_total = 0.0
                _ap_rows  = []
                for _pr in active_procs:
                    _ap_pr = _at_processor_raw_kg(cfg, _sc["id"], _pr["id"])
                    if _ap_pr > 0:
                        _ap_total += _ap_pr
                        _ap_rows.append((_pr["name"], _ap_pr))
                _ic2.markdown(_kpi_card("임가공사 (원료 합계)", f"{_ap_total/1000:,.2f} MT", "출하 − 투입 누계"), unsafe_allow_html=True)
                if _ap_rows:
                    for _prname, _apkg in _ap_rows:
                        st.caption(f"  └ {_prname}: {_apkg/1000:,.2f} MT → BP {_apkg*_cv/100/1000:,.2f} MT")
                st.caption(f"BP 환산 합계: **{(_wh+_ap_total)*_cv/100/1000:,.2f} MT**")

        st.divider()

        # ── 계약별 이행 현황 ──────────────────────────────────────────────────
        st.markdown("#### 계약별 이행 현황")
        _ship_map_disp = {s["id"]: s for s in cfg.get("shipments", [])}
        for _ct in _ct_list_show:
            _ct_id   = _ct.get("id","")
            _ct_buyer_obj = _ct_buyers.get(_ct.get("buyer_id",""), {})
            _bname   = f"{_ct_buyer_obj.get('name','—')} ({_ct_buyer_obj.get('product','')})" if _ct_buyer_obj else "—"
            _scname  = _ct_scraps.get(_ct.get("scrap_type_id",""), {}).get("name", "—")
            _prname  = _ct_procs.get(_ct.get("processor_id",""), {}).get("name", "") if _ct.get("processor_id") else ""
            _m       = _contract_metrics(cfg, _ct)

            _ct_cstatus = _ct.get("contract_status", "active")
            _ct_cst_lbl = {"active": "진행 중", "closed": "완료", "cancelled": "취소"}.get(_ct_cstatus, _ct_cstatus)
            _ct_cst_ico = {"active": "🟢", "closed": "🔵", "cancelled": "⚫"}.get(_ct_cstatus, "⚪")
            _stat_color = {"complete": "🟢", "ok": "🟡", "short": "🔴"}.get(_m["status"], "⚪")
            _stat_label = {"complete": "이행 완료", "ok": "재고 충분", "short": "재고 부족"}.get(_m["status"], "—")

            # 이행률 progress bar — expander 바깥에서 항상 표시
            _prog_pct  = min(1.0, _m["shipped_mt"] / _m["max_mt"]) if _m["max_mt"] else 0
            _prog_pct  = 1.0 if _m["status"] == "complete" else _prog_pct
            _bar_color = {"complete": "#4ade80", "ok": "#2383e2", "short": "#ef4444"}.get(_m["status"], "#9b9b9b")
            _stat_badge_color = {"complete": "#166534", "ok": "#1e3a5f", "short": "#7f1d1d"}.get(_m["status"], "#333")
            _sub_lbl   = f" / {_prname}" if _prname else ""
            st.markdown(f"""
<div style="background:#252525;border:1px solid #383838;border-radius:10px;
            padding:11px 16px 10px;margin-bottom:10px">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
    <span style="font-size:.85rem;font-weight:600;color:#e5e5e5">
      {_bname} &nbsp;·&nbsp; {_scname}{_sub_lbl}
    </span>
    <span style="font-size:.75rem;font-weight:600;color:{_bar_color};
                 background:{_stat_badge_color};border-radius:5px;padding:2px 8px">
      {_stat_label}
    </span>
  </div>
  <div style="display:flex;align-items:center;gap:10px">
    <div style="flex:1;background:#383838;border-radius:20px;height:7px;overflow:hidden">
      <div style="width:{_prog_pct*100:.1f}%;height:100%;
                  background:linear-gradient(90deg,{_bar_color}cc,{_bar_color});
                  border-radius:20px"></div>
    </div>
    <span style="font-size:.78rem;color:#9b9b9b;white-space:nowrap;min-width:160px;text-align:right">
      {_m['shipped_mt']:,.1f} / {_m['qty_mt']:,.1f} MT &nbsp;({_m['fulfill_pct']:.1f}%)
    </span>
  </div>
</div>""", unsafe_allow_html=True)

            with st.expander(
                f"{_ct_cst_ico} **{_bname}**  {_ct.get('product','BP')} / {_scname}"
                + (f" / {_prname}" if _prname else "")
                + f"  |  계약 {_m['qty_mt']:,.1f} MT ±{_ct.get('tolerance_pct',0):.0f}%"
                + f"  |  선적 {_m['shipped_mt']:,.2f} MT ({_m['fulfill_pct']:.1f}%)"
                + f"  |  {_stat_label}  [{_ct_cst_lbl}]",
                expanded=_m["status"] == "short",
            ):
                # 상한 초과 / 하한 미달 경고 (협의 하에 발생 가능 — 저장은 항상 허용, 안내만 표시)
                if _m["max_mt"] > 0 and _m["shipped_mt"] > _m["max_mt"]:
                    st.warning(f"⚠️ 선적량({_m['shipped_mt']:.2f} MT)이 계약 상한({_m['max_mt']:.2f} MT)을 "
                               f"{_m['shipped_mt']-_m['max_mt']:.2f} MT 초과했습니다.")
                elif _m["min_mt"] > 0 and _m["shipped_mt"] > 0 and _m["shipped_mt"] < _m["min_mt"] and _ct_cstatus == "closed":
                    st.warning(f"⚠️ 선적량({_m['shipped_mt']:.2f} MT)이 계약 하한({_m['min_mt']:.2f} MT)에 "
                               f"{_m['min_mt']-_m['shipped_mt']:.2f} MT 미달합니다.")
                if _m.get("oop_alloc_mt", 0) > 0:
                    st.info(f"ℹ️ 계약 기간 밖 선적일의 배분 {_m['oop_alloc_mt']:.2f} MT가 "
                            f"이행량에 포함되어 있습니다 (수동 배분 = 협의 물량으로 간주).")

                _mc1, _mc2, _mc3, _mc4 = st.columns(4)
                _rem_val = f"{_m['remaining_mt']:,.2f} MT" if _m["remaining_mt"] > 0 else "충족"
                _rem_col = "#f87171" if _m["remaining_mt"] > 0 else "#4ade80"
                _avl_col = "#4ade80" if _m["total_avail_mt"] >= _m["remaining_mt"] else "#f87171"
                _avl_sub = f"{_m['total_avail_mt']-_m['remaining_mt']:+.2f} MT 여유" if _m["remaining_mt"] > 0 else ""
                _mc1.markdown(_kpi_card("계약량",          f"{_m['qty_mt']:,.1f} MT",
                                        f"허용 {_m['min_mt']:,.1f}~{_m['max_mt']:,.1f} MT"), unsafe_allow_html=True)
                _mc2.markdown(_kpi_card("선적 완료",       f"{_m['shipped_mt']:,.2f} MT",
                                        f"이행률 {_m['fulfill_pct']:.1f}%"), unsafe_allow_html=True)
                _mc3.markdown(_kpi_card("잔여 의무",       _rem_val, val_color=_rem_col), unsafe_allow_html=True)
                _mc4.markdown(_kpi_card("충당 가능 (BP)",  f"{_m['total_avail_mt']:,.2f} MT",
                                        _avl_sub, val_color=_avl_col), unsafe_allow_html=True)

                _pr_scope = f"임가공사: {_prname}" if _prname else "임가공사: 전체"
                st.caption(
                    f"전환율 {_m['conv_pct']:.0f}% ({_m.get('conv_src','실적')}) 적용  ·  {_pr_scope}  ·  "
                    f"창고 원료 {_m['warehouse_raw_kg']/1000:,.2f} MT → BP {_m['warehouse_bp_mt']:,.2f} MT  ·  "
                    f"임가공사 미처리 {_m['at_proc_raw_kg']/1000:,.2f} MT → BP {_m['at_proc_bp_mt']:,.2f} MT  ·  "
                    f"완제품(미연결 배치) {_m.get('finished_bp_mt',0):,.2f} MT"
                )

                # 가격·정산 조건 표시
                _ct_ni_disp = f"{_ct['ni_payable_pct']:.2f}%" if _ct.get("ni_payable_pct") else "매입사 기본"
                _ct_co_disp = f"{_ct['co_payable_pct']:.2f}%" if _ct.get("co_payable_pct") else "매입사 기본"
                _prov_pct_disp = f"{_ct['prov_pct']:.0f}%" if _ct.get("prov_pct") else "100%"
                _prov_idx_disp_map = {"prov": "가정산월", "loading": "선적월"}
                _final_idx_disp_map = {"final": "확정월", "prov": "가정산월", "loading": "선적월"}
                _prov_idx_d = _prov_idx_disp_map.get(_ct.get("prov_index_basis","prov"), "가정산월")
                _final_idx_d = _final_idx_disp_map.get(_ct.get("final_index_basis","final"), "확정월")
                st.caption(
                    f"💰 Ni 지불율: {_ct_ni_disp}  ·  Co 지불율: {_ct_co_disp}  ·  "
                    f"가정산: {_prov_pct_disp}  ·  Prov INDEX: {_prov_idx_d}  ·  Final INDEX: {_final_idx_d}"
                )
                if _ct.get("notes"):
                    st.caption(f"📝 {_ct['notes']}")

                # 기간 표시
                if _ct.get("start_date") or _ct.get("end_date"):
                    st.caption(f"📅 계약 기간: {_ct.get('start_date','—')} ~ {_ct.get('end_date','—')}")

                # ── 계약 편집 ────────────────────────────────────────────────
                with st.expander("계약 수정", expanded=False):
                    _edf1, _edf2, _edf3 = st.columns(3)
                    _ed_qty  = _edf1.number_input("계약량 (MT)", value=float(_ct.get("contract_qty_mt",0)),
                                                   step=1.0, format="%.1f", key=f"ed_qty_{_ct_id}")
                    _ed_tol  = _edf2.number_input("허용 오차 (%)", value=float(_ct.get("tolerance_pct",5)),
                                                   min_value=0.0, max_value=20.0, step=1.0, format="%.0f",
                                                   key=f"ed_tol_{_ct_id}")
                    _ed_cst  = _edf3.selectbox("계약 상태", _ct_status_opts,
                                                index=_ct_status_opts.index(_ct.get("contract_status","active")),
                                                format_func=lambda s: _ct_status_labels.get(s, s),
                                                key=f"ed_cst_{_ct_id}")
                    _edf4, _edf5 = st.columns(2)
                    _ed_start = _edf4.text_input("계약 시작일", value=_ct.get("start_date",""), key=f"ed_start_{_ct_id}")
                    _ed_end   = _edf5.text_input("계약 종료일", value=_ct.get("end_date",""), key=f"ed_end_{_ct_id}")
                    _edf6, _edf7, _edf8 = st.columns(3)
                    _ed_ni_pay = _edf6.number_input("Ni 지불율 (%)", value=float(_ct.get("ni_payable_pct") or 0),
                                                     min_value=0.0, step=0.1, format="%.2f",
                                                     key=f"ed_ni_{_ct_id}", help="0이면 매입사 기본값")
                    _ed_co_pay = _edf7.number_input("Co 지불율 (%)", value=float(_ct.get("co_payable_pct") or 0),
                                                     min_value=0.0, step=0.1, format="%.2f",
                                                     key=f"ed_co_{_ct_id}", help="0이면 매입사 기본값")
                    _ed_prov_pct = _edf8.number_input("가정산 비율 (%)", value=float(_ct.get("prov_pct") or 100),
                                                       min_value=0.0, step=5.0, format="%.0f",
                                                       key=f"ed_pp_{_ct_id}")
                    _edp1, _edp2 = st.columns(2)
                    # 기존 저장값이 YYYY-MM 고정월이면 "특정월 지정"으로 표시
                    _cur_prov_basis  = _ct.get("prov_index_basis",  "prov")
                    _cur_final_basis = _ct.get("final_index_basis", "final")
                    _prov_is_custom  = _cur_prov_basis  not in _prov_idx_map.values()
                    _final_is_custom = _cur_final_basis not in _final_idx_map.values()
                    _ed_prov_idx = _edp1.selectbox(
                        "Provisional INDEX 기준",
                        list(_prov_idx_map),
                        index=list(_prov_idx_map.keys()).index("특정월 지정") if _prov_is_custom
                              else (list(_prov_idx_map.values()).index(_cur_prov_basis)
                                    if _cur_prov_basis in _prov_idx_map.values() else 0),
                        key=f"ed_pidx_{_ct_id}",
                    )
                    _ed_final_idx = _edp2.selectbox(
                        "Final INDEX 기준",
                        list(_final_idx_map),
                        index=list(_final_idx_map.keys()).index("특정월 지정") if _final_is_custom
                              else (list(_final_idx_map.values()).index(_cur_final_basis)
                                    if _cur_final_basis in _final_idx_map.values() else 0),
                        key=f"ed_fidx_{_ct_id}",
                    )
                    # 특정월 지정 선택 시 월 입력
                    _ed_prov_month_fixed  = ""
                    _ed_final_month_fixed = ""
                    if _prov_idx_map[_ed_prov_idx] == "custom":
                        _ed_prov_month_fixed  = _edp1.text_input("Provisional 기준월 (YYYY-MM)",
                            value=_cur_prov_basis if _prov_is_custom else "",
                            placeholder="예: 2025-03", key=f"ed_prov_fm_{_ct_id}")
                    if _final_idx_map[_ed_final_idx] == "custom":
                        _ed_final_month_fixed = _edp2.text_input("Final 기준월 (YYYY-MM)",
                            value=_cur_final_basis if _final_is_custom else "",
                            placeholder="예: 2025-06", key=f"ed_final_fm_{_ct_id}")
                    _ed_notes = st.text_input("메모", value=_ct.get("notes",""), key=f"ed_notes_{_ct_id}")
                    if st.button("수정 저장", key=f"ed_save_{_ct_id}"):
                        _ed_prov_basis_val  = _ed_prov_month_fixed.strip()  if _prov_idx_map[_ed_prov_idx]  == "custom" else _prov_idx_map[_ed_prov_idx]
                        _ed_final_basis_val = _ed_final_month_fixed.strip() if _final_idx_map[_ed_final_idx] == "custom" else _final_idx_map[_ed_final_idx]
                        if _prov_idx_map[_ed_prov_idx] == "custom" and (not _ed_prov_basis_val or len(_ed_prov_basis_val) != 7):
                            st.error("Provisional 기준월을 YYYY-MM 형식으로 입력하세요.")
                        elif _final_idx_map[_ed_final_idx] == "custom" and (not _ed_final_basis_val or len(_ed_final_basis_val) != 7):
                            st.error("Final 기준월을 YYYY-MM 형식으로 입력하세요.")
                        else:
                            for _c2 in cfg["contracts"]:
                                if _c2.get("id") == _ct_id:
                                    _c2.update({
                                        "contract_qty_mt":   _ed_qty,
                                        "tolerance_pct":     _ed_tol,
                                        "contract_status":   _ed_cst,
                                        "start_date":        _ed_start.strip(),
                                        "end_date":          _ed_end.strip(),
                                        "ni_payable_pct":    _ed_ni_pay   if _ed_ni_pay   > 0 else None,
                                        "co_payable_pct":    _ed_co_pay   if _ed_co_pay   > 0 else None,
                                        "prov_pct":          _ed_prov_pct if _ed_prov_pct != 100.0 else None,
                                        "prov_index_basis":  _ed_prov_basis_val,
                                        "final_index_basis": _ed_final_basis_val,
                                        "notes":             _ed_notes.strip(),
                                    })
                                    break
                            save_cfg(cfg)
                            st.toast("✅ 계약 수정 완료")
                            st.rerun()

                # ── 선적 배분 관리 ──────────────────────────────────────────
                st.divider()
                st.markdown("**📦 선적 배분 (계약별 부분 배정)**")

                _allocs = cfg.setdefault("contract_allocations", [])
                _ct_allocs_cur = [a for a in _allocs if a.get("contract_id") == _ct_id]

                if _ct_allocs_cur:
                    _alloc_rows = []
                    for _a in _ct_allocs_cur:
                        _s = _ship_map_disp.get(_a.get("shipment_id", ""), {})
                        _alloc_rows.append({
                            "HBL": _s.get("hbl","—"),
                            "선적일": _s.get("loading_date", "—"),
                            "배분량 (MT)": round(float(_a.get("allocated_kg") or 0) / 1000, 3),
                            "_alloc_id": _a.get("id", ""),
                        })
                    for _ar in _alloc_rows:
                        _ac1, _ac2, _ac3, _ac4 = st.columns([3, 2, 2, 1])
                        _ac1.write(_ar["HBL"])
                        _ac2.write(_ar["선적일"])
                        _ac3.write(f"{_ar['배분량 (MT)']:,.3f} MT")
                        if _ac4.button("삭제", key=f"alloc_del_{_ar['_alloc_id']}"):
                            cfg["contract_allocations"] = [
                                x for x in _allocs if x.get("id") != _ar["_alloc_id"]
                            ]
                            save_cfg(cfg)
                            st.rerun()
                else:
                    st.caption("배분 기록 없음 — 아래에서 추가하세요.")

                # 배분 추가 폼
                _buyer_ships = [
                    s for s in cfg.get("shipments", [])
                    if s.get("buyer_id") == _ct.get("buyer_id", "")
                ]
                if _buyer_ships:
                    _ship_opts = {
                        f"{s.get('hbl','—')}  ({s.get('loading_date','—')}, {float(s.get('weight_kg') or 0)/1000:,.2f} MT)": s["id"]
                        for s in _buyer_ships if s.get("id")
                    }
                    with st.form(key=f"alloc_form_{_ct_id}"):
                        _fa1, _fa2 = st.columns([4, 2])
                        _sel_ship_label = _fa1.selectbox("선적건 선택", list(_ship_opts), key=f"alloc_ship_{_ct_id}")
                        _alloc_kg_input = _fa2.number_input("배분량 (MT)", min_value=0.0, step=0.001, format="%.3f", key=f"alloc_kg_{_ct_id}")
                        # 선택한 선적건의 기배분/잔여 표시
                        _preview_sid = _ship_opts.get(_sel_ship_label, "")
                        _preview_total = float(next((s.get("weight_kg",0) for s in _buyer_ships if s.get("id")==_preview_sid), 0) or 0)
                        _preview_used  = sum(float(a.get("allocated_kg",0)) for a in _allocs if a.get("shipment_id")==_preview_sid)
                        _preview_rem   = _preview_total - _preview_used
                        st.caption(f"선적 합계 {_preview_total/1000:,.3f} MT  ·  기배분 {_preview_used/1000:,.3f} MT  ·  잔여 **{_preview_rem/1000:,.3f} MT**")
                        _add_alloc = st.form_submit_button("배분 추가")
                    if _add_alloc:
                        _sel_sid   = _preview_sid
                        _remain_kg = _preview_rem
                        # 계약 상한 초과 검증
                        _cur_alloc_mt = sum(
                            float(a.get("allocated_kg",0)) for a in _allocs if a.get("contract_id") == _ct_id
                        ) / 1000
                        _after_mt = _cur_alloc_mt + _alloc_kg_input
                        if _alloc_kg_input <= 0:
                            st.error("배분량은 0보다 커야 합니다.")
                        elif _alloc_kg_input * 1000 > _remain_kg + 0.1:
                            st.error(f"배분량이 잔여량을 초과합니다. 잔여: {_remain_kg/1000:,.3f} MT")
                        else:
                            # 계약 상한 초과 시에도 저장은 허용 (양사 협의 하에 발생 가능) — 초과분은 배너로 안내
                            if _m["max_mt"] > 0 and _after_mt > _m["max_mt"] + 0.001:
                                st.toast(f"⚠️ 배분 후 총량이 계약 상한을 {(_after_mt-_m['max_mt']):.3f} MT 초과합니다 — 저장은 진행됩니다.")
                            _allocs.append({
                                "id":           str(uuid.uuid4())[:8],
                                "contract_id":  _ct_id,
                                "shipment_id":  _sel_sid,
                                "allocated_kg": round(_alloc_kg_input * 1000, 3),
                            })
                            cfg["contract_allocations"] = _allocs
                            save_cfg(cfg)
                            st.rerun()
                else:
                    st.caption("이 매입사의 선적 기록이 없습니다.")

                # 삭제
                with st.popover("계약 삭제"):
                    st.warning(f"**{_bname}** {_ct.get('product','')} {_m['qty_mt']:,.0f} MT 계약을 삭제합니다.")
                    if st.button("확인 삭제", key=f"ct_del_{_ct_id}"):
                        cfg["contracts"] = [c for c in _ct_list if c.get("id") != _ct_id]
                        cfg["contract_allocations"] = [
                            a for a in cfg.get("contract_allocations", []) if a.get("contract_id") != _ct_id
                        ]
                        save_cfg(cfg)
                        st.rerun()

