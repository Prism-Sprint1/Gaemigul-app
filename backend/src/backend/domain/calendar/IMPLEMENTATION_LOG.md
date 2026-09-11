# Calendar 백엔드 1차 구현 정리 (FRED CPI)

CLAUDE.md 요구사항 기준으로 1~4단계(FRED 연동 → FastAPI → Supabase → API 응답)를 CPI 지표 하나로
끝까지 완성한 기록. 개발 순서표 기준 STEP 1~11에 해당.

## 1. 확정된 설계 결정

| 항목                     | 결정                                                                                              |
| ------------------------ | ------------------------------------------------------------------------------------------------- |
| ORM 모델                 | 사용하지 않음. `models/calendar.py`는 비워둠                                                      |
| Supabase 접근 방식       | `core/database.py`의 `async_session`/`get_db()`를 그대로 재사용, `sqlalchemy.text()` 기반 raw SQL |
| 테이블 생성 방식         | 마이그레이션 도구 없이 Supabase SQL Editor에서 수동 실행                                          |
| FRED 수집 트리거         | APScheduler 미사용. `scripts/seed_cpi.py` 수동 실행(1회성 적재)                                   |
| API 엔드포인트           | `GET /calendar/events?year=YYYY&month=MM`                                                         |
| `publishedAt` 의미       | 한국시간(KST) 기준 경제지표 **발표일**. FRED 원본 날짜를 그대로 쓰지 않고 Service에서 변환        |
| `publishedAt` 타입       | `text` 유지 (`'YYYY-MM-DD'` 형식 고정 → 사전순 정렬이 곧 날짜순 정렬)                             |
| `forecast`, `importance` | FRED가 제공하지 않으므로 항상 `null` (임의 생성 금지)                                             |

## 2. Supabase `calendar_events` 테이블 (생성 완료)

```sql
CREATE TABLE calendar_events (
    id            text PRIMARY KEY,
    "publishedAt" text NOT NULL,
    start_date    text,
    end_date      text,
    "time"        text,
    region        text NOT NULL,
    category      text NOT NULL,
    title         text NOT NULL,
    summary       text NOT NULL,
    importance    integer,
    previous      text,
    forecast      text,
    actual        text,
    status        text NOT NULL
);

CREATE INDEX idx_calendar_events_published_at ON calendar_events ("publishedAt");
CREATE INDEX idx_calendar_events_category ON calendar_events (category);
```

- `publishedAt`, `time`은 camelCase라서 모든 SQL에서 반드시 큰따옴표로 감싸야 함(안 그러면 Postgres가 자동 소문자화).
- `id`가 PK라서 `INSERT ... ON CONFLICT (id) DO UPDATE`로 중복 없이 upsert 가능.

## 3. 신규/수정 파일

| 파일                                   | 역할                                                                    |
| -------------------------------------- | ----------------------------------------------------------------------- |
| `core/config.py`                       | `fred_api_key` 필드 추가 (기존 항목 유지)                               |
| `core/fred_client.py` (신규)           | FRED `series/observations`, `series/release`, `release/dates` 호출 전담 |
| `domain/calendar/schemas/calendar.py`  | Pydantic `CalendarEvent` (CLAUDE.md 6번 그대로, 14개 필드)              |
| `domain/calendar/services/calendar.py` | FRED 호출 → KST 변환 → 한국어 title/summary → upsert/조회. ORM 미사용   |
| `domain/calendar/routers/calendar.py`  | `GET /calendar/events?year=&month=`                                     |
| `main.py`                              | `calendar_router` include 한 줄만 추가 (기존 코드 불변)                 |
| `scripts/seed_cpi.py` (신규)           | CPI 1회 적재용 수동 스크립트                                            |

## 4. KST 변환 로직

FRED는 발표 **날짜**만 주고 **시각**은 주지 않는다. BLS(미국 노동통계국)가 CPI를 공식적으로
미국 동부시간 **08:30**에 발표한다는 것은 공개된 고정 스케줄이므로(추정치 아님, `market_hours.py`의
장 운영시간표와 같은 성격), 이 시각을 기준으로 `America/New_York` → `Asia/Seoul`로 실제 timezone
변환을 수행해 `publishedAt`(날짜)과 `time`(시각)을 계산한다. 다른 지표(PPI/GDP/고용/실업률)를
추가할 때는 `services/calendar.py`의 `_RELEASE_TIME_ET` 표에 해당 지표의 공식 발표 시각을 추가하면 됨
(모르는 지표는 표에 없으면 자동으로 `time=null` 처리).

## 5. 검증 결과 (STEP 9~11)

### STEP 9 — `scripts/seed_cpi.py` 실행: 성공

```
저장 완료: fred-CPIAUCSL-2026-07-01 | publishedAt=2026-08-12 time=21:30 | actual=332.813 previous=332.568 status=RELEASED
```

### STEP 10 — 저장 데이터 검증: 성공

DB에 실제로 저장된 row:

| 컬럼                      | 값                         | 비고                                                                                                     |
| ------------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------- |
| `id`                      | `fred-CPIAUCSL-2026-07-01` | `fred-{series_id}-{observation_date}` 규칙                                                               |
| `publishedAt`             | `2026-08-12`               | FRED 실제 release date를 KST로 환산                                                                      |
| `time`                    | `21:30`                    | 08:30 ET(서머타임 EDT, UTC-4) → KST(UTC+9) 변환 결과, 검산 일치                                          |
| `region`                  | `미국`                     |                                                                                                          |
| `category`                | `CPI`                      |                                                                                                          |
| `title`                   | `미국 소비자물가지수(CPI)` | 최초 적재 시점 값. 8번 항목에서 대상 기간 표기를 추가해 현재는 `"미국 소비자물가지수(CPI) - 2026년 7월"` |
| `previous`                | `332.568`                  | FRED 실제 관측값                                                                                         |
| `actual`                  | `332.813`                  | FRED 실제 관측값                                                                                         |
| `importance`              | `null`                     | FRED 미제공                                                                                              |
| `forecast`                | `null`                     | FRED 미제공                                                                                              |
| `start_date` / `end_date` | `null`                     | 보류 규칙                                                                                                |
| `status`                  | `RELEASED`                 | `actual` 존재 → RELEASED                                                                                 |

- **UPSERT 검증**: `seed_cpi.py`를 두 번째 실행해도 같은 `id`라서 row 수는 계속 1개 유지 (중복 적재 없음 확인).

### STEP 11 — API 테스트: 성공

`uvicorn main:app`으로 로컬 서버를 띄워 실제 HTTP 요청 확인 (테스트 후 서버 종료).

**`GET /calendar/events?year=2026&month=9`**

- HTTP 200, `[]` (9월 데이터가 아직 없어서 빈 배열 — 정상)

**`GET /calendar/events?year=2026&month=8`** (실제 데이터가 있는 달, 검증용 추가 호출)

- HTTP 200
- 아래는 이 시점(최초 적재 직후) 스냅샷. title/summary가 대상 기간 없이 저장된 상태이며,
  8번 항목에서 이 문제를 다루고 개선했다.

```json
[
  {
    "id": "fred-CPIAUCSL-2026-07-01",
    "publishedAt": "2026-08-12",
    "start_date": null,
    "end_date": null,
    "time": "21:30",
    "region": "미국",
    "category": "CPI",
    "title": "미국 소비자물가지수(CPI)",
    "summary": "미국 소비자물가지수(CPI)는 미국에서 소비자가 구입하는 상품과 서비스의 가격 변화를 보여주는 대표적인 물가 지표입니다. 물가가 예상보다 높게 나오면 인플레이션 우려가 커지고 미국의 금리 인하 기대가 약해질 수 있어 주식시장에 부담으로 작용할 수 있습니다.",
    "importance": null,
    "previous": "332.568",
    "forecast": null,
    "actual": "332.813",
    "status": "RELEASED"
  }
]
```

## 6. 종합

| 단계                              | 결과 |
| --------------------------------- | ---- |
| STEP 9 (CPI 1회 적재)             | 성공 |
| STEP 10 (저장 데이터/UPSERT 검증) | 성공 |
| STEP 11 (API 실제 호출 테스트)    | 성공 |

## 7. title/summary 대상 기간(대상 월) 표기 추가

**문제**: `title`이 항상 `"미국 소비자물가지수(CPI)"`로 고정이라, 이 발표가 **몇 월 데이터인지**
캘린더 화면에서 알 수 없었다. FRED observation의 `date`(예: `"2026-07-01"`)는 **대상 기간**(그
값이 설명하는 달)이고, `release/dates`가 주는 날짜는 **발표일**(그 값이 공개된 날) — 이 둘은
다른 개념이며, `publishedAt`은 이미 발표일 기준으로 정확히 계산되고 있었다. 다만 대상 기간
정보가 어디에도 노출되지 않는 게 진짜 문제였다.

**검토했던 대안과 결정**:

| 대안                                                           | 채택 여부 | 이유                                                                                                                                                                                              |
| -------------------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `start_date`/`end_date`에 대상 기간(예: 2026-07-01~07-31) 저장 | ❌        | 이 두 컬럼은 CLAUDE.md 10번 항목에서 "여러 날에 걸친 **이벤트**"(FOMC, 컨퍼런스) 용도로 이미 정의됨. "통계가 설명하는 기간"은 다른 개념이라 같은 컬럼에 넣으면 의미가 섞임 → **NULL 유지로 확정** |
| title에 대상 기간을 덧붙임                                     | ✅        | `"미국 소비자물가지수(CPI) - 2026년 7월"`. 컬럼 추가 없이 텍스트만으로 해결                                                                                                                       |
| summary 맨 앞에 대상 기간 안내 문장 추가                       | ✅        | `"2026년 7월 소비자물가지수(CPI) 자료입니다."` + 기존 summary                                                                                                                                     |

**구현 위치**: `services/calendar.py`에 `_PERIOD_LABELS` 표와 `_format_period_kr()` 함수 추가,
`ingest_cpi_from_fred()`에서 title/summary 조합 시 사용. 테이블 스키마, FRED 수집 로직,
`forecast`/`importance`/`actual` 값 생성 로직은 변경하지 않음.

**적용 후 실제 데이터** (재적재해서 확인):

```json
{
  "title": "미국 소비자물가지수(CPI) - 2026년 7월",
  "summary": "2026년 7월 소비자물가지수(CPI) 자료입니다. 미국 소비자물가지수(CPI)는 미국에서 소비자가 구입하는 상품과 서비스의 가격 변화를 보여주는 대표적인 물가 지표입니다. ..."
}
```

## 8. Response 구조 점검 (Next.js 캘린더 연동 기준, PPI 추가 전 예비 점검)

PPI를 추가하기 전에, 현재 `GET /calendar/events` 응답이 프런트 캘린더에서 바로 쓸 수 있는
구조인지 필드별로 점검한 결과.

| 필드                      | 프런트에서의 쓰임                                | 비고                                                                                                           |
| ------------------------- | ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| `publishedAt`             | 캘린더에서 어느 날짜 칸에 이벤트를 배치할지 결정 | `'YYYY-MM-DD'`, 이미 KST 기준                                                                                  |
| `time`                    | 카드 상단 시각 표시 (`"21:30"`)                  | `HH:MM` 24시간제. `null`이면 프런트가 시각 미표기 처리 필요                                                    |
| `title`                   | 카드 제목                                        | 대상 기간 포함(`"... - 2026년 7월"`)이라 좁은 카드에서는 말줄임(ellipsis) 처리 고려 필요 (프런트 UI 판단 영역) |
| `category`                | 색깔별 카테고리 태그                             | 문자열 그대로 매핑 키로 사용 가능                                                                              |
| `region`                  | 국가 배지                                        | 현재 `"미국"` 고정                                                                                             |
| `summary`                 | 카드 본문/상세 설명                              | 대상 기간 안내 문장이 맨 앞에 포함됨                                                                           |
| `actual` / `previous`     | 상세 영역의 "실제값 / 이전값"                    | FRED 실측값, 항상 문자열                                                                                       |
| `forecast` / `importance` | 상세 영역의 "예상값 / 중요도"                    | 현재 항상 `null` → 프런트는 "-"로 표시 (CLAUDE.md 39·47번 원칙)                                                |
| `status`                  | 발표완료(`RELEASED`)/발표예정(`SCHEDULED`) 배지  | `actual` 유무와 사실상 연동되지만 별도 필드로 명시                                                             |
| `start_date` / `end_date` | (현재 미사용)                                    | CPI/PPI 등 단일 발표 지표에는 항상 `null`                                                                      |

**PPI 추가 시 프런트 영향**: 응답은 카테고리와 무관하게 항상 동일한 14필드 flat 구조이므로,
PPI가 추가돼도 배열에 `category: "PPI"` 항목이 하나 늘어날 뿐 JSON 구조 변경은 없음. 프런트는
카테고리별 색상 매핑에 `PPI` 항목만 추가하면 됨. 백엔드도 `services/calendar.py`의
`_TITLES`/`_SUMMARIES`/`_PERIOD_LABELS`/`_RELEASE_TIME_ET` 4개 표에 `"PPI"` 항목만 추가하면
되고, 라우터/스키마/테이블 변경은 불필요.

## 9. Git 브랜치 동기화 (원격 "연습" 커밋과의 충돌 해결)

`back/feat/calendar`에 push가 거부되는 문제가 있었다. 원인은 단순히 "뒤처짐"이 아니라, 원격에
`44acc3c "api연동 및 연습"`이라는 커밋이 로컬 히스토리에 없는 상태에서 정확히 같은 파일
(`main.py`, `routers/calendar.py`, `schemas/calendar.py`, `services/calendar.py`)을 건드려서
히스토리가 갈라져 있었다.

**확인 결과**: 이 커밋은 팀원이 아니라 본인이 다른 세션에서 미리 짜본 연습용 초안이었고, 내용도
대부분 주석 처리된 이전 시도들과 CLAUDE.md 스펙과 다른 구버전 `CalendarEvent` 스키마
(`date`/`country`/`importance: int` 등), CORS·스케줄러 없는 미완성 `main.py`였다.

**해결**: `git pull`로 병합한 뒤, 충돌난 4개 파일은 전부 이번 세션에서 완성한 버전으로 확정
(`git checkout --ours`)하고, 충돌 없이 병합 가능했던 `test_fred.py`(FRED 연결 테스트 스크립트),
`calendarPractice.py`(빈 파일), `.gitignore` 추가 내용은 그대로 살렸다. 병합 커밋을 만들어
push 완료. (`calendarPractice.py`는 이후 정리 과정에서 삭제됨.)

## 10. PPI(PPIACO) 구현

### FRED 데이터 확인 (구현 전 사전 검토)

| 항목 | 값 |
|---|---|
| Series ID | `PPIACO` |
| 지표명 | Producer Price Index by Commodity: All Commodities |
| 주기 | Monthly |
| 단위 | Index 1982=100 (Not Seasonally Adjusted) |
| release_id | 46 ("Producer Price Index", BLS 공식) |
| 2026년 7월 실제 발표일 | `2026-08-13` |

CPI와 동일하게 `series/observations`의 `date`는 대상 기간, `release/dates`의 `date`가 실제
발표일이며, BLS가 CPI와 같은 고정 시각(08:30 ET)에 발표한다는 공개된 사실을 그대로 적용해
KST로 변환했다.

### 구현 방식

`ingest_cpi_from_fred()` 내부 로직을 `_ingest_from_fred(category)` 공통 함수로 일반화하고,
`ingest_cpi_from_fred()` / `ingest_ppi_from_fred()`는 이 공통 함수를 호출하는 얇은 래퍼로
남겨서 기존 호출부(`scripts/seed_cpi.py`)에 영향이 없도록 했다. `_TITLES`, `_SUMMARIES`,
`_PERIOD_LABELS`, `_RELEASE_TIME_ET`, `_SERIES_IDS` 5개 표에 `"PPI"` 항목만 추가.
`scripts/seed_ppi.py`를 신규로 추가(수동 1회 적재, APScheduler 미사용). 테이블 스키마,
`GET /calendar/events` 라우터 구조는 변경하지 않았다.

### 검증 결과

- **PPI 실제 저장 데이터**:
```json
{
  "id": "fred-PPIACO-2026-07-01",
  "publishedAt": "2026-08-13",
  "time": "21:30",
  "region": "미국",
  "category": "PPI",
  "title": "미국 생산자물가지수(PPI) - 2026년 7월",
  "summary": "2026년 7월 생산자물가지수(PPI) 자료입니다. 미국 생산자물가지수(PPI)는 기업이 상품과 서비스를 생산하면서 받는 가격의 변화를 보여주는 지표입니다. 생산 단계의 물가 흐름을 확인할 수 있어 향후 소비자물가와 인플레이션 흐름을 판단할 때 참고합니다.",
  "importance": null,
  "previous": "286.279",
  "forecast": null,
  "actual": "284.057",
  "status": "RELEASED"
}
```
- `publishedAt`/`time`은 FRED의 실제 release date(`2026-08-13`)를 KST로 변환한 값 — 관측일을
  그대로 쓴 게 아님을 확인.
- `actual`/`previous`는 FRED 실측값 그대로, `forecast`/`importance`는 여전히 `null`.
- **CPI 회귀 테스트**: PPI 추가 후 `scripts/seed_cpi.py`를 재실행해도 CPI row(`publishedAt=2026-08-12`, `actual=332.813`)가 이전과 완전히 동일하게 유지됨을 확인.
- **`GET /calendar/events?year=2026&month=8`**: `HTTP 200`, CPI·PPI 두 이벤트가 `publishedAt` 오름차순(08-12, 08-13)으로 한 배열에 정상적으로 반환됨.

## 11. Next.js 연동 준비 단계 — Response 구조 최종 점검 (CPI+PPI)

PPI까지 추가된 상태에서 실제 응답을 다시 점검한 결과 (8번 항목의 예비 점검을 구체화).

- **캘린더 날짜 배치**: `publishedAt`으로 날짜 칸 결정, 칸 안에는 `time`/`category`/`title`로 카드 렌더링. `id`는 리스트 key.
- **클릭 시 상세 정보**: `title`, `summary`, `region`, `category`, `actual`, `previous`, `forecast`, `importance`, `status`, `time`. `start_date`/`end_date`는 항상 `null`이라 다일 이벤트가 생기기 전까지 미사용.
- **필드별 프런트 표시 방법**:
  - `status`: `RELEASED`→"발표완료", `SCHEDULED`→"발표예정" 배지로 프런트가 매핑 (백엔드 값은 영문 유지로 확정)
  - `actual`/`previous`: 값 있으면 그대로, `null`이면 "-"
  - `forecast`/`importance`: **현재 항상 `null`** → 반드시 "-" 또는 미표시 처리 (CLAUDE.md 27·28번, 값이 있는 것처럼 보이는 UI 금지)
- **현재 구조가 Next.js 연동에 충분한가**: 기본 캘린더 표시(날짜 배치, 카드, 상세 패널)에는 충분. 카테고리 추가(PPI)에도 응답 구조가 안 바뀌는 것을 실제로 확인함.
- **프런트에서 추가로 필요할 수 있는 필드 (제안만, 테이블 변경 필요해서 보류)**:
  1. 단위(unit) — CLAUDE.md 39번은 단위 표시를 요구하는데 현재 응답엔 단위 정보가 없음 (FRED는 `units` 메타데이터를 실제로 제공함)
  2. 대상 기간의 구조화된 값 — 지금은 "2026년 7월"이 `title`/`summary` 문자열 안에만 있어서 프런트가 따로 쓰려면 문자열 파싱 필요
  3. 국가 코드 — `region`이 이미 한국어 텍스트(`"미국"`)라 국기 아이콘 매핑 등에 쓰려면 별도 코드가 있으면 편함
- **백엔드 구조에서 향후 검토할 사항 (목록만, 아직 미수정)**:
  1. `main.py`의 CORS `allow_origins`가 `localhost:3000`만 허용 — 프런트 배포 도메인 추가 필요
  2. 단위 정보 부재 (위 1번과 동일 이슈)
  3. `title`/`summary`의 대상 기간이 자유 텍스트로만 존재 — 구조화된 필드 없음

## 12. Next.js 임시 연동 테스트 화면 (`/calendar-api-test`)

프런트엔드 팀의 실제 캘린더 화면(`frontend/app/calendar/page.tsx`, `components/ui/full-calendar.tsx`)은
아직 전달되지 않았지만, 백엔드 API가 정상 동작하는 것을 눈으로 확인하기 위해 완전히 분리된
임시 테스트 화면을 만들었다. **기존 프런트 작업물은 전혀 수정하지 않았다.**

### 사전 분석 결과

| 항목 | 확인 결과 |
|---|---|
| Next.js 프로젝트 경로 | `frontend/` (저장소 최상위, `backend/`와 나란히 위치) |
| package.json | `frontend/package.json` |
| Next.js 버전 | `16.2.6` (React `19.2.4`). `frontend/AGENTS.md`에 "이전에 알던 Next.js와 다르다, 코드 작성 전 번들 문서 확인" 경고 있음 |
| 라우터 방식 | App Router (`frontend/app/`, `pages/` 디렉토리 없음) |
| 기존 캘린더 컴포넌트 | 이미 존재함 — `app/calendar/page.tsx` + `components/ui/full-calendar.tsx` (더미 이벤트로 렌더링 중, 처음 공유된 캡처 화면과 동일). **수정하지 않음** |
| HTTP 클라이언트 | `axios` 미설치 — 네이티브 `fetch` 사용이 프로젝트 관례 |
| 백엔드 주소 | `frontend/.env.example`의 `NEXT_PUBLIC_API_BASE_URL` 기본값이 `8080`으로 이미 지정돼 있어, 이 포트로 통일하기로 확정 |

### 구현

- `frontend/app/calendar-api-test/page.tsx` (신규) — `/calendar-api-test` 라우트. 서버 컴포넌트에서
  `fetch(NEXT_PUBLIC_API_BASE_URL + "/calendar/events?year=&month=")`를 직접 호출해 SSR로 렌더링.
  브라우저 클라이언트 코드가 없어 CORS 영향을 받지 않는다. `?year=&month=` 쿼리로 연/월 변경 가능,
  기본값은 실데이터가 있는 2026년 8월.
- `frontend/.env.local` (신규, `.gitignore`로 커밋 제외) — `NEXT_PUBLIC_API_BASE_URL=http://localhost:8080`
- `npm install`로 `frontend/node_modules` 최초 설치 (이전엔 설치돼 있지 않았음)

### 검증 결과

- `uv run uvicorn main:app --port 8080`(백엔드) + `npm run dev`(프런트, 포트 3000) 동시 기동 후 실제 호출.
- `GET /calendar-api-test?year=2026&month=8` → `HTTP 200`, CPI(`332.813`/`332.568`)·PPI(`284.057`/`286.279`) 카드가 title/summary/시각/상태까지 정상 렌더링됨을 SSR HTML과 Playwright 스크린샷으로 직접 확인.
- `GET /calendar-api-test?year=2026&month=9` → `HTTP 200`, "해당 연/월에는 이벤트가 없습니다" 정상 표시 (빈 배열 케이스).
- 기존 `/calendar` 라우트 → `HTTP 200`, 변경 없이 그대로 동작 확인 (영향 없음 재확인).

### 후속 조정

사용자 요청으로 화면의 "예상값(forecast) / 중요도(importance)" 표시 줄을 주석 처리함 — 두 필드 모두
FRED가 제공하지 않아 항상 `null`이라 테스트 화면에서 굳이 "-"로 노출할 필요가 없다고 판단. 필드
자체(타입 정의)는 남겨두고 화면 출력 JSX만 주석 처리했다. 재검증 결과 "실제값 / 이전값"만 정상
표시됨을 스크린샷으로 재확인.

## 13. 다음 후보

- GDP(`GDP`) → 고용(`PAYEMS`) → 실업률(`UNRATE`) → 금리(`FEDFUNDS`) 순으로 확장
  (각 지표 추가 시 `_TITLES`, `_SUMMARIES`, `_PERIOD_LABELS`, `_RELEASE_TIME_ET`, `_SERIES_IDS`에 항목만 추가하면 되는 구조 — PPI 추가로 검증됨)
- 기본 흐름이 안정된 뒤 APScheduler로 자동 수집 전환 여부 결정
- 11번 항목에서 제안한 unit/대상기간/국가코드 필드를 추가할지 프런트엔드 팀과 논의
- 프런트엔드 팀과 `GET /calendar/events` Response 구조 최종 합의
