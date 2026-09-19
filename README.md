# 개미굴 (Gaemigul)

주식 입문자를 위한 시황·뉴스 AI 인사이트 대시보드입니다.
한국투자증권·네이버 뉴스·FRED·DART 데이터를 정해진 시각에 수집하고, Gemini가 입문자용 브리핑·해설과 일간·주간 보고서를 만들어 보여 줍니다.

- 백엔드 API: http://129.225.201.150:8000 (API 문서 `/docs`)
- 대시보드: (Vercel 배포 후 추가)

```
외부 데이터(KIS·네이버·FRED·DART·Gemini) → 백엔드(FastAPI + 예약 작업) → Supabase(DB·이미지) → 프런트엔드(Next.js)
```

| 폴더 | 내용 |
|---|---|
| `backend/` | FastAPI 서버. `src/backend/core`(외부 API·DB), `domain/`(timeline·market·calendar·heatmap) |
| `frontend/` | Next.js 대시보드 |

## 1. 서비스 실행

**준비물**: Python 3.14 + [uv](https://docs.astral.sh/uv/), Node.js 20.9 이상, Supabase PostgreSQL

```bash
# 백엔드 - http://localhost:8000
cd backend
uv sync
cp .env.example .env              # 키 입력 (설명은 .env.example, 커밋 금지)
uv run python create_tables.py    # 처음 한 번, 없는 테이블만 생성
uv run fastapi run main.py

# 프런트엔드 - http://localhost:3000
cd frontend
npm install
cp .env.example .env.local        # NEXT_PUBLIC_API_BASE_URL=백엔드 주소
npm run dev
```

- 백엔드를 켜면 예약 작업이 바로 돈다. 운영 서버가 있으므로 로컬 백엔드는 필요할 때만 켠다 ([4. 운영 규칙](#4-운영-규칙)).
- Vercel(https) 배포에서는 `next.config.ts`의 `rewrites`로 백엔드를 프록시한다 (https 페이지의 http 호출 차단 회피).

### 운영 서버 구축 (Oracle Cloud Always Free, Ubuntu 24.04)

1. VM 생성 후 공용 IP 지정, 보안 목록에 TCP 8000 수신 허용
2. 서버 설정
   ```bash
   sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
   sudo timedatectl set-timezone Asia/Seoul
   sudo apt update && sudo apt install -y fonts-noto-cjk git          # 한글 폰트: 보고서 이미지 합성용
   sudo iptables -I INPUT -p tcp --dport 8000 -m state --state NEW -j ACCEPT && sudo netfilter-persistent save
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. `git clone -b back/dev <저장소>` → `cd backend && uv sync` → `.env` 복사
4. systemd 서비스 `gaemigul` 등록 (`WorkingDirectory=backend`, `ExecStart=.venv/bin/fastapi run main.py --host 0.0.0.0 --port 8000`, `Restart=always`) → `sudo systemctl enable --now gaemigul`

**코드 반영**: `cd ~/Gaemigul-app && git pull && sudo systemctl restart gaemigul` (의존성이 바뀌면 `uv sync` 먼저, 슬롯 시각은 피한다)

## 2. 데이터 갱신

**자동** (서버 안 예약 작업, 한국 시간, 국내 휴장일에는 슬롯·보고서 생략)

| 대상 | 시각 |
|---|---|
| 타임라인 슬롯 8개 | 07:30 · 08:30 · 09:30 · 12:00 · 14:00 · 15:34(장 마감) · 17:30 · 20:00 |
| 일간·주간 보고서 | 20:10 (주간은 그 주 마지막 거래일에 일간 직후) |
| 지표 바 / VIX·환율 차트 | 10분마다 / 매시 00·30분 |
| 수급·시장심리지수 / 거래대금 | 평일 09:00~15:00 30분마다 + 15:35 / 평일 15:34:30 |
| 히트맵 / 캘린더 | 정규장 10분 간격 / FOMC 30분·FRED 6시간·DART 매일 00:10 |

**수동** (슬롯이 빠졌거나 보고서를 다시 만들 때, `.env`의 `ADMIN_API_KEY` 필요)

```bash
curl -X POST -H "X-Admin-Key: $ADMIN_API_KEY" "http://<서버>:8000/timeline/collect/1400"                 # 슬롯 (0730~2000)
curl -X POST -H "X-Admin-Key: $ADMIN_API_KEY" "http://<서버>:8000/timeline/report/daily?date=2026-09-18"  # 보고서 (weekly도 같음)
```

수동 수집은 **실행한 시점의 값**을 저장한다. 보고서의 업종 상승 종목 수는 다음 개장(09:00) 전까지만 다시 받을 수 있다.

## 3. 기본 점검

```bash
curl http://<서버>:8000/                       # {"message":"hello world"} → 서버 정상
sudo systemctl status gaemigul                 # active (running)
grep "스케줄러 시작" backend/logs/timeline.log | tail -1     # "작업 18개"
grep -E "WARNING|ERROR" backend/logs/timeline.log | tail -20
```

**점검 시점**: 평일 슬롯 직후 `저장 완료` 로그, 20:10 뒤 `GET /timeline/report?type=daily&date=오늘`, 하루 한 번 `WARNING|ERROR` 로그

| 증상 | 대응 |
|---|---|
| KIS 호출이 500, 로그에 `EGW00123` | 공유 토큰이 무효 → 자동 1회 재발급. 반복되면 옛 코드로 켜진 로컬 서버를 끈다 |
| DB 연결 실패 `ECIRCUITBREAKER` | 틀린 DB 비밀번호로 접속하는 서버가 있음 → 옛 `.env` 서버를 끄면 몇 분 뒤 자동 해제 |
| 슬롯·보고서가 비어 있음 | 로그 확인 후 2. 수동 갱신 |
| 보고서 이미지 없음 | Pollinations 잔액(402)·한글 폰트(`fonts-noto-cjk`) 확인 |
| 코드가 반영 안 됨 | 자동 재시작이 없으므로 `sudo systemctl restart gaemigul` |

API 전체 목록과 요청·응답 형식은 `/docs`에서 확인한다.

## 4. 운영 규칙

- **백엔드 서버는 한 대만 켠다.** 로컬 백엔드는 평일 슬롯 시각(각 슬롯 앞뒤 5~15분, 19:55~20:40)에 켜지 않는다.
- 로컬 실행은 **최신 `back/dev` + 팀이 공유한 최신 `.env`** 로만 한다. KIS 토큰은 DB로 공유하며, 옛 코드는 토큰을 따로 발급해 운영 서버 토큰을 무효로 만든다.
- `.env`, `backend/.cache/`는 커밋하지 않는다.
- 작업 흐름: 기능 브랜치 push → 확인 후 `back/dev` 병합 → 운영 서버 `git pull` + 재시작.
