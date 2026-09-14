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

| 항목                   | 값                                                 |
| ---------------------- | -------------------------------------------------- |
| Series ID              | `PPIACO`                                           |
| 지표명                 | Producer Price Index by Commodity: All Commodities |
| 주기                   | Monthly                                            |
| 단위                   | Index 1982=100 (Not Seasonally Adjusted)           |
| release_id             | 46 ("Producer Price Index", BLS 공식)              |
| 2026년 7월 실제 발표일 | `2026-08-13`                                       |

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

| 항목                  | 확인 결과                                                                                                                                            |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Next.js 프로젝트 경로 | `frontend/` (저장소 최상위, `backend/`와 나란히 위치)                                                                                                |
| package.json          | `frontend/package.json`                                                                                                                              |
| Next.js 버전          | `16.2.6` (React `19.2.4`). `frontend/AGENTS.md`에 "이전에 알던 Next.js와 다르다, 코드 작성 전 번들 문서 확인" 경고 있음                              |
| 라우터 방식           | App Router (`frontend/app/`, `pages/` 디렉토리 없음)                                                                                                 |
| 기존 캘린더 컴포넌트  | 이미 존재함 — `app/calendar/page.tsx` + `components/ui/full-calendar.tsx` (더미 이벤트로 렌더링 중, 처음 공유된 캡처 화면과 동일). **수정하지 않음** |
| HTTP 클라이언트       | `axios` 미설치 — 네이티브 `fetch` 사용이 프로젝트 관례                                                                                               |
| 백엔드 주소           | `frontend/.env.example`의 `NEXT_PUBLIC_API_BASE_URL` 기본값이 `8080`으로 이미 지정돼 있어, 이 포트로 통일하기로 확정                                 |

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

## 13. 실제 프런트엔드 Calendar 연동 분석 (front/feat/calendar 병합 후)

프런트 팀의 실제 캘린더 화면(`front/feat/calendar` 브랜치 병합분)이 들어온 뒤, 백엔드
`GET /calendar/events`와 실제로 연결 가능한지 코드 기준으로 분석한 기록. **분석만 진행, 코드는
수정하지 않음.**

### 프런트 Calendar 관련 실제 파일

| 파일                                             | 역할                                                                          |
| ------------------------------------------------ | ----------------------------------------------------------------------------- |
| `frontend/app/(main)/calendar/page.tsx`          | 페이지 엔트리                                                                 |
| `frontend/app/(main)/calendar/calendar-view.tsx` | 메인 컴포넌트(월/주 뷰, 필터, 미니캘린더)                                     |
| `frontend/app/(main)/calendar/news-data.ts`      | **타입 정의 + mock 데이터** (`NewsItem`, `Category`, `MarketHoliday`, `NEWS`) |
| `frontend/app/(main)/calendar/news-panel.tsx`    | 날짜 클릭 상세 팝업                                                           |
| `frontend/lib/api/indicator.ts`                  | (타임라인 도메인) 실제 axios API 연동 선례                                    |
| `frontend/components/ui/full-calendar.tsx`       | 더 이상 안 쓰는 예전 더미 캘린더 잔재                                         |

### 프런트 `NewsItem` 타입 (실제 요구 데이터 구조)

```ts
type NewsItem = {
  id: string;
  title: string;
  summary: string;
  category: "macro" | "rate" | "dividend" | "earnings" | "optionExpiry"; // 5종 고정
  region: string; // 국가/기업명 겸용
  publishedAt: Date; // 날짜+시간 통합 (백엔드는 publishedAt/time 분리)
  highlight?: "special";
  replay?: boolean;
  url?: string;
  detail?: {
    forecast?: string;
    previous?: string;
    source?: string;
    sectors?: string[];
  };
};
```

`news-data.ts` 상단에 `/* 뉴스 데이터 — TODO: API 연동 시 NEWS 배열만 교체 */` 주석이 이미
있어, 프런트 팀이 이 지점을 연동 지점으로 스스로 열어둔 상태.

### 백엔드 ↔ 프런트 필드 비교

| 백엔드 필드                        | 프런트 대응                          | 상태                                                                                        |
| ---------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------- |
| `id`                               | `id`                                 | 이름 동일, 값 형식만 다름(문제 없음)                                                        |
| `publishedAt`(날짜) + `time`(시각) | `publishedAt`(날짜+시각 통합 `Date`) | 합쳐서 변환 필요                                                                            |
| `start_date`/`end_date`            | 없음                                 | 다일 이벤트 개념 자체가 프런트에 없음                                                       |
| `region`                           | `region`                             | 호환                                                                                        |
| `category`(지표 코드: `CPI`/`PPI`) | `category`(5종 그룹)                 | **값 불일치, 매핑표 필요** (`CPI`/`PPI`/`GDP`/`UNRATE`/`PAYEMS`→`macro`, `FEDFUNDS`→`rate`) |
| `title`/`summary`                  | `title`/`summary`                    | 호환                                                                                        |
| `importance`                       | 없음                                 | 항상 null이라 당장 문제 없음                                                                |
| `previous`/`forecast`              | `detail.previous`/`detail.forecast`  | 이름은 다르지만(중첩 구조) 매핑 가능                                                        |
| **`actual`**                       | **없음**                             | **UI에 실제값을 보여줄 자리가 아예 없음 — 가장 중요한 격차**                                |
| **`status`**                       | **없음**                             | RELEASED/SCHEDULED 구분 UI 없음                                                             |

### 발견된 주요 문제

1. 날짜/시간 구조 불일치 (분리 vs 통합)
2. `category` 값 완전 불일치 → 매핑표 필요
3. `actual`/`status`를 보여줄 화면 요소가 프런트에 없음 (프런트 팀과 별도 협의 필요)
4. timezone 처리 코드 없음 — 프런트는 "브라우저 로컬시간 = KST"라는 암묵적 가정에 의존 (date-fns만 사용, UTC/timezone 변환 로직 없음)
5. **환경변수 불일치**: `frontend/.env.local`이 `8080`인데, `.env.example`과 `lib/api/indicator.ts`의 실제 기본값은 `8000`으로 이미 바뀌어 있음 — 나중에 `8000`으로 통일 필요
6. HTTP 클라이언트는 fetch가 아니라 **axios**가 실제 팀 컨벤션(`indicator.ts` 기준, 이제 `package.json`에도 설치돼 있음)

### 현재 API 연결 상태

**mock 데이터만 사용 중.** `calendar-view.tsx`가 `news-data.ts`의 `NEWS` 정적 배열을 그대로 씀.
fetch/axios 호출 0건(grep 확인). Supabase 직접 호출도 프로젝트 전체에 0건.

### 연결 가능 여부 판단: **B. 간단한 데이터 매핑 후 연결 가능**

필드명이 상당수 동일(`id`/`region`/`title`/`summary`)하고 나머지도 이름만 바꾸거나 합치는
수준이라, 백엔드 스키마나 프런트 컴포넌트 구조를 바꿀 정도의 근본적 불일치는 없음. **백엔드는
지금 구조를 그대로 유지**하는 것으로 결론.

### 나중에 필요한 최소 수정사항 (아직 미적용)

- `news-data.ts`의 `NEWS` 상수를 "백엔드 응답 → `NewsItem[]` 변환 함수" 호출 결과로 교체
- `lib/api/calendar.ts` 신규 추가 (`indicator.ts`와 동일한 axios 패턴으로 `GET /calendar/events` 호출)
- `frontend/.env.local`을 `8000`으로 통일
- `calendar-view.tsx`/`news-panel.tsx`는 둘 다 `NEWS`라는 이름의 배열만 소비하므로, 위 두 파일만 추가/교체하면 **컴포넌트는 한 줄도 안 건드리고 연결 가능**
- `actual`/`status` 노출 여부는 프런트 팀과 UI 설계 협의 필요

### 전체 데이터 흐름 현황

| 단계                                                       | 상태                                                           |
| ---------------------------------------------------------- | -------------------------------------------------------------- |
| FRED → FastAPI Service → Supabase → `GET /calendar/events` | ✅ 완료                                                        |
| Next.js (axios 연동)                                       | 🟡 부분완료 — timeline 도메인만 연동, calendar 도메인은 미연동 |
| Calendar UI                                                | ❌ 미구현 — 100% mock 데이터                                   |

`Supabase → Next.js` 직접 연결은 없음(확인 완료, 목표 아키텍처 위반 없음).

## 14. 전체 카테고리 체계 재설계 (5개 대분류 확정 + 전체 이벤트 유형 매핑)

`category` 컬럼을 지표별 코드(`CPI`/`PPI`/...)가 아니라, 캘린더 색상 구분용 **5개 대분류
고정값**으로만 쓰기로 확정. 프런트 `NewsItem.category`(13번 항목에서 확인한 5종)와 정확히
동일한 값을 백엔드도 그대로 저장하는 방향.

```python
Literal["macro", "rate", "dividend", "earnings", "optionExpiry"]
```

### 전체 이벤트 유형 → category 매핑

| 지역        | 이벤트                                                | category       | 소스 상태                                                                                                   |
| ----------- | ----------------------------------------------------- | -------------- | ----------------------------------------------------------------------------------------------------------- |
| 미국        | FOMC(회의/결정)                                       | `macro`        | ❓ 미정 — Federal Reserve 공식 캘린더 필요(FRED/KIS 둘 다 없음)                                             |
| 미국        | CPI                                                   | `macro`        | ✅ FRED, 구현 완료                                                                                          |
| 미국        | PPI                                                   | `macro`        | ✅ FRED, 구현 완료                                                                                          |
| 미국        | GDP                                                   | `macro`        | ✅ FRED, series_id `GDP` (다음 후보)                                                                        |
| 미국        | 고용지표(UNRATE/PAYEMS)                               | `macro`        | ✅ FRED (다음 후보)                                                                                         |
| 미국        | 기준금리(FEDFUNDS)                                    | `rate`         | ✅ FRED, series_id `FEDFUNDS` (다음 후보) — FOMC 회의 일정과는 다른 데이터(41번/CLAUDE.md 원문 경고 재확인) |
| 미국        | 증시 휴장일                                           | `macro`        | ❓ 미정 — FRED·KIS 둘 다 미국 시장 휴장일 데이터 없음(KIS `chk-holiday`는 한국 KRX 전용)                    |
| 미국        | 주요 기업 실적 발표(NVIDIA/Apple/MS/Oracle 등)        | `earnings`     | ❓ 미정 — KIS `estimate-perform`은 발표일 아님(기존 조사 결론 유지), 기업 IR 캘린더 등 별도 소스 필요       |
| 미국        | 선물 만기/옵션 만기/동시만기/월물옵션                 | `optionExpiry` | 🔧 API 없음, **규칙 계산으로 해결 가능**(예: 매월 세번째 금요일 등 고정 규칙)                               |
| 미국        | 기업/시장 이벤트(신제품 발표·GTC·CES·Investor Day 등) | `macro`        | ❓ 미정 — 뉴스/보도자료성 데이터, 정형화된 API 없음                                                         |
| 한국        | 기준금리                                              | `rate`         | ❓ 미정 — 한국은행 API/공지 필요                                                                            |
| 한국        | 주요 기업 실적 발표(삼성전자/SK하이닉스 등)           | `earnings`     | ❓ 미정 — DART 등 필요(KIS로는 발표일 확인 불가, 기존 조사 결론 유지)                                       |
| 한국        | 주요 금융 뉴스 / 정책·관세 뉴스                       | `macro`        | ❓ 미정 — 뉴스 API 필요                                                                                     |
| 한국        | 증시 휴장일                                           | `macro`        | ✅ KIS `chk-holiday`, 라이브 테스트 완료                                                                    |
| 한국        | 옵션 만기/선물 만기/동시만기                          | `optionExpiry` | 🔧 API 없음, 규칙 계산으로 해결 가능                                                                        |
| 한국        | 합병/분할                                             | `macro`        | ✅ KIS `ksdinfo/merger-split`, 라이브 테스트 완료                                                           |
| (지역 무관) | 배당                                                  | `dividend`     | ✅ KIS `ksdinfo/dividend`, 라이브 테스트 완료. 실데이터 없으면 임의 생성 안 함(원칙 유지)                   |

### ⚠️ 지난 KIS 설계안과 달라진 점 (재확인 필요)

10번 항목(KIS 설계)에서는 `IPO`, `MERGER_SPLIT`, `SHAREHOLDER_MEETING`을 **각각 별도
category 값**으로 제안했었다. 이번 5개 고정 category 체계에서는:

- **합병/분할**은 `macro`로 재배정됨(사용자 지시 목록에 명시)
- **공모주청약(IPO)**은 이번 전체 이벤트 목록에 아예 등장하지 않음 — "기업/시장 이벤트" 하위 예시로만 존재했던 원래 항목이라 `macro`에 포함되는 것으로 추정되나, 명시적 확인 필요
- **주주총회일정**도 이번 두 차례 지시 어디에도 등장하지 않음 — 계속 확장 대상에 포함할지, 이번 범위에서 제외할지 확인 필요

### Supabase 테이블 구조 변경 필요 여부 — 결론: **컬럼 추가 불필요**

현재 14개 컬럼만으로 위 표의 모든 이벤트 유형을 구조적으로 담을 수 있다고 판단한다. 근거:

| 컬럼                                        | 위 모든 유형에 왜 충분한가                                                                                                                                                                                                                                                         |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `region`                                    | **국가명만 사용**(`"미국"`/`"한국"`). 기업명은 `region`에 넣지 않고 `title`에 포함시킨다 — 예: `title="삼성전자 2026년 3분기 실적 발표"`, `region="한국"`. (13번 항목에서 확인한 프런트의 "국가/기업명 겸용" 방식과는 다른 선택 — 프런트 연동 매핑 단계에서 이 차이를 흡수해야 함) |
| `start_date`/`end_date`                     | FOMC 2일 회의, 합병/분할의 매매정지~신주상장 구간 등 다일 이벤트에 사용(원래 이 두 컬럼의 설계 목적)                                                                                                                                                                               |
| `previous`/`actual`/`forecast`/`importance` | 값이 있는 유형(지표, 기준금리, 배당금 등)엔 채우고, 없는 유형(휴장일, 만기일, 뉴스)엔 전부 `null` 유지 — 임의 생성 금지 원칙 그대로                                                                                                                                                |
| `title`/`summary`                           | 어떤 지표/이벤트인지 구체적으로 구분하는 역할을 전담(카테고리가 더 이상 이 역할을 안 하므로 더 중요해짐)                                                                                                                                                                           |

**대신 필요한 변경 2가지** (컬럼 추가 아님):

1. `category`에 5개 값만 허용하는 제약(Pydantic `Literal`, 필요하면 Postgres `CHECK` 제약)
2. **코드 내부 리팩터링**: 지난 턴(카테고리 이슈 발견)에서 확인한 대로, `services/calendar.py`의 `category`가 지금 "저장값"과 "내부 조회 키(indicator)"를 겸하고 있어서, 이 둘을 분리해야 함 — `indicator`("CPI"/"PPI"/"KR_HOLIDAY" 등, 코드 내부에서만 쓰는 세부 식별자) → `category`(5개 값, DB 저장용) 매핑표를 추가하는 구조로.

### 소스별 `id` 접두사 규칙 제안 (여러 API가 같은 테이블을 공유하므로)

| 소스                      | 접두사 예시                                                           |
| ------------------------- | --------------------------------------------------------------------- |
| FRED                      | `fred-{series_id}-{observation_date}` (기존 그대로)                   |
| KIS                       | `kis-{세부유형}-{종목코드 또는 all}-{날짜}` (10번 항목에서 이미 제안) |
| 규칙 계산(만기일 등)      | `rule-{세부유형}-{날짜}` (신규 제안)                                  |
| 향후 뉴스/IR 등 미정 소스 | 소스가 정해지면 그때 접두사 확정                                      |

서로 다른 접두사를 쓰는 한, 같은 `calendar_events` 테이블을 계속 공유해도 `id` 충돌 위험은 없다.

## 15. category → macro 통일 구현 + CPI/PPI 2026년 1~12월 일괄 수집

14번 항목에서 설계한 내용을 실제로 구현하고 실행한 기록.

### category 리팩터링 (indicator ≠ category 분리)

기존엔 `services/calendar.py`의 `category` 변수가 "DB에 저장할 값"과 "FRED series/제목/
발표시각을 찾는 내부 조회 키" 두 역할을 동시에 하고 있었다(13~14번 항목에서 발견한 문제). 아래처럼
분리했다.

```python
_SERIES_IDS  = {"CPI": "CPIAUCSL", "PPI": "PPIACO"}   # 내부 조회 키(indicator)는 그대로
_CATEGORY_OF = {"CPI": "macro", "PPI": "macro"}        # 신규: indicator -> 저장할 category
```

`_ingest_from_fred()`의 파라미터명도 `category` → `indicator`로 바꾸고, DB에는
`category=_CATEGORY_OF[indicator]`(즉 `"macro"`)를 저장하도록 수정. `scripts/seed_cpi.py`,
`scripts/seed_ppi.py`는 코드 변경 없이 그대로 이 새 로직을 타게 됨.

기존에 이미 저장돼 있던 2건(`fred-CPIAUCSL-2026-07-01`, `fred-PPIACO-2026-07-01`)의 `category`도
Supabase에서 직접 `"CPI"`/`"PPI"` → `"macro"`로 UPDATE(삭제 아님, 값만 변경)해서 앞으로의
데이터와 일관되게 맞춰뒀다.

### `core/fred_client.py` 확장 (기존 호출 방식엔 영향 없음, 파라미터 추가만)

- `get_series_observations()`: `observation_start`/`observation_end` 옵션 추가 → 특정 기간
  전체 관측치를 한 번에 조회 가능
- `get_release_dates()`: `realtime_start`/`realtime_end`/`include_release_dates_with_no_data`
  옵션 추가 → 이 마지막 옵션이 `True`여야 **아직 지나지 않은 미래 예정 발표일**까지 나온다
  (기본값 `False`일 땐 이미 지나간 발표일만 나옴 — 실제 라이브 호출로 확인한 FRED 자체 규칙)

### 연간 일괄 수집 함수: `ingest_year_from_fred(indicator, year)`

동작 방식:

1. 전년 12월분까지 포함해서 그 해 전체 관측치를 한 번에 조회(1월의 `previous` 계산용)
2. 그 해 전체 발표일(예정 포함)을 한 번에 조회 — PPI처럼 월 12개보다 발표일이 더 많이 나오는
   경우(특이 발표일)가 있어서, "각 관측월의 다음 달 1일 이후 최초로 오는 발표일"을 그 달의
   실제 발표일로 매칭하는 규칙을 사용(실제 데이터로 정확성 검증 완료)
3. 그 발표일에 대응하는 실제 관측값이 FRED에 있으면 `RELEASED`+실제값, 없으면(아직 발표 안 됨)
   `SCHEDULED`+`actual=null`
4. 예정 발표일 자체가 FRED 캘린더에 없는 달은 **아무것도 만들지 않고 건너뜀**(임의 날짜 생성 금지
   원칙)
5. `previous`는 RELEASED/SCHEDULED 관계없이, 그 시점까지 실제로 존재하는 가장 최근 관측값을 사용

`scripts/seed_2026_calendar.py`(신규)로 CPI/PPI 각각 이 함수를 호출.

### 실행 결과

```
CPI 2026년: 11건 upsert (1~11월)
PPI 2026년: 11건 upsert (1~11월)
```

**12월이 빠진 이유**: 12월분 발표는 보통 다음 해 1월에 나오는데, 조회 범위(2027년 2월까지)를
넉넉히 잡았는데도 FRED가 그 발표일을 아직 공개하지 않은 상태였다. 규칙대로 만들지 않고 건너뜀
— 의도한 동작.

### Supabase 최종 상태 (검증 완료)

- 전체 22건(CPI 11 + PPI 11), **전부 `category="macro"`**
- RELEASED 16건(1~8월, 실제 FRED 값), SCHEDULED 6건(9~11월, `actual=null`이지만 `previous`는
  최근 실측값으로 채워짐)
- `GET /calendar/events?year=2026&month=1~12`를 전부 실제 호출해서 월별 분포 확인(2월~12월
  각 2건씩 정상 반환. 1월만 0건이라 처음엔 버그로 의심했으나, **16번 항목에서 원인이 밝혀짐 —
  버그 아님**: `fred-CPIAUCSL-2026-01-01`(관측월은 1월)의 실제 `publishedAt`은 `2026-02-13`
  (발표는 다음 달에 되므로). 즉 "관측월이 1월인 이벤트"는 있어도 "1월에 실제로 발표되는
  이벤트"는 이번에 채운 범위(2026년 관측치만) 안에서는 존재하지 않는 게 정상 — 2025년 12월분
  데이터가 있었다면 그게 2026년 1월에 발표됐을 것

### Git 동기화

- 위 작업을 커밋(`d9fdee4`)한 뒤, 새로 올라온 `front/feat/calendar`(캘린더 UI 개선,
  `calendar-view.tsx`/`full-calendar.tsx` 등 7개 프런트 파일)를 병합 — 백엔드 파일과 전혀
  안 겹쳐서 충돌 없이 완료. 아직 원격에는 push하지 않은 상태.

## 16. GDP(분기별 지표) 추가 — CPI/PPI(월별)와 다른 처리 필요성 발견

GDP는 FRED에서 `frequency: "Quarterly"`로 확인됨. CPI/PPI와 같은 로직(1~12월 반복)을 그대로
쓰면 분기가 아닌 달에도 억지로 이벤트를 만들려고 시도하게 되므로(원래 CLAUDE.md가 경고했던
"GDP 월별 12개 임의 생성 금지"), 아래처럼 분리했다.

```python
_FREQUENCY = {"GDP": "quarterly"}  # 표에 없으면 monthly로 취급(CPI/PPI는 그대로)
```

`ingest_year_from_fred()`가 이 표를 보고 분기별이면 대상 기간을 1/4/7/10월만 순회하고,
`_format_period_kr()`도 지표를 보고 "2026년 9월" 대신 "2026년 3분기" 형태로 만든다.

### ⚠️ 실제 라이브 검증으로 발견한 중요한 문제와 해결

GDP는 분기당 발표가 **3번**(속보치→잠정치→확정치, BEA 관행) 있어서, "다음 분기 1일 이후
최초로 오는 release date"라는 기존 매칭 규칙(CPI/PPI에서는 잘 맞았음)을 그대로 쓰면 틀릴 수
있음을 실제로 확인했다.

- 2026년 1분기(Q1) GDP의 실제 최초 발표일을 FRED의 실시간(vintage) 데이터로 직접 검증한 결과
  **`2026-04-30`**이었는데, 단순 "다음 분기 시작 이후 최초 발표일" 규칙으로는 그 사이에 낀
  다른 발표일(`2026-04-09`, 아마도 직전 분기 확정치/연간 개정 관련)을 잘못 골랐을 것.
- **해결**: 실제 값이 존재하는(RELEASED) 기간에 한해, 후보 발표일들을 하나씩
  `realtime_start`/`realtime_end`로 고정해서 "그 시점 스냅샷에 이 관측값이 실제로 있는지"를
  라이브로 검증하고, 처음으로 값이 나타나는 날짜를 진짜 발표일로 채택하도록
  `ingest_year_from_fred()`를 수정. 아직 발표 안 된(SCHEDULED) 기간은 검증할 실제 값이
  없으므로 후보 중 가장 이른 날짜(=속보치 예정일)를 그대로 사용.
- 이 수정 덕분에 `core/fred_client.py`의 `get_series_observations()`에도 `realtime_start`/
  `realtime_end` 파라미터를 추가했다(기존 호출 방식에는 영향 없음).

### 실행 결과

```
GDP 2026년: 3건 upsert (1~3분기)
  fred-GDP-2026-01-01 | publishedAt=2026-04-30 | actual=31865.721 | status=RELEASED
  fred-GDP-2026-04-01 | publishedAt=2026-07-30 | actual=32486.066 | status=RELEASED
  fred-GDP-2026-07-01 | publishedAt=2026-10-29 | actual=None      | status=SCHEDULED
```

`publishedAt=2026-04-30`이 앞서 vintage 데이터로 직접 검증한 값과 정확히 일치함을 확인.
4분기는 발표일이 FRED에 아직 없어서(12월 케이스와 같은 이유) 생성되지 않음 — 의도한 동작.

`GET /calendar/events?year=2026&month=4` 실제 호출로 CPI(3월분)·PPI(3월분)·GDP(1분기)가 한
배열에 정상적으로 같이 나오는 것도 확인. `title`이 `"미국 국내총생산(GDP) - 2026년 1분기"`로
분기 표기가 정확히 적용됨.

### Supabase 최종 상태

전체 25건(CPI 11 + PPI 11 + GDP 3), 전부 `category="macro"`.

## 17. PAYEMS(비농업 고용) 추가

CPI/PPI와 동일한 월별·발표 1회 패턴인지 먼저 라이브로 확인: FRED `frequency: "Monthly"`,
release_id=50("Employment Situation", BLS), 2026년 발표일이 정확히 12개(월 1개씩, GDP 같은
특이 케이스 없음)로 확인됨 — 그대로 기존 `_ingest_from_fred`/`ingest_year_from_fred` 구조에
값만 추가.

```python
_RELEASE_TIME_ET["PAYEMS"] = dt_time(8, 30)   # BLS, CPI/PPI와 동일 기관·시각
_TITLES["PAYEMS"]          = "미국 비농업 고용(Nonfarm Payrolls)"
_PERIOD_LABELS["PAYEMS"]   = "비농업 고용"
_SERIES_IDS["PAYEMS"]      = "PAYEMS"
_CATEGORY_OF["PAYEMS"]     = "macro"
```

참고: release_id=50은 UNRATE(실업률)와 같은 "Employment Situation" 보고서를 공유한다 — 나중에
UNRATE 추가할 때 release_id 조회 결과가 PAYEMS와 같아도 정상이다.

### 실행 결과

```
PAYEMS 2026년: 11건 upsert (1~11월, 12월은 CPI/PPI와 같은 이유로 보류)
  fred-PAYEMS-2026-01-01 | publishedAt=2026-02-11 | actual=158592 previous=158432 status=RELEASED
  ...
  fred-PAYEMS-2026-08-01 | publishedAt=2026-09-04 | actual=159075 previous=158913 status=RELEASED
  fred-PAYEMS-2026-09-01 | publishedAt=2026-10-02 | actual=None   previous=159075 status=SCHEDULED
```

### Supabase 최종 상태

전체 36건(CPI 11 + PPI 11 + GDP 3 + PAYEMS 11), 전부 `category="macro"`.

## 18. UNRATE(실업률) 추가 + FEDFUNDS(연방기금금리) 보류 결정

### UNRATE

사전 확인 결과 PAYEMS와 완전히 같은 패턴(release_id=50 "Employment Situation" 공유, 월별 12개
발표일). 바로 표에 값만 추가.

```python
_RELEASE_TIME_ET["UNRATE"] = dt_time(8, 30)   # PAYEMS와 같은 보고서, 같은 기관·시각
_TITLES["UNRATE"]          = "미국 실업률"
_PERIOD_LABELS["UNRATE"]   = "실업률"
_SERIES_IDS["UNRATE"]      = "UNRATE"
_CATEGORY_OF["UNRATE"]     = "macro"
```

실행 결과: **11건 upsert(1~11월)**, publishedAt이 PAYEMS와 완전히 동일한 날짜로 확인됨(같은
보고서라 당연함). 참고로 2025-10분 관측치가 FRED에서 `"."`(값 없음)로 왔는데, 이번에 채운
2026년 범위의 `previous` 계산엔 영향 없음(2026년 1월의 previous는 2025년 12월 실측값을
정상적으로 사용함, 영향받는 건 2025년 11월분 계산이라 이번 범위 밖).

**Supabase 최종 상태**: 전체 47건(CPI 11 + PPI 11 + GDP 3 + PAYEMS 11 + UNRATE 11), 전부
`category="macro"`.

### FEDFUNDS — 이번 확장에서 제외 (사용자 결정, 추후 별도 논의)

실제 조회해본 결과 다른 5개 지표와 근본적으로 성격이 다름을 발견해서 구현 전에 확인받음.

- release_id=18 **"H.15 Selected Interest Rates"**(연준 자체 발표, BLS/BEA 아님)
- 월 1회가 아니라 **거의 매 영업일 발행**됨(2026년 1~3월만 조회해도 61건)
- 지금까지 쓴 "다음 달 1일 이후 최초 발표일 = 그 달의 발표일" 매칭 규칙을 그대로 적용하면
  "그 달의 첫 영업일"이 기계적으로 골라질 뿐, CPI처럼 "시장이 그 순간 처음 그 숫자를 알게 된
  날"이라는 의미가 없음
- 원래 CLAUDE.md의 "FEDFUNDS는 FOMC 회의 일정이 아니다" 경고와 같은 맥락 — FEDFUNDS를 CPI류의
  "발표 이벤트"로 다루는 것 자체가 애매함

**결정: 이번 확장 대상에서 제외, 추후 별도 논의.** `scripts/seed_2026_calendar.py`에도 포함하지
않았고 주석으로 제외 이유를 남겨둠. `_TITLES` 등 표에도 아직 추가 안 함.

## 19. 프런트엔드 `/calendar` 화면에 실데이터 임시 반영 (테스트 목적)

화면에 실제로 어떻게 뿌려지는지 눈으로 확인하기 위해, `frontend/app/(main)/calendar/news-data.ts`의
더미 `NEWS` 배열을 Supabase `calendar_events`의 실제 47건으로 교체했다. **사용자 확인 후 진행**
— 프런트는 다른 팀원이 계속 작업 중이라 원래는 건드리지 않기로 했던 파일이라, 진행 전 범위를
명확히 확인받았다(구조는 유지, 데이터 내용만 교체, `back/feat/calendar`에 올리는 것도 괜찮다는
확인).

### 변경 범위

- **바꾼 것**: `NEWS` 배열의 내용물만. Supabase 47건(CPI 11 + PPI 11 + GDP 3 + PAYEMS 11 +
  UNRATE 11)을 `NewsItem[]` 형태로 변환해서 그대로 채워 넣음.
- **안 바꾼 것**: `Category`/`NewsItem`/`MarketHoliday` 타입, `CAT`/`CATEGORY_GROUPS` 정의,
  `scopeOf`/`countryCodeOf` 함수, `MARKET_HOLIDAYS` 더미 데이터, `calendar-view.tsx`,
  `news-panel.tsx` — 컴포넌트/구조는 전혀 건드리지 않음.

### 변환 규칙 (백엔드 `CalendarEvent` → 프런트 `NewsItem`)

| 백엔드 필드                            | 처리                                                                                                        |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `publishedAt` + `time`                 | `new Date("YYYY-MM-DDTHH:mm:00")`로 합침(13번 항목에서 설계한 방식)                                         |
| `category`                             | 이미 전부 `"macro"`로 저장돼 있어서 값 그대로 사용(15번 항목의 category 리팩터링 덕분에 별도 매핑표 불필요) |
| `region`                               | 그대로 사용(끝에 공백이 붙어있던 CPI 1건은 `.strip()`으로 정리, DB 값 자체는 안 건드림)                     |
| `title`, `summary`                     | 그대로 사용                                                                                                 |
| `previous`                             | 값이 있을 때만 `detail.previous`로                                                                          |
| `forecast`                             | 전부 null이라 `detail.forecast` 자체를 만들지 않음(빈 키 생성 안 함)                                        |
| `actual`, `status`                     | **대응 필드가 프런트에 없어서 반영 못 함** — 13번 항목에서 이미 확인한 한계 그대로                          |
| `importance`, `start_date`, `end_date` | 전부 null/미사용이라 반영 대상 없음                                                                         |

### 진행 상태

파일 교체까지 완료. 사용자가 "문서로만 알려달라"고 해서 **개발 서버 실행/스크린샷/커밋·push는
하지 않고 여기서 멈춤.** 다음 확인이 필요하면:

```
frontend/ 에서 npm run dev 실행 후 /calendar 접속
```

## 20. 주식 초보자에게 필요한 FRED 일정 후보 정리

"FRED에서 주식 시작하는 사람이 알아야 할 일정 중 필요한 것"을 정리해달라는 요청으로, 후보
시리즈들을 실제로 FRED에 존재하는지 하나씩 라이브로 확인했다. 순수 조사/문서 작업이며 코드는
건드리지 않았다.

### 이미 구현됨

| Series ID  | 지표                | 이유                                                          |
| ---------- | ------------------- | ------------------------------------------------------------- |
| `CPIAUCSL` | 소비자물가지수(CPI) | 인플레이션의 대표 지표, 금리 방향을 가늠하는 가장 중요한 숫자 |
| `PPIACO`   | 생산자물가지수(PPI) | CPI보다 하루 먼저 나오는 물가 선행지표                        |
| `GDP`      | 국내총생산(GDP)     | 경제가 성장하는지 축소하는지 보여주는 가장 큰 그림            |
| `UNRATE`   | 실업률              | 고용시장 체력, 연준 금리 결정의 핵심 근거                     |
| `PAYEMS`   | 비농업 고용         | 매달 가장 시장이 크게 반응하는 지표 중 하나(첫째 주 금요일)   |

### 실제 FRED에 존재함 — 추가 후보 (라이브로 확인 완료)

| Series ID            | 지표                         | 주기                  | 초보자에게 중요한 이유                                                                                                     |
| -------------------- | ---------------------------- | --------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `PCEPI` / `PCEPILFE` | PCE 물가지수(근원 포함)      | 월별                  | **연준이 금리 결정 시 CPI보다 더 공식적으로 참고하는 물가 지표.** "연준이 진짜로 보는 물가"라고 소개하기 좋음              |
| `ICSA`               | 신규 실업수당 청구건수       | **주별**(매주 목요일) | 매주 나오는 몇 안 되는 지표라 고용시장 변화를 가장 빨리 감지할 수 있음. 초보자에게 "매주 확인하는 습관"을 들이기 좋은 지표 |
| `UMCSENT`            | 미시간대 소비자심리지수      | 월별                  | 소비자들이 경기를 어떻게 느끼는지 보여줌. 미국 경제의 약 70%가 소비이므로 중요                                             |
| `MICH`               | 미시간대 기대인플레이션율    | 월별                  | "사람들이 앞으로 물가가 오를 거라 믿는지" — 실제 인플레이션에 선행하는 심리 지표                                           |
| `RSAFS`              | 소매판매                     | 월별                  | 소비 동향을 직접 보여주는 지표, 경기소비재·유통주와 관련                                                                   |
| `INDPRO`             | 산업생산지수                 | 월별                  | 제조업 경기 판단 지표                                                                                                      |
| `HOUST`              | 신규 주택착공건수            | 월별                  | 부동산·건설 경기 판단, 금리 민감 업종과 직결                                                                               |
| `CSUSHPINSA`         | S&P/케이스-실러 주택가격지수 | 월별                  | 집값 흐름 — 가계 자산과 소비 여력에 영향                                                                                   |

### FRED에서 구할 수 없음 (확인됨)

| 항목           | 확인 결과                                                                                                                                                                                               |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ISM 제조업 PMI | `series_id=NAPM` 조회 시 **400 오류** — ISM 데이터는 라이선스 문제로 FRED가 직접 제공하지 않음. 프런트 더미 데이터에 "ISM 제조업지수"가 있었는데, FRED로는 구현 불가 — 별도 소스(ISM 직접 구독 등) 필요 |

### 존재는 하지만 "발표 이벤트"로 쓰기엔 부적합함 (FEDFUNDS와 같은 문제)

| Series ID  | 지표                   | 문제                                                                 |
| ---------- | ---------------------- | -------------------------------------------------------------------- |
| `DGS10`    | 미국 10년물 국채금리   | **매 영업일** 발행 — FEDFUNDS처럼 "이 날 발표됐다"는 이벤트성이 없음 |
| `T10Y2Y`   | 10년-2년 금리 스프레드 | 위와 동일(매 영업일)                                                 |
| `DTWEXBGS` | 달러인덱스             | 위와 동일(매 영업일)                                                 |

이 3개는 18번 항목의 FEDFUNDS 결론과 같은 이유로, 캘린더 "이벤트"보다는 종목 상세 페이지 등의
**배경 참고 데이터(차트용)**로 쓰는 게 더 맞아 보인다.

### 제안 우선순위 (다음에 추가한다면)

1. **`ICSA`(신규 실업수당 청구)** — 주별이라 "매주 확인" 습관을 들이기 좋고, 구현 난이도도 월별
   지표와 동일(release_id만 다름)
2. **`PCEPI`/`PCEPILFE`** — CPI 다음으로 시장이 가장 신경 쓰는 물가 지표. CLAUDE.md 원래
   대상엔 없었지만 "연준이 보는 물가"라는 설명으로 초보자 교육 가치가 큼
3. `UMCSENT`/`MICH`, `RSAFS`, `INDPRO`, `HOUST`, `CSUSHPINSA` — 나머지는 우선순위 낮게 순차
   확장

## 21. PCE(개인소비지출 물가지수) 추가

20번 항목에서 조사한 후보 중 우선순위 2위(연준이 CPI보다 공식적으로 더 참고하는 물가 지표)를
바로 구현. series_id `PCEPI`, release_id=54("Personal Income and Outlays", BEA).

### 사전 확인 — GDP와 발표 캘린더를 공유함

PCEPI의 2026년 release/dates가 **GDP(release_id=53)의 날짜와 완전히 동일**함을 확인했다
(1/22, 2/20, 3/13, 4/9, 4/30, ... 전부 일치). BEA가 GDP와 PCE를 같은 날 같이 발표하기 때문.
GDP처럼 한 기간에 여러 후보 발표일이 섞여 있는 구조라, 16번 항목에서 만든 "실측 검증"(candidate
발표일들을 realtime으로 고정해서 실제로 값이 등장하는 첫 날짜를 찾는 로직)이 정확히 필요한
케이스였다 — 별도 코드 추가 없이 `ingest_year_from_fred()`가 기존 로직 그대로 처리함.

```python
_RELEASE_TIME_ET["PCE"] = dt_time(8, 30)   # BEA, GDP와 같은 기관·시각
_TITLES["PCE"]          = "미국 개인소비지출 물가지수(PCE)"
_PERIOD_LABELS["PCE"]   = "개인소비지출(PCE) 물가지수"
_SERIES_IDS["PCE"]      = "PCEPI"
_CATEGORY_OF["PCE"]     = "macro"
```

### 실행 결과 — 실측 검증이 실제로 후보를 정정한 사례

```
PCE 2026년: 11건 upsert (1~11월)
  fred-PCEPI-2026-01-01 | publishedAt=2026-03-13 | actual=129.023 previous=128.576 status=RELEASED
  ...
  fred-PCEPI-2026-07-01 | publishedAt=2026-08-26 | actual=131.659 previous=131.454 status=RELEASED
  fred-PCEPI-2026-08-01 | publishedAt=2026-09-30 | actual=None   previous=131.659 status=SCHEDULED
```

1월분 데이터의 경우, "다음 달 1일 이후 최초 후보"만 썼다면 `2026-02-20`이 골라졌을 텐데(그 날짜엔
아직 1월분 PCE 값이 없음, GDP 쪽 특이일로 추정), 실측 검증이 실제로 값이 등장하는 `2026-03-13`을
정확히 찾아냄. GDP 때 만든 로직이 다른 지표에서도 그대로 유효함을 재확인.

### Supabase 최종 상태

전체 58건(CPI 11 + PPI 11 + GDP 3 + PAYEMS 11 + UNRATE 11 + PCE 11), 전부 `category="macro"`.

## 22. 한국투자증권(KIS) API에서 가져올 수 있는 일정 정리 (종합)

지금까지 여러 턴에 걸쳐 조사·라이브 검증한 KIS 일정 관련 API를 한 곳에 모아 정리. **순수
문서 작업이며 코드는 건드리지 않았다.** 전부 실제 계정으로 라이브 호출해서 확인한 내용이다
(core/kis_client.py의 `get_access_token()` 재사용, 새 토큰 발급 없이 캐시 재사용).

### 사용 가능함 (실제 라이브 호출로 확인 완료)

| #   | 일정                  | endpoint                                                  | TR_ID           | 5개 category 중                                                          | 실데이터 예시(핵심 필드만)                                                                                      |
| --- | --------------------- | --------------------------------------------------------- | --------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| 1   | 한국 증시 휴장일      | `GET /uapi/domestic-stock/v1/quotations/chk-holiday`      | `CTCA0903R`     | `macro`                                                                  | `{bass_dt, opnd_yn}` — 개장일 여부만 있음, 날짜만 있고 시각 없음                                                |
| 2   | 배당일정              | `GET /uapi/domestic-stock/v1/ksdinfo/dividend`            | `HHKDB669102C0` | `dividend`                                                               | `{record_date, sht_cd, isin_name, divi_kind, per_sto_divi_amt, divi_rate, divi_pay_dt}`                         |
| 3   | 합병/분할일정         | `GET /uapi/domestic-stock/v1/ksdinfo/merger-split`        | `HHKDB669104C0` | `macro`                                                                  | `{record_date, sht_cd, cust_nm, merge_type, merge_rate, td_stop_dt, list_dt}`                                   |
| 4   | 주주총회일정          | `GET /uapi/domestic-stock/v1/ksdinfo/sharehld-meet`       | `HHKDB669111C0` | **미정** (5개 중 마땅한 값 없음, earnings에 가깝다는 의견 있으나 미확정) | `{record_date, sht_cd, isin_name, gen_meet_dt, gen_meet_type, agenda}`                                          |
| 5   | 공모주청약일정(IPO)   | `GET /uapi/domestic-stock/v1/ksdinfo/pub-offer`           | `HHKDB669108C0` | **미정** (5개 중 마땅한 값 없음)                                         | `{record_date, sht_cd, isin_name, fix_subscr_pri, subscr_dt("시작~종료" 문자열), pay_dt, list_dt, lead_mgr}`    |
| 6   | 국내주식 종목추정실적 | `GET /uapi/domestic-stock/v1/quotations/estimate-perform` | `HHKST668300C0` | **캘린더 부적합**                                                        | 날짜(이벤트 시점) 자체가 없는 "현재 시점 추정치" 데이터라 애초에 calendar_events에 안 맞음(10번 항목 결론 유지) |

⚠️ **1번(휴장일)은 KIS 공식 주석에 "하루 1회 이하로 호출" 제한이 명시돼 있음** — 자동 수집 시 반드시 캐싱 필요.

### KIS에 없는 것 (확인됨)

| 항목                                                      | 결과                                                                                                                                                                                          |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 한국 선물 만기 / 한국 옵션 만기 / 한국 옵션·선물 동시만기 | 전용 API 없음(공식 저장소 전수 검색 결과 없음). 보통 "매월 둘째 주 목요일" 같은 고정 규칙 계산으로 해결 가능(20번 항목의 FEDFUNDS/DGS10과 비슷하게, API가 아니라 규칙으로 풀어야 하는 케이스) |
| 삼성전자/SK하이닉스 등 기업 실적 **발표일**               | `estimate-perform`은 추정치 API일 뿐 발표일 필드가 없음 — DART 등 별도 소스 필요(이전 조사 결론 유지)                                                                                         |
| 한국 기준금리(한국은행 금통위 결정)                       | **KIS 안에서 전용 API를 아직 찾아보지 않음** — 확인 필요 항목으로 남겨둠(임의로 "없다"고 단정하지 않음)                                                                                       |
| 주요 금융 뉴스 / 정책·관세 뉴스                           | KIS는 증권 시세·공시 데이터 API라 뉴스 API 자체가 없음                                                                                                                                        |

### 구현 시 참고할 것 (이미 정해진 원칙 재확인)

- **ORM 미사용**: 지금까지와 동일하게 `services/calendar.py`가 raw SQL로 직접 upsert
- **id 접두사**: `kis-{세부유형}-{종목코드 또는 all}-{날짜}` (9번 항목에서 이미 제안, fred- 접두사와 충돌 없음)
- **category**: 위 표처럼 5개 중 5번(휴장일)과 4번(합병/분할)은 이미 확정(`macro`), 2번(배당)도
  확정(`dividend`). 주주총회·IPO 2개만 아직 미정 — 실제 KIS 데이터 연동 코드를 작성하는 시점에
  다시 확인하기로 함(사용자 확인: "지금은 안 중요, KIS 연동할 때 다시 물어봐라")
- **날짜/시간**: 전부 날짜만 있고 시각 정보가 없음 → `time`은 항상 `null` (임의 생성 금지 원칙 그대로 적용)
- **previous/actual/forecast**: FRED 지표들과 달리 이 KIS 일정들은 "수치 발표" 개념이 아니라
  "이벤트 발생" 개념에 가까움(예: 주주총회가 "열린다"는 사실 자체가 중요, 숫자 비교가 핵심이
  아님) → 대부분 previous/actual/forecast는 null로 두고 summary 텍스트로 내용 전달하는 게 맞을
  가능성이 높음(배당만 예외로 실제 배당금액을 actual에 넣는 안이 있었음, 10번 항목 참고)

## 23. KIS 배당일정 구현 — 첫 번째 KIS 연동 (`category="dividend"`)

지금까지는 설계·조사만 했던 KIS 연동을 실제로 구현. 전체 종목 조회는 페이지당 100건 제한이 있어서
(22번 항목에서 확인), 주요 국내 기업 29개로 범위를 좁혀 종목코드 지정 조회 방식으로 구현했다.

### 신규/수정 파일

| 파일                                   | 내용                                                                                                                                                  |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `core/kis_client.py`                   | `get_dividend_schedule(f_dt, t_dt, sht_cd, gb1)` 추가(기존 함수 3개는 그대로)                                                                         |
| `services/calendar.py`                 | `_clean_kis_value`/`_clean_kis_date`(KIS 전용 빈값 정리), `_dividend_event_from_kis`(변환), `ingest_dividends_from_kis(stock_codes, f_dt, t_dt)` 추가 |
| `scripts/seed_kis_dividends.py` (신규) | 시가총액 상위 위주 코스피 29개 종목 리스트 + 실행 스크립트                                                                                            |

### 변환 규칙 (KIS 레코드 → CalendarEvent)

| 필드                               | 값                                                                                                                |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `id`                               | `kis-dividend-{종목코드}-{record_date}` (fred- 접두사와 충돌 없음)                                                |
| `publishedAt`                      | `record_date`(배당기준일, "YYYYMMDD"→"YYYY-MM-DD")                                                                |
| `time`                             | 항상 `null` (KIS에 시각 정보 없음)                                                                                |
| `region`                           | `"한국"` 고정, 회사명은 `title`에 (9/14 결정 사항 그대로 적용)                                                    |
| `category`                         | `"dividend"`                                                                                                      |
| `title`                            | `"{종목명} 배당기준일({배당구분})"`                                                                               |
| `summary`                          | 배당금액이 있으면 "주당 N원 배당 예정", 없으면 "배당금액은 아직 확정되지 않았습니다" + 지급예정일(있으면)         |
| `actual`                           | `per_sto_divi_amt`(주당배당금), 미확정이면 `null`                                                                 |
| `previous`/`forecast`/`importance` | 항상 `null` (해당 개념 없음)                                                                                      |
| `status`                           | `publishedAt`이 오늘(KST) 이후면 `SCHEDULED`, 지났으면 `RELEASED` (22번 항목에서 제안한 날짜 기반 규칙 최초 적용) |

**`divi_rate`는 의도적으로 안 씀** — 실제 라이브 데이터로 확인해보니 이 필드가 시가 기준이 아니라
**액면가 대비 배당률**이었다(삼성전자: 주당 374원 / 액면가 100원 = "374.00%"로 표시됨). 초보자가
보면 "배당율 374%"로 오해할 수 있어서, 주식 초보자 혼동 방지 원칙(CLAUDE.md 47번)에 따라
summary에서 제외하고 실제 배당금액(원)만 보여주기로 판단.

### 실행 결과

```
=== KIS 배당일정 29개 종목 조회, 42건 upsert ===
  kis-dividend-005930-20260630 | actual=374  status=RELEASED | 삼성전자 배당기준일(분기)
  ...
  kis-dividend-055550-20261103 | actual=None status=SCHEDULED | 신한금융지주회사 배당기준일(분기)
```

29개 종목 중 8개(삼성바이오로직스, 셀트리온, 한화에어로스페이스, 삼성물산, 메리츠금융지주,
SK이노베이션, 삼성생명, 한국전력)는 2026년 기준 배당 레코드가 0건으로 조회됨(KIS에 해당 데이터가
없다는 뜻 — 임의로 채우지 않음).

`GET /calendar/events?year=2026&month=8` 실제 호출로 macro(FRED)와 dividend(KIS) 데이터가 한
응답 배열에 정상적으로 섞여서 나오는 것 확인 완료.

### 참고 — 회사명 표기

KIS `isin_name`은 정식 등기명이라 일반적으로 알려진 종목명과 다를 수 있다(예: "SK하이닉스"가
아니라 "에스케이하이닉스", "NAVER"가 아니라 "네이버", "HD현대중공업"이 아니라
"에이치디현대중공업"). 지금은 KIS가 주는 이름을 그대로 쓰고 있는데, 사용자에게 익숙한 이름으로
바꾸려면 별도의 종목명 매핑표가 필요하다 — 지금은 임의로 이름을 바꾸지 않았다.

### Supabase 최종 상태

전체 100건(macro 58 + dividend 42).

## 24. KIS 합병/분할일정 구현 — `start_date`/`end_date` 첫 실사용

배당과 달리 전체 시장 조회(SHT_CD 빈값)로도 2026년 30건뿐이라 페이지 제한에 안 걸림을 먼저 확인
후, 종목코드 없이 전체 조회 한 번으로 구현.

### 신규/수정 파일

| 파일                                       | 내용                                                                                                                                                                    |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `core/kis_client.py`                       | `get_merger_split_schedule(f_dt, t_dt, sht_cd)` 추가(기존 함수는 그대로)                                                                                                |
| `services/calendar.py`                     | `_clean_kis_date_compact`(구분자 없는 "YYYYMMDD" 파서), `_split_kis_date_range`(기간 문자열 분리), `_merger_split_event_from_kis`, `ingest_merger_splits_from_kis` 추가 |
| `scripts/seed_kis_merger_splits.py` (신규) | 전체 시장 조회 실행 스크립트                                                                                                                                            |

### 변환 규칙 (KIS 레코드 → CalendarEvent)

| 필드                               | 값                                                                                                                                                                                                                                                |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`                               | `kis-mergersplit-{종목코드}-{record_date}-{seq}` — `seq`를 포함한 이유는 회사분할 시 한 레코드가 여러 신설 종목코드로 나뉘어 같은 날짜에 여러 건 생기기 때문(예: 한화머시너리앤서비스홀딩스 분할이 000880/000885/00088K 3건으로 옴 — 실제 확인됨) |
| `publishedAt`                      | `record_date`                                                                                                                                                                                                                                     |
| **`start_date`/`end_date`**        | `td_stop_dt`(매매정지 기간, "YYYY/MM/DD ~ YYYY/MM/DD" 또는 "YYYY/MM/DD ~") 파싱 결과. **CLAUDE.md가 다일 이벤트용으로 예비해둔 이 두 컬럼을 프로젝트에서 처음으로 실사용**                                                                        |
| `category`                         | `"macro"` (14번 항목 결정 그대로)                                                                                                                                                                                                                 |
| `title`                            | `"{cust_nm} {merge_type}"` (예: "휴맥스 흡수합병")                                                                                                                                                                                                |
| `summary`                          | 관련 회사(`opp_cust_nm`), 비율(`merge_rate`), 매매정지 기간, 신주상장일(`list_dt`) 중 있는 것만 문장으로 조합                                                                                                                                     |
| `actual`                           | `merge_rate`(합병/분할 비율), 없으면 `null`                                                                                                                                                                                                       |
| `previous`/`forecast`/`importance` | 항상 `null`                                                                                                                                                                                                                                       |
| `status`                           | 배당과 동일하게 날짜 기반(`publishedAt` 기준 과거/미래)                                                                                                                                                                                           |

`cust_nm`(이 종목)과 `opp_cust_nm`(관련 회사) 중 어느 쪽이 "흡수하는 쪽"인지 필드명만으로는
단정할 수 없어서, title/summary에서 방향성(A가 B를 흡수한다 등)은 주장하지 않고 사실 관계만
기술했다 — 임의 추론 금지 원칙 적용.

### 실행 결과

```
=== KIS 합병/분할일정: 30건 upsert ===
  kis-mergersplit-028080-20260930-0 | start_date=2026-09-29 end_date=None       | 휴맥스 흡수합병
  kis-mergersplit-082640-20260810-0 | start_date=2026-08-07 end_date=2026-08-30 | 우리금융지주 주식교환
  ...
```

`merge_type`은 "흡수합병"/"회사분할"/"주식교환"/"분할합병" 등 KIS가 이미 한국어로 제공하는 값을
그대로 사용.

### Supabase 최종 상태

전체 130건(macro 88 + dividend 42).

## 25. KIS 신규상장(IPO)/유상증자/무상증자 구현

### ⚠️ "신규상장" 관련 확인 필요 사항

KIS에 "상장정보일정"(`ksdinfo/list-info`)이라는 API가 따로 있는데, 실제로 호출해보니 이건
**진짜 신규 IPO가 아니라 전환사채(CB)/신주인수권(BW) 행사·스톡옵션 행사로 인한 기존 상장사의
추가 주식 상장**이었다(`issue_type` 값이 "국내CB행사"/"국내BW행사"/"STOCKOPTION행사" 등으로
확인됨). 일반적으로 "신규상장"이라 하면 IPO(기업공개)를 뜻하므로, **이미 조사해둔
`ksdinfo/pub-offer`(공모주청약일정)를 "신규상장"으로 구현했다.** `list-info`는 다른 성격의
데이터라 이번엔 구현하지 않음 — 필요하면 별도로 다시 논의.

### 신규/수정 파일

| 파일                                           | 내용                                                                                                                |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `core/kis_client.py`                           | `get_ipo_schedule`, `get_paidin_capital_increase_schedule`, `get_bonus_issue_schedule` 3개 추가(기존 함수는 그대로) |
| `services/calendar.py`                         | 각각의 변환 함수(`_ipo_event_from_kis` 등)와 ingest 함수(`ingest_ipos_from_kis` 등) 3세트 추가                      |
| `scripts/seed_kis_corporate_actions.py` (신규) | 셋을 한 번에 실행하는 스크립트                                                                                      |

### 조회 방식 (엔드포인트별 데이터량에 맞춰 다르게 선택)

| 일정          | endpoint               | TR_ID           | 2026년 건수                          | 조회 방식                                                                    |
| ------------- | ---------------------- | --------------- | ------------------------------------ | ---------------------------------------------------------------------------- |
| 신규상장(IPO) | `ksdinfo/pub-offer`    | `HHKDB669108C0` | 43건                                 | 전체 시장(페이지 제한 안 걸림, 라이브 확인)                                  |
| 유상증자      | `ksdinfo/paidin-capin` | `HHKDB669100C0` | 82건                                 | 전체 시장(마찬가지로 안 걸림)                                                |
| 무상증자      | `ksdinfo/bonus-issue`  | `HHKDB669101C0` | 100건(전체 조회 시 페이지 제한 도달) | 주요 기업 29개 종목코드 지정 조회(배당일정과 동일 방식) — 결과 1건(셀트리온) |

### category 판단

세 가지 다 "기업 주식구조 변경" 이벤트로 보고 **`"macro"`**로 저장했다. 5개 고정 카테고리 중
확정된 지침이 없어서, 24번 항목의 합병/분할과 같은 논리(마땅한 카테고리가 없으면 macro로 묶음)를
그대로 적용한 판단 — 확정 사항 아님, 필요하면 재논의.

### 변환 규칙 요약

| 일정     | `start_date`/`end_date`    | `actual`에 넣은 값                                                                       |
| -------- | -------------------------- | ---------------------------------------------------------------------------------------- |
| IPO      | `subscr_dt`(청약기간) 파싱 | `fix_subscr_pri`(공모가)                                                                 |
| 유상증자 | `sub_term`(청약기간) 파싱  | `fix_rate`(신주배정비율 %) — `fix_price`(확정발행가)는 대부분 "0"(미확정)이라 채택 안 함 |
| 무상증자 | 없음(해당 필드 없음)       | `fix_rate`(신주배정비율 %)                                                               |

### 실행 결과

```
=== 신규상장(IPO): 43건 upsert ===
=== 유상증자: 82건 upsert ===
=== 무상증자: 1건 upsert ===   (주요기업 29개 중 셀트리온만 2026년 무상증자 있음)
```

`GET /calendar/events?year=2026&month=9` 실제 호출로 FRED 지표·배당·IPO·유상증자가 한 응답에
정상적으로 섞여 나오는 것 확인 완료(예: "엔에이치스팩34호 공모주 청약", "에스케이디앤디
유상증자", "미국 비농업 고용" 등이 같은 배열에 같이 있음).

### Supabase 최종 상태

전체 256건(macro 214 + dividend 42).

## 26. 유상증자/무상증자 캘린더 제외 결정

25번 항목 직후, "신규상장/유상증자/무상증자가 초보 투자자에게 얼마나 중요한가"를 물어봐서 아래
의견을 드렸고, 그대로 확정됐다.

- **IPO는 유지** — 한국 개인투자자에게 "공모주 청약"은 관심도가 매우 높은 항목
- **유상증자/무상증자는 제외** — 유상증자는 기존 주주 입장에서 "주의할 리스크"일 뿐 초보자가
  능동적으로 찾아볼 이벤트가 아니고, 무상증자는 대형주에선 드묾(주요기업 29개 중 1건). 특히
  유상증자만 82건이라 다 넣으면 낯선 중소형주 이름으로 캘린더가 채워져서 CPI·삼성전자 배당 같은
  진짜 중요한 항목이 묻힐 위험이 있다고 판단

### 처리

- Supabase에서 기존에 넣었던 83건(유상증자 82 + 무상증자 1)을 직접 DELETE로 제거
  (`id LIKE 'kis-paidincap-%' OR id LIKE 'kis-bonusissue-%'`)
- `scripts/seed_kis_corporate_actions.py`에서 유상증자/무상증자 호출을 제거하고 IPO만 남김 —
  재실행해도 다시 안 들어감
- `services/calendar.py`의 `ingest_paidin_capital_increases_from_kis`/`ingest_bonus_issues_from_kis`
  함수 자체는 **삭제하지 않고 남겨둠** — FEDFUNDS를 보류 처리했을 때(18번 항목)와 같은 방식으로,
  나중에 다시 필요해지면 스크립트에 호출만 추가하면 되도록. `core/kis_client.py`의 관련 함수도 동일.

### Supabase 최종 상태

전체 173건(macro 131 + dividend 42).

## 27. 합병/분할 캘린더 제외 결정

26번 항목 직후 "전체적으로 불필요한 데이터/더 필요한 데이터"를 물어봐서, 합병/분할도 유상증자와
비슷하게 "보유 종목이 아닌 이상 초보자가 능동적으로 찾아볼 정보는 아니다"라는 의견을 드렸고 그대로
제외 결정됨. 대신 가장 아쉬운 공백으로 **기업 실적 발표일**(삼성전자/SK하이닉스/NVIDIA/Apple
등, 현재 KIS·FRED 어디에도 발표일 소스가 없음)을 꼽았고, 그다음 우선순위로 한국 증시 휴장일·FOMC
일정을 제안함 — 다음 작업 후보에 반영.

### 처리

- Supabase에서 기존 30건을 직접 DELETE로 제거 (`id LIKE 'kis-mergersplit-%'`)
- `scripts/seed_kis_merger_splits.py` 상단에 "재실행하면 다시 들어가니 주의" 경고 주석 추가
  (26번 항목과 동일한 방식)
- `services/calendar.py`의 `ingest_merger_splits_from_kis`/`core/kis_client.py`의
  `get_merger_split_schedule`은 **삭제하지 않고 남겨둠** — 26번 항목과 동일한 이유(정책이 바뀌면
  재사용 가능하도록)

### Supabase 최종 상태

전체 143건(macro 101 + dividend 42).

## 28. FRED·KIS 수집 현황 종합 정리 (2026-09-14 기준)

지금까지 여러 항목에 흩어져 있던 FRED/KIS 데이터 현황을 한 곳에 모은 스냅샷. 실제 Supabase를
다시 조회해서 검증한 최신 수치이며, 코드는 건드리지 않았다.

### 현재 `calendar_events`에 실제로 들어있는 것 (전체 143건)

**FRED (미국 경제지표, 전부 `category="macro"`, `region="미국"`)** — 58건

| 지표                       | series_id  | 주기   | 건수 | 비고                                                |
| -------------------------- | ---------- | ------ | ---- | --------------------------------------------------- |
| 소비자물가지수(CPI)        | `CPIAUCSL` | 월별   | 11   | 1~11월(12월은 발표일 미확정으로 보류)               |
| 생산자물가지수(PPI)        | `PPIACO`   | 월별   | 11   | 위와 동일                                           |
| 국내총생산(GDP)            | `GDP`      | 분기별 | 3    | 1~3분기(4분기는 발표일 미확정)                      |
| 비농업 고용(PAYEMS)        | `PAYEMS`   | 월별   | 11   | 1~11월                                              |
| 실업률(UNRATE)             | `UNRATE`   | 월별   | 11   | 1~11월                                              |
| 개인소비지출 물가지수(PCE) | `PCEPI`    | 월별   | 11   | 1~11월, GDP와 발표 캘린더 공유(실측 검증 로직 적용) |

**KIS (한국, `region="한국"`)** — 85건

| 일정                      | category   | 건수 | 비고                                                            |
| ------------------------- | ---------- | ---- | --------------------------------------------------------------- |
| 배당일정                  | `dividend` | 42   | 주요 기업 29개 종목코드 지정 조회(전체 조회는 페이지 제한 있음) |
| 신규상장(IPO, 공모주청약) | `macro`    | 43   | 전체 시장 조회(연 100건 미만이라 제한 안 걸림)                  |

**status 분포**: RELEASED 122건, SCHEDULED 21건(미래 발표 예정)

### 조사는 했지만 캘린더에서 제외/보류한 것

| 항목                                | 소스                        | 상태                   | 이유                                                                        |
| ----------------------------------- | --------------------------- | ---------------------- | --------------------------------------------------------------------------- |
| 연방기금금리(FEDFUNDS)              | FRED                        | 미구현                 | 매 영업일 발행돼서 "발표 이벤트" 개념이 안 맞음(18번 항목)                  |
| 합병/분할                           | KIS `ksdinfo/merger-split`  | **구현 후 삭제**(27번) | 보유 종목 아니면 관심사 아니라는 판단                                       |
| 유상증자                            | KIS `ksdinfo/paidin-capin`  | **구현 후 삭제**(26번) | 82건이라 캘린더에 노이즈 유발                                               |
| 무상증자                            | KIS `ksdinfo/bonus-issue`   | **구현 후 삭제**(26번) | 대형주엔 드묾(29개 중 1건)                                                  |
| 상장정보일정(`list-info`)           | KIS                         | 조사만 함, 미구현      | "신규상장"이 아니라 CB/BW/스톡옵션 행사로 인한 추가상장이라는 걸 확인(25번) |
| 주주총회일정                        | KIS `ksdinfo/sharehld-meet` | 필드까지 확인, 미구현  | 5개 category 중 마땅한 값이 없어 보류                                       |
| 종목추정실적                        | KIS `estimate-perform`      | 조사만 함, 구현 안 함  | 날짜 개념이 없는 추정치 데이터라 애초에 캘린더 부적합(10번 항목)            |
| ISM 제조업 PMI                      | FRED 후보였으나 없음        | -                      | 라이선스 문제로 FRED가 아예 제공 안 함(400 오류 확인, 20번 항목)            |
| 10년물 국채·금리스프레드·달러인덱스 | FRED                        | 미구현                 | 매 영업일 발행, FEDFUNDS와 같은 이유로 부적합                               |
| PCEPILFE(근원 PCE)                  | FRED                        | 미구현                 | PCEPI(헤드라인)만 구현, 코어는 후순위                                       |
| ICSA(신규 실업수당 청구) 등         | FRED                        | 조사만 함              | 20번 항목에서 후보로 정리, 순위 2순위(주별이라 구현 용이)                   |

### 아직 소스 자체를 못 구한 것 (구현 이전 단계)

- **기업 실적 발표일**(삼성전자·SK하이닉스·NVIDIA·Apple 등) — 현재 최우선 공백
- 한국 증시 휴장일 — KIS `chk-holiday`로 가능하다고 이미 확인됨(설계만 완료, 구현 안 함)
- 미국 증시 휴장일 — FRED/KIS 어디에도 없음, 별도 소스 필요
- FOMC 회의 일정 — Federal Reserve 공식 캘린더 필요
- 한국 기준금리(금통위) — KIS 안에서 검색 안 해봄(22번 항목, "없다"고 단정 안 함)
- 선물/옵션 만기(한국·미국) — API 자체가 없음, 규칙 계산으로 해결 필요

## 29. 버그 수정 — KIS 숫자 필드 공백 트림 누락 + 프런트 실데이터 재반영

프런트에 현재 143건을 다시 반영하는 작업 중 실제 데이터 버그를 하나 발견해서 고쳤다.

### 버그: `_clean_kis_value`가 KIS의 고정폭 공백을 안 지우고 있었음

IPO 데이터를 프런트용으로 변환하다가 `actual`/`summary`에 이상한 공백이 들어있는 걸 발견했다.

```
actual: "       18000"   (앞에 공백 7개)
summary: "...공모가는        18000원입니다..."
```

원인 확인: KIS의 `fix_subscr_pri`(공모가) 같은 일부 숫자 필드가 **고정폭 우측정렬**로 오는데
(`"       18000"`), `_clean_kis_value()`가 `raw in ("", "0", "0.00")`만 검사하고 trim은 안 하고
있었다. 배당의 `per_sto_divi_amt`는 우연히 패딩이 없어서 지금까지 안 걸렸을 뿐, 같은 함수를 쓰는
모든 KIS 숫자 필드(배당금액, 합병비율, 증자비율 등)에 잠재된 문제였다.

### 수정

- `_clean_kis_value`: trim 후 빈 문자열/"0"/"0.00" 판정하도록 수정
- `_clean_kis_date`, `_clean_kis_date_compact`: 방어적으로 trim 추가
- `scripts/seed_kis_dividends.py`, `scripts/seed_kis_corporate_actions.py` 재실행해서
  Supabase에 이미 저장된 값도 정정(upsert라 기존 42+43건이 새 값으로 덮어써짐, 건수 변화 없음)
- 수정 후 재확인: `actual: "18000"`, `summary: "...공모가는 18000원입니다..."` — 정상

### 프런트 `/calendar` 실데이터 재반영 + 실제 화면 확인

19번 항목과 같은 방식으로 `news-data.ts`의 `NEWS` 배열을 현재 143건(버그 수정 반영된 값)으로
다시 채웠다. 이번엔 지난번과 달리 **실제 개발 서버를 띄워 진짜 `/calendar` 화면을 스크린샷으로
확인**했다(이전엔 "문서로만 알려달라"고 하셔서 화면 확인 전에 멈췄었음).

- 첫 스플라이스 시도에서 실수 발견: 기존 파일에 새 주석만 앞에 붙이고 `export const NEWS: NewsItem[] = [` 여는 줄을 빠뜨려서 문법이 깨짐 → 파일 전체를 처음부터 다시 깨끗하게 작성해서 해결(중괄호/대괄호/소괄호 개수 일치 확인 후 배포)
- 백엔드(8080)/프런트(3000) 기동 후 Playwright로 실제 `/calendar` 화면 캡처 — "와이즈플래닛컴퍼니 공모주 청약", "빅웨이브로보틱스 공모주 청약"(KIS IPO), "미국 개인소비지출 물가지수(PCE) - 2026년 8월"(FRED) 등 실데이터가 정상적으로 카드에 표시되는 것 확인
- 테스트 후 서버 종료. 이전에 죽이지 못하고 남아있던 오래된 개발 서버 프로세스(포트 3000 점유)가 있어서 그것도 같이 정리함

### Supabase 최종 상태

전체 143건, 변경 없음(값 교정만).

## 30. 다음 후보

- **기업 실적 발표일 소스 확보** (최우선 공백 — DART 등 KIS/FRED 밖의 별도 소스 조사 필요)
- 한국 증시 휴장일 구현 (KIS `chk-holiday`, 설계 완료·구현만 남음, 하루 1회 호출 제한 유의)
- FOMC 회의 일정 소스 확보 (Federal Reserve 공식 캘린더)
- IPO의 `category="macro"` 배정이 적절한지 재확인(확정 사항 아님)
- "신규상장"으로 `list-info`(CB/BW/스톡옵션 행사에 따른 추가상장)도 별도로 다룰지 결정
- KIS `isin_name`/`cust_nm` → 일반적으로 통용되는 종목명으로 바꿀지(매핑표 필요) 여부 결정
- 20번 항목의 나머지 후보(`ICSA` 신규 실업수당 청구 등) 순차 확장
- FEDFUNDS 처리 방식 별도 논의(H.15 매일 발행 구조를 어떻게 "이벤트"로 환산할지, 혹은 실제
  FOMC 회의 결과 발표 이벤트를 별도 소스로 구할지)
- 기본 흐름이 안정된 뒤 APScheduler로 자동 수집 전환 여부 결정
- 11번 항목에서 제안한 unit/대상기간/국가코드 필드를 추가할지 프런트엔드 팀과 논의
- 프런트엔드 팀과 `GET /calendar/events` Response 구조 최종 합의

FRED (58건, 전부 macro): CPI 11 / PPI 11 / GDP 3 / PAYEMS 11 / UNRATE 11 / PCE 11

KIS (85건): 배당 42(dividend) / IPO 43(macro)
