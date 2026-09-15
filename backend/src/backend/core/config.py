# config.py
# .env에 저장된 값(API 키 등) 읽어오기

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# 새 API 키를 추가하려면:
#   1. 여기에 "# OO API - 어느 도메인에서 씀" 주석 + 필드 추가
#   2. .env.example에도 같은 이름으로 추가
#   3. 자기 도메인만 쓰는 키면 str | None = None (필수값 X)으로 - 안 그러면 그 키가
#      없는 다른 사람 환경에서는 앱 전체가 아예 안 뜬다(예전에 한 번 이걸로 문제 생겼었음)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 한국투자증권(KIS) 오픈API - timeline 도메인(지표 바)에서 사용
    kis_app_key: str
    kis_app_secret: str
    kis_base_url: str = "https://openapi.koreainvestment.com:9443"

#  Supabase Postgres 연결 문자열 (SQLAlchemy용, asyncpg 드라이버 사용) - 전체 공용
    database_url: str | None = None

    # FRED(미국 연준 경제 데이터) API - calendar 도메인에서 사용
    fred_api_key: str | None = None

    # DART(전자공시시스템) Open API - calendar 도메인에서 기업 실적 발표일 조사용(테스트 단계)
    dart_api_key: str | None = None

    # 한국은행 ECOS(경제통계시스템) Open API - calendar 도메인에서 한국 기준금리 조사용(테스트 단계)
    # 인증키가 없으면 "sample"로도 호출 가능하지만 sample은 조회건수가 최대 10건으로 제한된다
    # (ecos.bok.or.kr에서 발급받은 정식 키가 있으면 .env에 넣을 것)
    ecos_api_key: str | None = None


# 설정값을 한 번만 읽어서 재사용 (설정값은 항상 이 함수로 가져올 것)
@lru_cache
def get_settings() -> Settings:
    # .env 파일이 없거나 필수 값이 비어있으면 여기서 에러가 난다 -> backend/.env부터 확인
    return Settings()
