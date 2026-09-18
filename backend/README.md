# Gaemigul backend

FastAPI 서버. 도메인별 코드는 `src/backend/domain/`, 외부 API 호출은 `src/backend/core/`에 있다.
담당 도메인 설명과 작업 기록은 각 도메인의 `Claude.md`를 본다 (예: `src/backend/domain/timeline/Claude.md`).

## 실행

```bash
uv sync                      # 의존성 설치
cp .env.example .env         # 키 입력 (커밋하지 말 것)
uv run python create_tables.py   # 없는 테이블만 생성
uv run fastapi run main.py   # 서버 실행 (자동 재시작 없음 - 코드를 고치면 직접 재시작)
```

- API 문서: `http://127.0.0.1:8000/docs`
- 로그: 터미널 + `logs/timeline.log` (14일 보관)

## 예약 작업

서버가 떠 있는 동안에만 동작한다. 시각·주기는 `main.py` 맨 위 목록 참고.
타임라인 슬롯 8회, 일간·주간 보고서(20:10), 지표 바, market 데이터(VIX·환율·수급·시장심리·거래대금).

## 주의

- `.env`와 `.cache/`(KIS 토큰)는 커밋하지 않는다.
- KIS 토큰은 계좌 단위라 `kis_client.get_access_token()`만 쓴다. 따로 발급하면 계좌 주인에게 알림이 간다.
- 같은 DB를 보는 서버를 두 대 이상 켜지 않는다. 수집이 중복되고 저장이 충돌한다.
