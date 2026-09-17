서비스 기획 및 아키텍처 계획서
<aside>
📌 본 문서는 최초 기획안을 바탕으로 실제 코드베이스와 calendar 도메인의 구현 내용을 통합한 최신 계획서입니다.

</aside>

---

## 1. 프로젝트 개요

| 항목 | 내용 |
| --- | --- |
| 프로젝트 주제 | 금융 뉴스 요약 및 시황 AI 인사이트 대시보드(개미굴 / Gaemigul) |
| 해결하려는 문제 | 개인 투자자가 시세·뉴스·일정을 서로 다른 곳에서 확인하며 스스로 맥락을 재구성해야 하는 정보 파편화 문제 |
| 대상 도메인 및 데이터 | 국내 상장 주식 + 국내외 주요 지수·환율·금융 뉴스 및 증시 일정 |
| 데이터·분석 방식 | 한국투자증권, 네이버 뉴스, FRED, DART, ECOS 등 외부 데이터 연동. 현재 인사이트는 통계 이상치 탐지와 감성 키워드 사전을 활용한 규칙 기반 방식으로 생성하며, LLM API 연동 시 문장 생성 계층을 교체할 수 있도록 설계 |
| 주요 사용자·시나리오 | 주식 입문자가 정해진 시간대에 대시보드를 확인해 시황·뉴스·일정을 한 화면에서 파악 |

### 1.1 배경 및 목적

- **서비스 목표**: 주식 입문자도 국내외 시황과 관련 뉴스를 한눈에 파악하고, AI가 종합한 인사이트를 통해 시장 흐름을 쉽게 이해할 수 있도록 지원

### 1.2 데이터 범위

- **주식**: 국내 상장 주식
- **지표·환율·금융 뉴스**: 국내외 데이터
- **증시 일정**: 미국 거시경제 지표·FOMC, 국내 기준금리·기업공시·배당·자본시장 일정·파생상품 만기

### 1.3 핵심 컨셉

- 주식 입문자를 위해 전문 용어나 이해하기 어려운 내용을 강조 표시하고, 호버(hover) 시 설명 제공
- `components/term.tsx`와 `lib/glossary.ts`를 활용해 용어 설명 기능 구성

---

## 2. 서비스 페이지 구성

### 2.1 공통 고정 레이아웃

- **좌측 사이드바**: 로고, 메뉴, 페이지별 콘텐츠, tip
- **헤더**: 코스피, 코스닥, 니케이, 달러 환율, S&P500, 나스닥 지수
- 좌측 사이드바와 헤더는 모든 페이지의 공통 고정 영역으로 사용
- 공통 메뉴는 메인·캘린더·히트맵으로 구성하며, 페이지별 콘텐츠 영역은 각 화면 목적에 맞게 제공

### 2.2 메인 페이지

> 레퍼런스: https://www.sesiban.site/timeline?slot=0730
> 

| 영역 | 표시 내용 |
| --- | --- |
| 메인 섹션 | 07:30·09:00·12:00·15:30 시점별 정보를 타임라인으로 표시. 주요 뉴스와 주도 섹터를 기반으로 요약·설명하며, 07:30에는 전날 글로벌 시황을 추가하고 15:30에는 당일 섹터·테마 상승 순위를 제공 |
| 우측 사이드바 | 메인 섹션 정보를 종합한 일간 보고서와 일간 보고서를 기반으로 한 주간 보고서 제공 |
- 개인·외국인·기관 순매수·순매도 지표는 유료 시세 API 연동 전까지 안내 문구로 대체
- 일간·주간 보고서는 규칙 기반 생성 구조이며, 향후 LLM 연동 시 문장 생성부를 교체할 수 있도록 분리

### 2.3 서브 페이지 1 — 증시 캘린더

> 레퍼런스: https://www.saveticker.com/calendar
> 

| 영역 | 표시 내용 |
| --- | --- |
| 메인 섹션 | 캘린더 형태로 주요 증시 일정 표시 |
| 우측 사이드 섹션 | 선택한 일정의 요약, 이전값, 실제값, 발표 상태 등 상세 내용 표시 |

캘린더는 정적 일정뿐 아니라 다음 실시간·공시 데이터를 연동합니다.

- **FOMC**: 2026년 확정 회의 일정 8회와 FRED 기준금리 시계열(`DFEDTARU`, `DFEDTARL`)을 결합해 이전·실제 금리 범위, 인상·인하·동결 여부, bp 변화를 계산합니다. 발표 전후 상태에 맞춰 상세 요약문도 자동 생성합니다.
- **FRED 6개 경제지표**: CPI·PPI·GDP·비농업고용·실업률·PCE의 실제 관측치를 수집해 이전값과 실제값을 계산합니다.
- **DART 잠정실적**: 삼성전자·SK하이닉스·현대차의 잠정실적 발표일과 매출액·영업이익·당기순이익을 전자공시에서 수집합니다.
- **한국투자증권(KIS)**: 배당기준일, 합병·분할, IPO, 유상증자, 무상증자 일정을 실제 공시 기반으로 수집합니다.
- **한국은행 기준금리**: ECOS 시계열과 공식 결정일을 매핑해 실제 발표일에 이벤트를 생성합니다.
- **KOSPI200 선물·옵션 만기**: 트리플위칭을 포함한 만기일을 매월 규칙에 따라 계산합니다.
- **표시 최적화**: `actual_label`로 실제값의 의미(주당·공모가·매출액 등)를 명시하고, 원시 수치를 읽기 쉬운 한국어 단위로 변환합니다.

### 2.4 서브 페이지 2 — 섹터/테마 히트맵

> 레퍼런스: https://www.sesiban.site/
> 

| 영역 | 표시 내용 |
| --- | --- |
| 메인 섹션 | 대표 섹터 6~9개를 등락률 기준 히트맵으로 표시 |
| 인터랙션 | 히트맵 클릭 시 해당 섹터·종목 관련 뉴스 표시 |
- 실시간 API가 없는 데이터는 샘플 데이터로 표시
- 뉴스 제목과 요약의 키워드를 바탕으로 관련 섹터를 추론해 연결

---

## 3. 시스템 아키텍처

### 3.1 전체 데이터 흐름

<aside>
🔄

외부 API·데이터 소스 → 데이터 수집·정제 계층 → RDB 적재 → FastAPI 백엔드 → 대시보드

</aside>

1. **외부 API·데이터 소스**
    - 한국투자증권 API: 국내 주식 시세, 배당·합병·분할·IPO·증자 일정
    - 네이버 뉴스 Search API: 종목·섹터 뉴스
    - FRED API: 미국 거시경제 지표 및 FOMC 금리
    - DART API: 국내 대형주 잠정실적 공시
    - ECOS API: 한국은행 기준금리
2. **데이터 수집·정제 계층**
    - `domain/*/services`의 collector, sentiment, indicator collector 등
3. **RDB 적재**
    - SQLAlchemy 기반, 기본 SQLite 및 Supabase(PostgreSQL) 전환 지원
4. **FastAPI 백엔드**
    - timeline, calendar, heatmap, news, insights 도메인별 API 라우터
    - 규칙 기반 인사이트 생성 계층
5. **프런트엔드**
    - 메인·캘린더·히트맵 페이지

캘린더 데이터는 소스 특성에 따라 “정적 일정 + 실시간 API 값”을 결합하거나,
“실제 API 데이터가 없으면 건너뛰기” 원칙을 적용합니다. 확인되지 않은 값을 임의로 생성하지 않습니다.

### 3.2 요청 및 수집 흐름

#### 메인 페이지

1. 사용자가 대시보드 메인 페이지(`/`)에 접속합니다.
2. 프런트엔드가 `GET /timeline/indicators`와 `GET /timeline`을 호출합니다.
3. 백엔드는 당일 데이터를 조회하고, 최초 실행 등으로 데이터가 없으면 수집 파이프라인을 1회 실행합니다.
4. 원시 데이터는 `insights/services/generator.py`와 `timeline/services/report_generator.py`를 거쳐 읽기 쉬운 문장으로 가공됩니다.
5. 백엔드가 JSON을 반환하고 프런트엔드가 지표 바와 타임라인 카드에 렌더링합니다.
6. 사용자가 시점 카드를 클릭하면 이미 받은 응답에서 해당 데이터를 표시합니다.

#### 캘린더

캘린더는 요청 시 수집하지 않고 백그라운드 스케줄러가 데이터를 미리 적재합니다.
`GET /calendar/events`는 저장된 값을 즉시 반환합니다.

- FOMC 일정·금리: 서버 기동 시 1회, 이후 30분마다
- FRED 6개 지표: 서버 기동 시 1회, 이후 6시간마다
- DART 대형주 3사 실적: 서버 기동 시 1회, 이후 매일 00:10
- 한국은행 기준금리·KOSPI200 만기·KIS 일정: `backend/scripts/seed_*.py`를 통한 수동 시딩

### 3.3 기술 스택

**백엔드**

- 프레임워크: FastAPI
- 패키지 매니저: uv
- DB: SQLite(로컬·데모), Supabase(PostgreSQL)
- ORM·DB 접근: SQLAlchemy 2.x
- 스케줄러: APScheduler

**프런트엔드**

- 프레임워크: Next.js App Router
- 스타일링: Tailwind CSS + shadcn/ui
- 아이콘: lucide

calendar 도메인은 팀 결정에 따라 별도 ORM 모델 대신 `core/database.py`의 `async_session`과 `sqlalchemy.text`를 사용해 `calendar_events` 테이블에 접근합니다. 다른 도메인은 스레드 풀 기반 `BackgroundScheduler`를 사용하고, calendar 재수집 작업은 `AsyncIOScheduler`로 FastAPI 메인 이벤트 루프에서 실행합니다.

### 3.4 저장소 구조

**백엔드** — `backend/src/backend`

- `core/`: config, database, pipeline, scheduler, routers
- `domain/timeline/`: 헤더 지표, 시간대별 타임라인, 일간·주간 보고서
- `domain/calendar/`: 증시 캘린더
- `domain/heatmap/`: 섹터·테마 히트맵
- `domain/news/`: 금융 뉴스 수집 및 감성 분석
- `domain/insights/`: 규칙 기반 인사이트 생성

**calendar 주요 파일**

| 파일 | 역할 |
| --- | --- |
| `services/calendar.py` | FRED·FOMC·DART·ECOS·KIS 데이터 수집, 한국시간·한국어 변환, upsert |
| `routers/calendar.py` | `GET /calendar/events` 엔드포인트 |
| `schemas/calendar.py` | `CalendarEvent` 응답 DTO |
| `scripts/seed_*.py` | 스케줄러가 없는 BOK·KOSPI200 만기·KIS 일정의 수동 시딩 |
| `CLAUDE.md` | 도메인 작업 원칙 |
| `IMPLEMENTATION_LOG.md` | 작업 이력과 트러블슈팅 기록 |

**프런트엔드**

- `app/`: layout, 메인·캘린더·히트맵 페이지
- `components/layout/`: Sidebar, HeaderTicker
- `components/term.tsx`: 용어 호버 설명
- `components/ui/`: shadcn/ui 컴포넌트
- `lib/api.ts`: 백엔드 클라이언트
- `lib/glossary.ts`: 용어 사전
- `lib/utils.ts`: 공통 유틸리티
- 원격 저장소: Gaemigul-app
- 브랜치 전략: `main` + `&lt;back|front&gt;/feat/도메인명` (예: `back/feat/timeline`)

### 3.5 협업 및 Push 규칙

1. **`core/` 폴더 역할**
    - 모든 도메인이 공유하는 코드를 관리합니다.
    - `config.py`는 `.env`에서 API 키를 불러오고, `database.py`는 DB 세션·연결을 담당합니다.
2. **API 클라이언트 파일명**
    - 외부 API 호출 파일은 `(api명)_client.py` 형식으로 작성합니다.
3. **함수 단위 주석**
    - 각 함수가 조회하는 데이터를 주석으로 명시합니다.
4. **`core/` 수정 및 push**
    - 기존 코드 수정·삭제 시 팀에 알린 뒤 `main`에 push합니다.
    - 추가만 하는 경우 별도 공지 없이 push할 수 있습니다.
    - push 전 `uv run fastapi dev main.py`로 서버의 정상 동작을 확인합니다.
5. **일반 작업**
    - 개인 브랜치에서 작업하며, 시작 전 `git pull origin main`으로 최신 변경을 받습니다.
6. **`.env` 관리**
    - 개인정보와 API 키가 포함되므로 저장소에 커밋하지 않습니다.
7. **calendar 도메인 외부 파일 수정**
    - `main.py`, `core/*` 등 담당 도메인 밖의 파일을 수정할 때는 먼저 팀에 확인합니다.
    - 다른 도메인의 코드는 유지하고 calendar 관련 변경만 분리해 반영합니다.

### 3.6 API 명세

| Method | Endpoint | 설명 |
| --- | --- | --- |
| GET | `/timeline/indicators` | 헤더 지표 바 데이터 조회 |
| GET | `/timeline/indicators/{symbol}/history` | 지표 일별 히스토리 |
| GET | `/timeline` | 07:30·09:00·12:00·15:30 시황 타임라인 |
| GET | `/timeline/reports/daily` | 일간 보고서 |
| GET | `/timeline/reports/weekly` | 주간 보고서 |
| GET | `/calendar/events?year=&month=` | 월별 증시 일정과 이벤트 상세 정보 |
| GET | `/heatmap?date=` | 섹터별 히트맵 스냅샷 |
| GET | `/heatmap/{sector}/news` | 섹터 관련 뉴스 |
| GET | `/news` | 감성·섹터 필터를 지원하는 뉴스 목록 |
| GET | `/insights` | 규칙 기반 인사이트 목록 |
| POST | `/collect` | 수집 및 인사이트 생성 파이프라인 수동 실행 |
| GET | `/api/health` | 헬스 체크 |

`GET /calendar/{event_id}`는 별도로 두지 않습니다. `/calendar/events` 응답의 각 이벤트에 `summary`, `previous`, `actual`, `status` 등 상세 정보를 포함해 목록 응답만으로 상세 화면을 구성합니다.

#### CalendarEvent 주요 필드

| 필드 | 설명 |
| --- | --- |
| `id` | 소스별 고유 upsert 키. 재수집해도 중복되지 않음 |
| `publishedAt` / `time` | 한국시간(KST) 기준 발표일·발표 시각. 확인되지 않은 시각은 `null` |
| `region` / `category` | 미국·한국 및 macro·earnings·rate·dividend·optionExpiry 분류 |
| `previous` / `actual` | 단위를 포함한 직전값·실제값. 미발표 시 `actual=null` |
| `actual_label` | 실제값의 의미. 제목만으로 맥락이 명확하면 `null` |
| `status` | `SCHEDULED`(발표 전) 또는 `RELEASED`(발표 후) |

#### category별 데이터 출처

| category | region | 내용 | 출처 |
| --- | --- | --- | --- |
| macro | 미국 | CPI·PPI·GDP·비농업고용·실업률·PCE, FOMC | FRED API |
| macro | 한국 | 합병·분할, IPO, 유상증자, 무상증자 | 한국투자증권 API |
| earnings | 한국 | 코스피 대형주 잠정실적 | DART API |
| rate | 한국 | 한국은행 기준금리 결정 | ECOS API + 공식 결정일 매핑 |
| dividend | 한국 | 배당기준일 | 한국투자증권 API |
| optionExpiry | 한국 | KOSPI200 선물·옵션 만기 | 매월 둘째 목요일 규칙 기반 계산 |

### 3.7 주요 설계 결정

- **도메인·데이터**: 국내 상장 주식에 집중하되, 국내 시황의 글로벌 맥락을 설명하기 위해 해외 지표와 뉴스를 포함합니다.
- **DB 스키마**: 지표·뉴스·일정·섹터 데이터가 서로 다른 소스에서 비동기로 수집되므로 엄격한 외래키 대신 날짜 기반으로 느슨하게 연결합니다. 한 소스의 실패가 다른 조회에 영향을 주지 않도록 하고, `DATABASE_URL` 변경만으로 SQLite에서 Supabase(PostgreSQL)로 전환할 수 있게 합니다.
- **LLM 연동**: 데이터에서 문장으로 변환하는 계층을 `generator.py`와 `report_generator.py`로 분리해 향후 LLM 문장 생성부만 교체할 수 있게 합니다.
- **임의 생성 금지**: 소스에서 제공하지 않는 `forecast`는 사용하지 않으며, 중요도·발표 시각처럼 확인되지 않은 값은 `null`로 둡니다. 발표 예정일이 없으면 이벤트를 만들지 않습니다.
- **재수집 전제**: FRED·DART처럼 사후 수정이 가능한 데이터는 최초 수집값을 확정값으로 간주하지 않고 주기적으로 다시 수집합니다.
- **비동기 DB 엔진**: 모듈 전역의 `async_session`이 여러 이벤트 루프에서 사용되어 커넥션 풀이 손상되지 않도록 calendar 작업을 FastAPI 메인 이벤트 루프의 `AsyncIOScheduler`에서 실행합니다.
- **동기 HTTP 분리**: 동기 `httpx.get()` 호출로 이벤트 루프가 멈추지 않도록 데이터 수집은 `asyncio.to_thread()`로 넘기고 DB 쓰기는 메인 루프에서 처리합니다.
- **장애 격리**: 재수집 작업을 개별 `try/except`로 감싸고 `_logger.exception`으로 원인을 기록합니다. 한 지표나 기업의 실패가 다른 재수집을 막지 않으며 마지막 정상 수집값을 유지합니다.

---

## 4. 필수 구현 내용

- 분석 대상 도메인 정의 및 데이터 수집·정제
- RDB 스키마 설계 및 ERD 작성
- ORM·SQLAlchemy를 활용한 데이터 적재 및 조회
- FastAPI 기반 백엔드 API 구성
- 제공 LLM API 연동 — 규칙 기반 인사이트 생성 계층은 구성되어 있으며 문장 생성 연동 예정
- 인사이트를 확인할 수 있는 웹 대시보드
- 데이터 수집부터 인사이트 생성까지의 파이프라인
- 프로젝트 전체 예외 처리 및 오류 로깅 — calendar 재수집 작업의 장애 격리와 로깅은 적용
- 구현 과정과 실행 방법 문서화

---
