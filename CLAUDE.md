# bp_calculator — 프로젝트 지침

EV 배터리 스크랩 → 임가공(톨링) → BP/BM 수출 손익·재고 관리 Streamlit 앱(`app.py`, 단일 파일).
데이터 원본은 Google Drive의 `config.json` 하나이고, **모든 입력은 구글 시트 `bp_calculator_sync` → 앱의 '시트 동기화'로만 들어온다**
(2026-11 결정: 앱 안의 추가·수정·삭제 폼은 모두 제거, 백업 복원만 남김. 선적 정산 상세는 입력칸 없이 읽기 전용 표).
시트 탭: 선적(26열: …계약ID·비고·확정액) / 컨테이너 / 입고 / 출고 / 생산 / 배치 / INDEX(7열 Co Low) / 환율 / 판관비 /
**계약**(시트가 원본, 계약ID 유지, 선적보다 먼저 동기화) / **실사**(월말 재고 실사) /
**셀·모듈**(입출고 원장 사본 → 앱 셀/모듈 창고 재고. 재고 파악용: 입고 단가 0, 출고는 직접판매, 손익 요약에는 안 들어감).
출고 탭 출고유형 '재고조정'(+ 감소 / − 증가)은 입출고 원장의 재고조정 행 — 창고 잔량·FIFO에 반영. 원장(scrapstocks)과 앱 창고 재고는 2026-11-05 기준 일치시킴.
INDEX 탭 3열(Co Mid)을 비우고 7열(Co Low)만 넣은 행도 받는다(기존 Co 유지, 없으면 Co Low로 대체). Co Low 값은 단가 계산기 Artifact DB `indexes`에서 옮겨 적는다.
입금 추적(입금 기록 입력·할 일·마감 점검)은 하지 않는다(2026-11 결정).
환율: 시트 환율 탭에 없는 월은 동기화 때 Frankfurter(ECB) 월말 환율로 자동 채움(src='auto', 시트 값 우선).
'확정액 재계산 필요'는 선적에 확정 분석값(매입사 Ni·Co)이 있을 때만 비교한다(`_has_final_assay`) — 없으면 시트 확정액이 기준.
기초재고 탭은 삭제(2026-11-06) — 기초재고는 config에 이미 있고, 바꿀 때만 같은 이름·열(스크랩유형/기준일/수량/단가/톤백)로 탭을 다시 만들면 동기화가 읽는다.
정산 INDEX 기본: Ni = LME, Co = 매입 Mid · 매각 Low(계약 'Co 기준'). 계약의 함유량·입금 조건이 매입사 기본값보다 우선(`_with_contract`).
매입사, 스크랩 유형, 견적 비교 화면과 견적 탭 동기화는 삭제(2026-11-27, 매입사/스크랩 데이터는 정산 계산에 쓰여 유지). 직접 판매 화면은 숨김(?page=pnl&sub=직접 판매).
선적 정산 상세는 읽기 전용 표(입력칸 없음). 원료단가는 FIFO 고정(이동평균은 보조, 수동 기본값 없음).
동기화: 저장 전 쓰지 않는 키(forwarders, sk_prices, freight, rfqs)를 지우고, 전후 점검 결과를 config sync_log(최근 100건)에 남긴다(동기화/백업 화면 '동기화 이력').
입력 점검 _data_quality(입고 단가 없음, 입출고 중복 의심, 직접판매 단가 없음, TBD 임시 HBL 14일 경과)가 할 일과 동기화 결과에 같이 나온다.
홈 3번째 줄은 업계 동향(Google News RSS 검색, 제목/출처/날짜/링크만, 6시간 캐시, 검색어는 app.py `_NEWS_TABS`) | 메탈 INDEX(`index_history` 최근 10개월).
미수 현금 전망 카드는 홈에서 뺐고(2026-11-27), 계산(`_receivable_rows`)은 KPI 미수금과 엑셀 보고서가 계속 쓴다. 매입사별 매출은 홈 1줄 카드. 이전 카드형 홈(`?v=1`)은 삭제.

## 메일 → 시트 입력 (tools/)

- `tools/mail_ingest.py`: 다우오피스 IMAP(`imap.daouoffice.com:993`) 읽기 전용 접속. 자격 증명은 Windows 자격 증명 관리자 `daou-imap`
  (사용자가 `cmdkey /generic:daou-imap /user:<메일 주소> /pass`로 등록). 첨부는 메모리에서만 연다(디스크 저장 시 문서 보안 프로그램이 암호화).
- `tools/ingest.py all|inout|tolling|tgl|szamla [--write]`: 기본은 미리보기. `--write`는 입출고(입고/출고 탭 새 행)와 생산(성일 월 합계)만 쓴다.
  TGL 리포트와 szamla는 보고만 한다(HBL 키 교체는 세 탭을 같이 바꿔야 하고, ETD/ETA는 MSC 기준이 우선).
- 월 입고 단가는 `tools/prices.json`('스크랩/출발지' 키). 같은 메일을 다시 돌려도 이미 있는 행은 건너뛴다(날짜+중량, SZ Form/서류번호로 대조).

## 데이터 질문에 답하는 법

사용자가 수치·상태를 물으면(예: "3분기 매출", "EcoPro 미수", "26090002 정산 상태", "BM 재고") 추정하지 말고
`bp_ask.py`로 실데이터를 읽어 답한다. 앱과 같은 계산 함수를 쓰므로 숫자가 앱 화면과 일치한다.

```
python bp_ask.py summary [2026Q3] [--buyer EcoPro] [--product BP|BM]   # 분기 KPI(직전 분기 대비) + 매입사·스크랩·임가공사·정산 상태
python bp_ask.py todo                                                  # 홈의 '할 일'과 동일
python bp_ask.py ar [--buyer POSCO]                                    # 미수 확정산 잔액·예상 입금일
python bp_ask.py ship <HBL>                                            # 선적 1건: 정산·입금·배치 손익
python bp_ask.py ships [--buyer ...] [--status provisional|final|paid]
python bp_ask.py pnl --by month|quarter|buyer|hbl|processor|scrap [--year 2026] [--buyer ...] [--product ...]
python bp_ask.py stock                                                 # 원료·완제품 재고, 생산·재고 대사
python bp_ask.py feed                                                  # 단가 계산기 Artifact용 JSON(재고·EUR/USD·반기 마진), 커넥터 calculator_feed
python bp_ask.py tolling [--year 2026]                                 # 임가공비 분석 JSON(임가공사×제품 손익·투입kg, 재고, 월별 생산 보고), 커넥터 tolling
```

- 출력 첫 줄의 `rev`·저장 시각을 답에 함께 밝힌다(데이터 기준 시점).
- 스크립트에 없는 질문은 `tests/regression_live.py`의 `load_live()`와 `R.F["함수명"]`(app.py 헬퍼)로 짧게 계산한다.
  새로 자주 쓰일 질문이면 `bp_ask.py`에 명령을 추가한다. 계산식을 이 스크립트에 따로 만들지 않는다.
- 읽기 전용이다. Drive `config.json`에 직접 쓰지 않는다. 수정은 사용자가 시트나 앱에서 한다.
- 같은 질의를 claude.ai 커스텀 커넥터로도 쓴다: `mcp_server.py`(FastMCP, Google 로그인 + `ALLOWED_EMAILS`)가
  `bp_ask.ask()`를 도구로 노출하고, `Dockerfile`로 Cloud Run(`bp-mcp`, europe-west1)에 GitHub `main` 푸시마다 자동 배포된다.
  설정 절차는 `MCP_SETUP.md`. 도구를 추가할 때는 `bp_ask.py`에 명령을 만들고 `mcp_server.py`에 얇은 래퍼만 단다.
  로컬 확인: `BP_MCP_LOCAL=1`(로그인 없이 127.0.0.1에서만 뜸).

## 용어와 계산 기준

- 매출 = 선적 확정액(`final_amount_usd`), 없으면 가정산 Invoice, 여기에 기타 조정(`other_adj_usd`)을 더한 값.
  한 HBL에 배치가 여럿이면 생산량 비율로 나눈다. NAV(Számla)에 보고되는 확정산 금액과 같은 기준.
- 실질 손익 = 매출 − 원료비(FIFO 우선) − 임가공비(순) − 수출비 − 보관비. 판관비는 제외.
- 배치(`processing_history`) = (HBL, 임가공사, 스크랩 유형)별 투입·생산. 투입이 비면 임가공사 생산 보고의 회수율, 그다음 계약 전환율로 역산.
- 상태: provisional(가정산) → final(확정산) → paid(입금완료). payable %는 매입사 INDEX 행 값이 계약값보다 우선.
- 완제품 재고 = 임가공사 생산 보고 누계 − HBL에 연결된 배치 생산. 시간은 한국 시간(`_now()`, `_today()`).

## 코드 작업 규칙

- 앱 헬퍼는 `# ── Sidebar ─` 표지 위에 둔다. `tests/smoke_test.py`가 그 구간을 잘라 실행하고, `bp_ask.py`도 거기서 함수를 가져온다.
- 수정 후 `python tests/smoke_test.py`, 계산식을 건드렸으면 `python tests/regression_live.py`까지 통과시킨다.
- 이 폴더의 `requirements.txt`·`runtime.txt`는 문서 보안 프로그램이 암호화·삭제한다. 로컬에서 편집하거나 `git add`하지 않는다.
  커밋은 파일을 지정해서 add 한다(`git add -A` 금지).
- 배포: `git push origin main` 후 `git push public main:main`(readonly 앱). 둘 다 비공개 저장소.
- 파이썬은 3.12로 실행한다: `py -V:3.12 ...` 또는 `C:\Users\KH\AppData\Local\Python\pythoncore-3.12-64\python.exe`.
  PC 기본 파이썬(3.15)에는 pandas, streamlit 등이 없다(2026-11-23 확인). Streamlit은 `>=1.56,<1.57` 고정(1.57+는 위젯 DOM이 바뀌어 CSS가 안 맞음).
- 화면 테스트는 `streamlit.testing.v1.AppTest`로 모든 하위 화면을 돌려 예외 0건을 확인한다. 스모크 테스트는 헬퍼 구간만 실행해서
  홈 화면 본문의 NameError 같은 오류를 못 잡는다(2026-11-23 `_more` 변수 이름 충돌 사례).

## 화면 디자인 규칙

- 테마: 밝은 테마 A(Ice Blue / Graphite / Flame Orange) + 배색 B(2026-11-27). 값은 `.streamlit/config.toml`과 app.py 상단 CSS에 하드코딩돼 있어,
  색을 바꿀 때는 둘을 함께 고친다. 표면 3단계: 바탕 #E4EBF1(CSS로만 덮어씀, config의 backgroundColor #EEF4F8은 데이터 표 셀과 입력칸 색이라 유지)
  / 카드 #FFFFFF(테두리 없이 옅은 그림자) / 카드 안 표와 타일 #F3F6F9, 표 머리글과 소계 띠 #E9EFF4.
  사이드바 그래파이트 #22272D(글자 #AEB8C2, 선택 칩 #353C44, 로고 주황), 본문 #22272D, 제목 #3A4048, 보조 글자 #5E6670.
- 밀도(2026-11-27): 홈은 HTML 한 장(CSS grid, `.h2-*`, 기본 13px, 간격 8px)으로 그리고 계산은 기존 함수를 쓴다. 이전 카드형 홈은 `?v=1`.
  나머지 화면은 CSS 끝의 "Dense system" 블록(블록 간격 8px, 카드 10x12px, 제목 13px, KPI 띠 라벨 11.5px/값 21px)이 일괄 적용된다.
  새 화면 요소를 만들 때 이 단위를 따른다. 글자는 11px 미만으로 내리지 않는다.
- 반응형: 홈 격자는 `.h2` 컨테이너 쿼리(1180/980/940/620/520px), 나머지는 본문 컨테이너(`main`) 900px 이하에서
  KPI 띠 2칸, 카드 나란한 줄은 세로 쌓기, 패널 안 입력칸 2칸. 사이드바는 `initial_sidebar_state="auto"`(휴대폰에서 접힘).
  확인 폭: 1600, 1061(앱 내장 브라우저), 768, 375px.
- 손익 단계표(손익계산서, kg당 단가 분해, HBL 손익 분해)는 `_pl_table_html`/`_pk_table_html`로 그린다(차감 행 "−", 소계 회색 띠, 최종 주황 띠).
  Styler로 배경을 칠할 때 흰 글자를 쓰지 않는다(옅은 배경 위 흰 글자는 읽히지 않음).
- 색 역할: 본계열(매출 막대와 선) 스틸 #9AA8B6 / 강조, 총계, 실질 손익 선 주황 #F26B1D(채움 전용, 글자와 링크는 #B84A0C) /
  양수/완료 틸 #2A9D8F(글자 #0F766E) / 음수 #E0524A(글자 #B42318) / 대기/주의 황토 #D4A72C(글자 #A16207).
  주황 채움 위 글자는 흰색이 아니라 #22272D(흰색은 대비 3:1 미만).
- 화면 문구에 가운뎃점(·)을 쓰지 않는다. 구분은 쉼표, 단어 묶음은 "/"(예: "선적/계약"). 문구는 짧게 "~함"/명사형.
  예외: 시트 탭 이름 `셀·모듈`(실제 구글 시트 탭명)과 시트 데이터의 구분자 " · "(셀·모듈 탭 내역 칸 "모니퍼 1항차 · MONIFER")는
  동기화가 그대로 읽으므로 코드에서 바꾸지 않는다.

## 시트 입력 관례

- 한 HBL에 Invoice(컨테이너)가 여러 건 묶이면 선적 행을 합치지 않고 키를 `HBL`, `HBL-1`, … 로 나눈다(예: TGLHUS26090002 / -1).
  합치면 중량이 달라 동기화가 기존 건을 못 찾아 새 선적을 만들고, 배치가 연결된 기존 건은 지워지지 않아 이중 계상된다.
  HBL 확정 전 임시 키 `TBD-<Invoice 끝번호>`에서 바꿀 때는 선적, 배치, 컨테이너 세 탭의 키를 한 번에 바꾼다(동기화가 선적일+매입사+중량으로 찾아 이름만 바꿈).
- 수출비(TGL szamla): net EUR(VAT 27% 제외) ÷ HBL의 컨테이너 수 × 발행일 ECB EUR/USD.
