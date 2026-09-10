# Calendar 백엔드 1차 구현 정리 (FRED CPI)

CLAUDE.md 요구사항 기준으로 1~4단계(FRED 연동 → FastAPI → Supabase → API 응답)를 CPI 지표 하나로
끝까지 완성한 기록. 개발 순서표 기준 STEP 1~11에 해당.

## 1. 확정된 설계 결정

| 항목 | 결정 |
|---|---|
| ORM 모델 | 사용하지 않음. `models/calendar.py`는 비워둠 |
| Supabase 접근 방식 | `core/database.py`의 `async_session`/`get_db()`를 그대로 재사용, `sqlalchemy.text()` 기반 raw SQL |
| 테이블 생성 방식 | 마이그레이션 도구 없이 Supabase SQL Editor에서 수동 실행 |
| FRED 수집 트리거 | APScheduler 미사용. `scripts/seed_cpi.py` 수동 실행(1회성 적재) |
| API 엔드포인트 | `GET /calendar/events?year=YYYY&month=MM` |
| `publishedAt` 의미 | 한국시간(KST) 기준 경제지표 **발표일**. FRED 원본 날짜를 그대로 쓰지 않고 Service에서 변환 |
| `publishedAt` 타입 | `text` 유지 (`'YYYY-MM-DD'` 형식 고정 → 사전순 정렬이 곧 날짜순 정렬) |
| `forecast`, `importance` | FRED가 제공하지 않으므로 항상 `null` (임의 생성 금지) |
| `source_url` | 컬럼/스키마/코드 어디에도 없음 |
| `summary` | 오타 `summaty` 사용 금지, `summary`로 통일 |

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

| 파일 | 역할 |
|---|---|
| `core/config.py` | `fred_api_key` 필드 추가 (기존 항목 유지) |
| `core/fred_client.py` (신규) | FRED `series/observations`, `series/release`, `release/dates` 호출 전담 |
| `domain/calendar/schemas/calendar.py` | Pydantic `CalendarEvent` (CLAUDE.md 6번 그대로, 14개 필드) |
| `domain/calendar/services/calendar.py` | FRED 호출 → KST 변환 → 한국어 title/summary → upsert/조회. ORM 미사용 |
| `domain/calendar/routers/calendar.py` | `GET /calendar/events?year=&month=` |
| `main.py` | `calendar_router` include 한 줄만 추가 (기존 코드 불변) |
| `scripts/seed_cpi.py` (신규) | CPI 1회 적재용 수동 스크립트 |

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

| 컬럼 | 값 | 비고 |
|---|---|---|
| `id` | `fred-CPIAUCSL-2026-07-01` | `fred-{series_id}-{observation_date}` 규칙 |
| `publishedAt` | `2026-08-12` | FRED 실제 release date를 KST로 환산 |
| `time` | `21:30` | 08:30 ET(서머타임 EDT, UTC-4) → KST(UTC+9) 변환 결과, 검산 일치 |
| `region` | `미국` | |
| `category` | `CPI` | |
| `title` | `미국 소비자물가지수(CPI)` | 최초 적재 시점 값. 8번 항목에서 대상 기간 표기를 추가해 현재는 `"미국 소비자물가지수(CPI) - 2026년 7월"` |
| `previous` | `332.568` | FRED 실제 관측값 |
| `actual` | `332.813` | FRED 실제 관측값 |
| `importance` | `null` | FRED 미제공 |
| `forecast` | `null` | FRED 미제공 |
| `start_date` / `end_date` | `null` | 보류 규칙 |
| `status` | `RELEASED` | `actual` 존재 → RELEASED |

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

| 단계 | 결과 |
|---|---|
| STEP 9 (CPI 1회 적재) | 성공 |
| STEP 10 (저장 데이터/UPSERT 검증) | 성공 |
| STEP 11 (API 실제 호출 테스트) | 성공 |

## 8. title/summary 대상 기간(대상 월) 표기 추가

**문제**: `title`이 항상 `"미국 소비자물가지수(CPI)"`로 고정이라, 이 발표가 **몇 월 데이터인지**
캘린더 화면에서 알 수 없었다. FRED observation의 `date`(예: `"2026-07-01"`)는 **대상 기간**(그
값이 설명하는 달)이고, `release/dates`가 주는 날짜는 **발표일**(그 값이 공개된 날) — 이 둘은
다른 개념이며, `publishedAt`은 이미 발표일 기준으로 정확히 계산되고 있었다. 다만 대상 기간
정보가 어디에도 노출되지 않는 게 진짜 문제였다.

**검토했던 대안과 결정**:

| 대안 | 채택 여부 | 이유 |
|---|---|---|
| `start_date`/`end_date`에 대상 기간(예: 2026-07-01~07-31) 저장 | ❌ | 이 두 컬럼은 CLAUDE.md 10번 항목에서 "여러 날에 걸친 **이벤트**"(FOMC, 컨퍼런스) 용도로 이미 정의됨. "통계가 설명하는 기간"은 다른 개념이라 같은 컬럼에 넣으면 의미가 섞임 → **NULL 유지로 확정** |
| title에 대상 기간을 덧붙임 | ✅ | `"미국 소비자물가지수(CPI) - 2026년 7월"`. 컬럼 추가 없이 텍스트만으로 해결 |
| summary 맨 앞에 대상 기간 안내 문장 추가 | ✅ | `"2026년 7월 소비자물가지수(CPI) 자료입니다."` + 기존 summary |

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

## 9. Response 구조 점검 (Next.js 캘린더 연동 기준)

PPI를 추가하기 전에, 현재 `GET /calendar/events` 응답이 프런트 캘린더에서 바로 쓸 수 있는
구조인지 필드별로 점검한 결과.

| 필드 | 프런트에서의 쓰임 | 비고 |
|---|---|---|
| `publishedAt` | 캘린더에서 어느 날짜 칸에 이벤트를 배치할지 결정 | `'YYYY-MM-DD'`, 이미 KST 기준 |
| `time` | 카드 상단 시각 표시 (`"21:30"`) | `HH:MM` 24시간제. `null`이면 프런트가 시각 미표기 처리 필요 |
| `title` | 카드 제목 | 대상 기간 포함(`"... - 2026년 7월"`)이라 좁은 카드에서는 말줄임(ellipsis) 처리 고려 필요 (프런트 UI 판단 영역) |
| `category` | 색깔별 카테고리 태그 | 문자열 그대로 매핑 키로 사용 가능 |
| `region` | 국가 배지 | 현재 `"미국"` 고정 |
| `summary` | 카드 본문/상세 설명 | 대상 기간 안내 문장이 맨 앞에 포함됨 |
| `actual` / `previous` | 상세 영역의 "실제값 / 이전값" | FRED 실측값, 항상 문자열 |
| `forecast` / `importance` | 상세 영역의 "예상값 / 중요도" | 현재 항상 `null` → 프런트는 "-"로 표시 (CLAUDE.md 39·47번 원칙) |
| `status` | 발표완료(`RELEASED`)/발표예정(`SCHEDULED`) 배지 | `actual` 유무와 사실상 연동되지만 별도 필드로 명시 |
| `start_date` / `end_date` | (현재 미사용) | CPI/PPI 등 단일 발표 지표에는 항상 `null` |

**PPI 추가 시 프런트 영향**: 응답은 카테고리와 무관하게 항상 동일한 14필드 flat 구조이므로,
PPI가 추가돼도 배열에 `category: "PPI"` 항목이 하나 늘어날 뿐 JSON 구조 변경은 없음. 프런트는
카테고리별 색상 매핑에 `PPI` 항목만 추가하면 됨. 백엔드도 `services/calendar.py`의
`_TITLES`/`_SUMMARIES`/`_PERIOD_LABELS`/`_RELEASE_TIME_ET` 4개 표에 `"PPI"` 항목만 추가하면
되고, 라우터/스키마/테이블 변경은 불필요.

## 10. 다음 후보

- PPI(`PPIACO`) 추가 → GDP → 고용(`PAYEMS`) → 실업률(`UNRATE`) → 금리(`FEDFUNDS`) 순으로 확장
  (각 지표 추가 시 `_TITLES`, `_SUMMARIES`, `_RELEASE_TIME_ET`에 항목만 추가하면 되는 구조)
- 기본 흐름이 안정된 뒤 APScheduler로 자동 수집 전환 여부 결정
- 프런트엔드 팀과 `GET /calendar/events` Response 구조 최종 합의
