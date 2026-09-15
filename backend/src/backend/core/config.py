# config.py
# .env에 저장된 값(API 키 등) 읽어오기

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


# 새 API 키를 추가하려면:
#   1. 여기에 "# OO API - 어느 도메인에서 씀" 주석 + 필드 추가
#   2. .env.example에도 같은 이름으로 추가
#   3. 자기 도메인만 쓰는 키면 str | None = None (필수값 X)으로 - 안 그러면 그 키가
#      없는 다른 사람 환경에서는 앱 전체가 아예 안 뜬다(예전에 한 번 이걸로 문제 생겼었음)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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


# 설정값을 한 번만 읽어서 재사용 (설정값은 항상 이 함수로 가져올 것)
@lru_cache
def get_settings() -> Settings:
    # .env 파일이 없거나 필수 값이 비어있으면 여기서 에러가 난다 -> backend/.env부터 확인
    return Settings()
