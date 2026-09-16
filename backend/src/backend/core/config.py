# config.py
# backend/.env 값을 읽어 설정 객체로 제공한다 (전 도메인 공용). 설정은 항상 get_settings()로 가져온다.

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# .env의 키 이름(대소문자 무관)과 필드 이름이 같으면 자동으로 채워진다
# 키는 전부 선택값(None 허용)이다. 키가 없어도 서버는 뜨고, 그 키를 쓰는 클라이언트를 호출할 때만 에러가 난다
# 새 키를 추가하려면: 여기에 필드 추가 -> .env.example에 같은 이름 추가 -> 쓰는 클라이언트에 "키 없으면 RuntimeError" 추가
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

<<<<<<< HEAD
    # 한국투자증권 오픈API (timeline 지표 바·슬롯, heatmap)
    kis_app_key: str | None = None
    kis_app_secret: str | None = None
    kis_base_url: str = "https://openapi.koreainvestment.com:9443"

    # 네이버 클라우드 플랫폼(NCP) 뉴스 검색 키 (developers.naver.com 키와 다름) (timeline 뉴스)
    naver_api_key_id: str | None = None
    naver_api_key: str | None = None

    # 제미나이 API (timeline 브리핑·해설·보고서, calendar)
    gemini_api_key: str | None = None

    # Supabase Postgres 연결 문자열. "postgresql+asyncpg://"로 시작해야 한다
    database_url: str | None = None

    # Cloudflare Workers AI 이미지 생성 (timeline 보고서 이미지)
    cloudflare_account_id: str | None = None
    cloudflare_api_token: str | None = None
=======
    # 한국투자증권(KIS) 오픈API - timeline(지표 바), heatmap(단물 지도) 공용
    kis_app_key: str
    kis_app_secret: str
    kis_base_url: str = "https://openapi.koreainvestment.com:9443"

    # 히트맵 수집 설정. 시세 조회만 사용하며 기존 KIS 계정/토큰을 함께 쓴다.
    heatmap_enabled: bool = True
    # 지표 바와 히트맵을 합한 프로세스 내 호출 속도. 계정의 실제 한도에 맞춰 낮출 수 있다.
    heatmap_requests_per_second: float = Field(default=5.0, gt=0, le=20)
    # 수능일 등 특별 거래시간은 KRX 공지에 맞춰 날짜별로 지정한다(한국 시간).
    # 예: {"2026-01-02": {"open": "10:00", "close": "15:30"}}
    heatmap_session_overrides: dict[str, dict[str, str]] = Field(default_factory=dict)

    # Supabase Postgres 연결 문자열 (SQLAlchemy용, asyncpg 드라이버 사용) - 전체 공용
    database_url: str | None = None

    # FRED(미국 연준 경제 데이터) API - calendar 도메인에서 사용
    fred_api_key: str | None = None

    # DART(전자공시시스템) Open API - calendar 도메인에서 기업 실적 발표일 조사용(테스트 단계)
    dart_api_key: str | None = None

    # 한국은행 ECOS(경제통계시스템) Open API - calendar 도메인에서 한국 기준금리 조사용(테스트 단계)
    # 인증키가 없으면 "sample"로도 호출 가능하지만 sample은 조회건수가 최대 10건으로 제한된다
    # (ecos.bok.or.kr에서 발급받은 정식 키가 있으면 .env에 넣을 것)
    ecos_api_key: str | None = None

>>>>>>> 417a5403824a674ccf01b6c32189b97a377db9be

    # 이미지 생성 서비스 선택 - "cloudflare"(기본) / "pollinations"(시험용). 지우면 Cloudflare
    image_provider: str = "cloudflare"
    # Pollinations 이미지 생성 (enter.pollinations.ai에서 발급하는 sk_ 비밀 키, 서버에서만 쓴다)
    pollinations_api_key: str | None = None
    # Pollinations 이미지 모델 id (예: black-forest-labs/flux.2-pro, black-forest-labs/flux.1-schnell)
    pollinations_image_model: str = "black-forest-labs/flux.2-pro"

    # Supabase Storage 파일 업로드 (timeline 보고서 이미지). URL은 "https://프로젝트ID.supabase.co"
    # 서비스 키는 DB 전체 권한이라 서버에서만 쓴다 (프런트·깃에 넣지 말 것)
    supabase_url: str | None = None
    supabase_service_key: str | None = None


# 설정을 한 번만 읽어 재사용한다 (.env를 바꾸면 서버를 재시작해야 반영된다)
@lru_cache
def get_settings() -> Settings:
    return Settings()
