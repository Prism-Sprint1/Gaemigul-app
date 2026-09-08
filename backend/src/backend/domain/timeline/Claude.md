# 담당 업무: 메인 페이지 백엔드 (timeline 도메인)

## 담당 범위

- 메인 페이지 백엔드 구현 (`src/backend/domain/timeline`)
- 실사용 API(한국투자증권, finlight, 네이버 뉴스 등) 데이터 확인 및 기획된 기능의 구현 가능 여부 검증
- 프로젝트 진행 중 미흡한 부분 지원

## 메인 페이지 구성 (내 작업 대상)

- **최상단 지표 바**: 코스피, 코스닥, 니케이, 달러 환율, S&P500, 나스닥 — 모든 페이지 공통 고정 영역이지만 데이터는 이 도메인에서 제공
  - ~~나스닥 선물, 유가, 금~~ 은 제외함. 한국투자증권 API로 조회는 되지만, 지금 쓰는 계좌에 CME/NYMEX/COMEX 거래소 이용 권한이 없어서 호출하면 에러가 남(계좌 권한 문제라 코드로 해결 불가)
- **좌측 사이드바**: 메인 페이지에서는 타임라인 콘텐츠(실시간 이벤트 타임라인)가 들어감. 이 사이드바 껍데기 자체는 전 페이지 고정이고, 캘린더/히트맵 페이지로 이동 시 내부 콘텐츠만 바뀔 예정(다른 도메인 담당, 세부 미정)
- **메인 섹션**: 타임라인별 정보 표시
- **우측 사이드바**: AI가 종합한 일간/주간/월간 보고서
- ⚠️ 타임라인별로 정확히 어떤 데이터를 표시할지는 아직 미확정 — 팀 회의에서 확정 예정

## 브랜치

- `back/feat/timeline` 에서 작업 (main 기준으로 분기)

## 기술 스택

- FastAPI, uv
- DB: Supabase(예정) — 팀 공용 프로젝트 사용, 연결 정보는 `.env`로 관리(커밋 금지)

## 내 작업 위치

```
backend/src/backend/domain/timeline/
├── models/
│   └── timeline.py            (아직 빈 파일 - 타임라인 이벤트 기능용, 미착수)
├── routers/
│   └── timeline.py            (GET /timeline/indicators)
├── schemas/
│   ├── market_indicator.py    (지표 바 응답 형태)
│   └── timeline.py            (아직 빈 파일 - 타임라인 이벤트 기능용, 미착수)
└── services/
    ├── kis_client.py            (한국투자증권 API 직접 호출)
    ├── market_hours.py          (지표별 장 운영시간 판단)
    ├── market_indicator_service.py  (캐시 관리 + 데이터 가공)
    └── timeline.py             (아직 빈 파일 - 타임라인 이벤트 기능용, 미착수)
```

## 최상단 지표 바 — 지금까지 만든 부분이 동작하는 순서

1. **서버가 켜질 때** (`backend/main.py`)
   - `market_indicator_service.refresh_all(force=True)`를 한 번 실행해서 캐시를 채워둔다(장이 닫혀있어도 무조건 한 번은 채움).
   - `APScheduler`로 매 시 0분/30분마다 `refresh_all()`을 자동으로 다시 실행하도록 예약해둔다.

2. **`refresh_all()`이 실행될 때** (`services/market_indicator_service.py`)
   - `_INDICATOR_DEFS`에 적힌 6개 지표(코스피/코스닥/나스닥/S&P500/달러환율/니케이)를 하나씩 돈다.
   - 각 지표마다 먼저 `market_hours.is_market_open()`으로 "지금 이 지표의 시장이 열려있나?"를 확인한다.
     - 닫혀있으면 → 그냥 건너뛴다(캐시에 있던 이전 값이 그대로 유지됨 = 장마감 시 값 고정).
     - 열려있으면(달러환율은 항상) → `kis_client.py`의 함수를 호출해서 실제 값을 가져온다.

3. **`kis_client.py`가 KIS 서버에 실제로 요청을 보낼 때**
   - 먼저 `get_access_token()`으로 인증 토큰을 준비한다(저장된 토큰이 있으면 그걸 재사용, 없으면 새로 발급).
   - 국내지수(코스피/코스닥)는 `get_domestic_index_price()`, 해외지수·환율(나스닥/S&P500/니케이/달러환율)은 `get_overseas_index_or_fx_price()`를 호출해서 KIS 응답(JSON)을 그대로 돌려준다.

4. **받아온 데이터를 가공할 때** (`market_indicator_service._refresh_one()`)
   - KIS 응답에서 필요한 값(현재가, 전일대비율)만 뽑아서 `_cache`라는 딕셔너리에 저장한다.
   - `_cache`는 이 파일 안에서만 쓰는 변수라 서버가 켜져 있는 동안 계속 최신 값을 들고 있는 저장소 역할을 한다.

5. **프론트가 데이터를 요청할 때** (`routers/timeline.py`)
   - `GET /timeline/indicators` 요청이 오면 `market_indicator_service.get_indicators()`를 호출한다.
   - 이 함수는 KIS를 다시 호출하지 않고, `_cache`에 이미 저장돼 있는 값을 그대로 꺼내서
     `schemas/market_indicator.py`에 정의된 형태(JSON)로 바꿔서 응답한다.

정리하면: **KIS 호출은 정시 스케줄러가 백그라운드에서만 하고, 프론트 요청은 항상 캐시된 값을 즉시 받아간다.**