# claude.ai에서 BP/BM 데이터 질문하기 — 설정 안내

claude.ai(웹·휴대폰 앱)에서 "3분기 매출 얼마야?", "EcoPro 미수 알려줘"처럼 물으면 앱과 같은 숫자로 답하게 하는 설정이다.
조회 서버(`mcp_server.py`)를 Google Cloud Run에 올리고, claude.ai에 커스텀 커넥터로 등록한다. 서버는 데이터를 읽기만 한다.

```
claude.ai ──질문──▶ 조회 서버 (Cloud Run, 구글 로그인 + 허용 이메일만) ──읽기──▶ Drive config.json
```

- Google Cloud 프로젝트: `bp-calculator-498206` (지금 동기화에 쓰는 프로젝트)
- 서비스 계정: `bp-calc-sync@bp-calculator-498206.iam.gserviceaccount.com` (이미 config.json 읽기 권한 있음)
- 처음 한 번만 하면 되고, 이후 GitHub `main`에 푸시하면 서버도 자동으로 다시 배포된다.
- 아래 링크는 모두 이 프로젝트로 열린다. 화면 문구는 Google 쪽 개편에 따라 조금 다를 수 있다.

---

## 1단계. 결제 계정 연결

Cloud Run·Firestore는 무료 사용량이 있지만 결제 계정이 연결돼 있어야 켜진다. 질의 몇 번 수준이면 무료 범위 안으로 예상한다.

1. https://console.cloud.google.com/billing/linkedaccount?project=bp-calculator-498206 열기
2. 결제 계정이 없으면 **결제 계정 연결/만들기** → 카드 등록 → 이 프로젝트에 연결
3. (권장) https://console.cloud.google.com/billing/budgets 에서 예산 알림(예: 월 $5) 만들기 — 과금이 생기면 메일로 알려 준다

## 2단계. API 켜기

아래 네 링크를 차례로 열고 각각 **사용(Enable)** 을 누른다.

- Cloud Run: https://console.cloud.google.com/apis/library/run.googleapis.com?project=bp-calculator-498206
- Cloud Build: https://console.cloud.google.com/apis/library/cloudbuild.googleapis.com?project=bp-calculator-498206
- Artifact Registry: https://console.cloud.google.com/apis/library/artifactregistry.googleapis.com?project=bp-calculator-498206
- Firestore: https://console.cloud.google.com/apis/library/firestore.googleapis.com?project=bp-calculator-498206

## 3단계. Firestore 데이터베이스 만들기 (로그인 상태 저장용)

서버가 쉬다가 다시 켜져도 claude.ai 로그인이 풀리지 않게, 로그인 정보를 암호화해 여기에 저장한다. 업무 데이터는 저장하지 않는다.

1. https://console.cloud.google.com/firestore/databases?project=bp-calculator-498206 열기
2. **데이터베이스 만들기** → ID는 `(default)` 그대로 → 모드 **Native** → 위치 **europe-west1** (목록에 없으면 `eur3`) → 만들기

## 4단계. 서비스 계정에 Firestore 권한 주기

1. https://console.cloud.google.com/iam-admin/iam?project=bp-calculator-498206 열기
2. `bp-calc-sync@...` 줄의 연필(수정) 아이콘 → **다른 역할 추가** → `Cloud Datastore User` 선택 → 저장

## 5단계. Cloud Run에 서버 배포 (GitHub에서 자동 빌드)

1. https://console.cloud.google.com/run?project=bp-calculator-498206 열기 → **저장소 연결(Connect repository)**
2. **Cloud Build** 선택 → **Cloud Build로 설정(Set up with Cloud Build)**
   - 저장소 제공업체: GitHub → 처음이면 **인증(Authenticate)** → GitHub 로그인·앱 설치 승인 → 저장소 `changikc-beep/bpbmbpbm` 선택 → 다음
   - 빌드 구성: 브랜치 `^main$` / 빌드 유형 **Dockerfile** / 소스 위치 `/Dockerfile` → 저장
   - 빌드용 서비스 계정에 권한을 부여하라는 안내가 나오면 **부여(Grant)** 를 누른다
3. 서비스 이름 `bp-mcp`, 리전 **europe-west1**
4. 인증: **공개 액세스 허용(Allow public access)** — claude.ai가 접속해야 하므로 공개로 둔다. 실제 차단은 서버의 구글 로그인 + 허용 이메일이 한다
5. 요금 청구: 요청 기반 / 최소 인스턴스 **0** / 최대 인스턴스 **1**
6. **컨테이너, 볼륨, 네트워킹, 보안** 펼치기
   - 컨테이너 탭: 포트 `8080`, 메모리 **1 GiB**, CPU 1, **시작 CPU 부스트** 켜기
   - 변수 및 보안 비밀 탭 → 변수 추가: `ALLOWED_EMAILS` = `changikc@gmail.com` (claude.ai에 쓰는 구글 계정과 같아야 함. 여러 개면 쉼표로 구분)
   - 보안 탭: 서비스 계정 = `bp-calc-sync@bp-calculator-498206.iam.gserviceaccount.com`
7. **만들기** → 빌드에 5~10분 걸린다. 끝나면 화면 위쪽에 **URL**이 나온다(예: `https://bp-mcp-123456789.europe-west1.run.app`). 이 주소를 메모한다

이 단계에서는 로그인 설정이 아직 없어서, 서버는 떠 있지만 모든 질문을 거부한다(정상).

## 6단계. 구글 로그인(OAuth) 설정

### 6-1. 동의 화면

1. https://console.cloud.google.com/auth/overview?project=bp-calculator-498206 열기 → **시작하기**
2. 앱 이름 `BP MCP`, 지원 이메일 = 본인 → 대상 **외부(External)** → 연락처 이메일 = 본인 → 만들기
3. https://console.cloud.google.com/auth/audience?project=bp-calculator-498206 → 게시 상태 **테스트** 그대로 두고 **테스트 사용자 추가** → 본인 구글 계정 추가
   (테스트 상태에서는 등록한 계정만 로그인할 수 있어 한 번 더 막아 준다)

### 6-2. 로그인 키(클라이언트) 만들기

1. https://console.cloud.google.com/auth/clients?project=bp-calculator-498206 → **클라이언트 만들기**
2. 애플리케이션 유형 **웹 애플리케이션**, 이름 `bp-mcp`
3. **승인된 리디렉션 URI** 추가: `<5단계 URL>/auth/callback`  (예: `https://bp-mcp-123456789.europe-west1.run.app/auth/callback`, 끝에 `/` 없이 정확히)
4. 만들기 → 나오는 **클라이언트 ID**와 **클라이언트 보안 비밀번호(GOCSPX-로 시작)** 를 복사. 보안 비밀번호는 다른 사람·채팅에 공유하지 않는다

### 6-3. 서버에 넣기

1. https://console.cloud.google.com/run?project=bp-calculator-498206 → `bp-mcp` → **새 버전 수정 및 배포**
2. 변수 및 보안 비밀 탭에서 변수 3개 추가 (`ALLOWED_EMAILS`는 그대로 둠)
   - `BASE_URL` = 5단계 URL (끝에 `/` 없이)
   - `GOOGLE_CLIENT_ID` = 6-2의 클라이언트 ID
   - `GOOGLE_CLIENT_SECRET` = 6-2의 보안 비밀번호
3. **배포**

## 7단계. claude.ai에 커넥터 등록

1. https://claude.ai/settings/connectors 열기 → **커스텀 커넥터 추가(Add custom connector)**
2. 이름 `BP/BM 데이터`, URL `<5단계 URL>/mcp` → 추가
3. **연결(Connect)** → 구글 로그인 화면에서 본인 계정 선택 → "확인되지 않은 앱" 경고가 나오면 **계속** (본인이 만든 테스트 앱이라 정상) → 서버의 승인 화면에서 **허용**
4. 새 대화에서 입력창 아래 도구 메뉴에 `BP/BM 데이터`가 켜져 있는지 확인하고 질문: "3분기 요약 알려줘", "POSCO 미수", "TGLHUS26090002 상태"
5. 휴대폰 Claude 앱은 같은 계정이면 따로 설정할 필요 없다

---

## 문제가 생기면

- **"Couldn't reach the MCP server"**: URL 끝이 `/mcp`인지, 6-3의 `BASE_URL`이 5단계 URL과 정확히 같은지 확인
- **로그인 후 "redirect_uri_mismatch"**: 6-2의 리디렉션 URI가 `<URL>/auth/callback`과 한 글자도 다르지 않은지 확인
- **"접근 권한이 없는 계정입니다"**: `ALLOWED_EMAILS`에 로그인한 구글 계정이 들어 있는지 확인
- **데이터 오류**: Cloud Run → `bp-mcp` → 로그 탭의 마지막 오류를 Claude Code에 붙여 주면 원인을 찾는다
- 서버를 끄려면 Cloud Run에서 `bp-mcp` 삭제, claude.ai에서 커넥터 제거

## 사용할 수 있는 질문 (도구)

| 도구 | 내용 |
|---|---|
| summary | 분기 요약(직전 분기 대비), 매입사·스크랩·임가공사별, 정산 상태 |
| todo | 앱 홈의 할 일 |
| receivables | 미수 확정산 잔액, 예상 입금일 |
| shipment | HBL 1건 상세(정산·입금·배치 손익) |
| shipments | 선적 목록(매입사·상태 필터) |
| pnl | 손익 집계(월·분기·매입사·HBL·임가공사·스크랩별) |
| stock | 원료·완제품 재고, 생산·재고 대사 |

자주 묻는데 도구가 없는 질문은 Claude Code에서 `bp_ask.py`에 명령을 추가하면 서버에도 같이 반영된다.
