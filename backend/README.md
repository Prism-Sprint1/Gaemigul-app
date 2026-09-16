# 개미굴 백엔드

## 실행

Python 3.14 이상과 uv를 사용합니다. `backend` 디렉터리에서 실행합니다.

```powershell
uv sync
# 처음 실행할 때만 .env.example을 .env로 복사하고 기존 KIS 키를 설정합니다.
uv run uvicorn main:app --host 127.0.0.1 --port 8000
```

프론트엔드의 `NEXT_PUBLIC_API_BASE_URL`도 같은 주소를 사용합니다. KIS 키와 토큰은 백엔드에만 둡니다.

## 히트맵

`GET /heatmap?market=kospi&period=day`

- `market`: `kospi`, `kosdaq`
- `period`: `day`, `week`, `month`. 연간은 제공하지 않습니다.
- 시가총액·가격은 원, 거래량은 주, 등락률과 거래량 비중은 0~100 기준 백분율입니다.
- 응답에는 `sectors[].stocks[]`, `top_sector`, `coverage`, `as_of_date`, `updated_at`, `next_update_at`, `market_status`, `is_stale`, `is_refreshing`, `message`가 포함됩니다.
- `updated_at`은 실제 수집 시각이며 GET 요청 시각으로 덮어쓰지 않습니다. `as_of_date`는 데이터 기준 거래일입니다.
- 초기 수집 중에는 HTTP 200과 부분 데이터/빈 목록 및 진행 상태를 반환합니다. 일부 종목이 누락되면 `top_sector=null`; 이전 전체 스냅샷이 있으면 이를 유지하고 지연 상태를 표시합니다.

### 집계 기준

KIS 종목마스터의 보통주(ST)와 외국주권(FS)을 대상으로 우선주·SPAC·ETF·ETN·주식예탁증서 등 별도 상품을 제외합니다. 종목마스터의 가장 세부적인 유효 업종 코드와 최신 업종 마스터의 이름을 사용합니다. 분류가 없는 종목은 `기타·미분류`로 남깁니다. 업종 구성 종목들의 선택 기간 거래량을 합산해 1위를 구하므로, 종합·대형주·제조 전체 같은 중복 집계 지수끼리 순위를 비교하지 않습니다. KIS 업종별 전체시세 API는 있으나 **거래량 1위 업종 전용 API는 확인되지 않았습니다**. 화면 순위는 이 서비스가 계산한 보통주 기준 순위입니다.

일간 등락률은 전 거래일 종가 대비, 주간은 이번 주 시작 전 마지막 거래일 종가 대비, 월간은 이번 달 시작 전 마지막 거래일 종가 대비입니다. 주간·월간 기준가격은 수정주가 일봉을 사용합니다. 기준가격이 없는 신규 상장은 등락률을 `null`로 표시합니다. 거래량은 해당 달력 기간의 일봉 거래량에 현재 거래일의 누적 거래량을 한 번만 더합니다. 10분마다 받은 누적 거래량을 서로 더하지 않습니다.

마스터에 기준가와 시가총액이 모두 0인 레코드가 남아 있으면 주식기본조회(`CTPF1002R`)의 해당 시장 상장폐지일을 확인합니다. 이미 상장폐지된 종목만 대상에서 제외하고, 단순 조회 실패나 가격 미제공은 임의로 제외하지 않습니다.

시가총액은 수집 가격×상장주수입니다. 초기에는 마스터의 천주 단위 상장주수를 변환하고, 기간시세 응답에서 정확한 상장주수를 확보하면 보완합니다. 화면은 가독성을 위해 업종과 종목 두 단계 각각 `sqrt(시가총액)`을 면적 가중치로 사용하며, 실제 시가총액은 별도로 표시합니다.

### 수집과 캐시

기존 APScheduler에서 한국 시간으로 매분 30초에 수집 필요 여부를 검사합니다. KRX 정규장 09:00~15:30 동안 개장 기준 10분 간격으로 갱신하고, 마감 체결 반영을 위해 15:30:30에 마지막 수집을 시작합니다. 전체 종목은 순차 조회하므로 모든 종목이 정확히 동일한 순간의 시세는 아닙니다. 브라우저 조회와 UPDATE 버튼은 저장된 결과만 읽습니다.

종목/업종 마스터는 하루 단위로 저장합니다. 주·월간용 최근 70일 일봉은 하루에 한 번 준비하고 초기 준비는 매분 제한된 시간 동안 나누어 진행합니다. 따라서 최초 실행은 전체 종목 수와 API 지연에 따라 여러 분 이상 걸립니다. 장중에는 일간 시세를 먼저 표시하고 기간 데이터가 준비되는 대로 주간·월간을 채웁니다. 날짜·가격·분류·스냅샷은 `backend/.cache/heatmap/`에 저장되며 Git에서 제외됩니다. 토큰은 기존 `.cache/kis_token.json`을 공유합니다.

정규장 마감에 확보한 시세는 파일에 저장해 서버 재시작 후에도 유지합니다. **장외에 처음 실행하여 마감 스냅샷이 없는 경우 KIS 일봉으로 복원하며, 그 거래량에는 시간외 거래가 포함될 수 있습니다.** 이 경우 화면에도 일봉 기준임을 표시합니다. 다음 정규장 마감부터 예약 수집한 값으로 고정됩니다.

휴장일 API는 당일에 한 번 확인해 캐시합니다. 신규 조회 실패 시 개장일을 평일로 추정하지 않습니다. 휴장일 API는 특별 개장시간까지 제공하지 않으므로, 수능일·연초 개장 등은 KRX 공지에 맞춰 `.env`에 설정합니다.

```dotenv
HEATMAP_ENABLED=true
HEATMAP_REQUESTS_PER_SECOND=5
HEATMAP_SESSION_OVERRIDES={"2026-01-02":{"open":"10:00","close":"15:30"}}
```

날짜별 `{"closed":"true"}`로 특별 휴장도 지정할 수 있습니다. 날짜 예시는 형식 안내이며 실제 거래 일정은 운영 시 확인해야 합니다. 호출 속도는 지표 바와 히트맵을 합친 프로세스 공용 제한입니다. **스케줄러와 토큰 잠금은 프로세스 내에서 공유하므로 서버 worker는 1개로 실행합니다.** 다중 서버/worker 배포 시 수집 전용 worker 및 공유 캐시/잠금으로 분리해야 합니다.

### 코드 위치와 KIS 요청 양식

- `src/backend/core/kis_client.py`: 인증·재시도·공용 속도 제한, API 경로/TR ID/요청 파라미터/응답 필드와 단위 주석, 종목·업종 마스터 파싱.
- `src/backend/domain/heatmap/services/heatmap.py`: 기간 계산, 휴장/세션 판정, 거래량 순위, 캐시 및 오류 처리.
- `src/backend/domain/heatmap/schemas/heatmap.py`: 화면 응답 모델.
- `src/backend/domain/heatmap/routers/heatmap.py`: 캐시 조회 라우터.

참조한 공식 KIS 예제: [업종별 전체시세](https://github.com/koreainvestment/open-trading-api/tree/main/examples_llm/domestic_stock/inquire_index_category_price), [복수 종목 시세](https://github.com/koreainvestment/open-trading-api/tree/main/examples_llm/domestic_stock/intstock_multprice), [수정주가 일봉](https://github.com/koreainvestment/open-trading-api/tree/main/examples_llm/domestic_stock/inquire_daily_itemchartprice), [휴장일](https://github.com/koreainvestment/open-trading-api/tree/main/examples_llm/domestic_stock/chk_holiday), [종목·업종정보파일](https://github.com/koreainvestment/open-trading-api/tree/main/stocks_info).

### 검증

```powershell
uv run python -m unittest discover -s tests
```

테스트는 실제 KIS 요청 없이 토큰 재사용, 업무 오류·속도 제한 재시도, 마스터 단위/분류, 일·주·월 기준가격, 거래량 중복 방지, 불완전 순위, 휴장/특별시간, 마감 저장·복원, 캐시 전용 GET을 검사합니다.
