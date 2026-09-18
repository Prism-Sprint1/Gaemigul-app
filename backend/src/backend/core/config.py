# config.py
# backend/.env 값을 읽어 설정 객체로 제공한다 (전 도메인 공용). 설정은 항상 get_settings()로 가져온다.

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# .env의 키 이름(대소문자 무관)과 필드 이름이 같으면 자동으로 채워진다
# 키는 전부 선택값(None 허용)이다. 키가 없어도 서버는 뜨고, 그 키를 쓰는 클라이언트를 호출할 때만 에러가 난다
# 새 키를 추가하려면: 여기에 필드 추가 -> .env.example에 같은 이름 추가 -> 쓰는 클라이언트에 "키 없으면 RuntimeError" 추가
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 한국투자증권 오픈API (timeline 지표 바·슬롯·보고서, market 메인 페이지 데이터)
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

    # 관리용 POST(수집·보고서 생성) 호출 키. 요청 헤더 X-Admin-Key와 비교한다
    # 비워 두면 그 POST들은 503으로 막힌다 (배포 주소가 공개돼도 아무나 못 부르게)
    admin_api_key: str | None = None

    # Pollinations 이미지 생성 (timeline 보고서 이미지). 키(sk_)는 서버에서만 쓴다. 모델 id를 바꾸면 화풍·비용이 바뀐다
    pollinations_api_key: str | None = None
    pollinations_image_model: str = "z-image-turbo"

    # Supabase Storage 파일 업로드 (timeline 보고서 이미지). URL은 "https://프로젝트ID.supabase.co"
    # 서비스 키는 DB 전체 권한이라 서버에서만 쓴다 (프런트·깃에 넣지 말 것)
    supabase_url: str | None = None
    supabase_service_key: str | None = None


# 설정을 한 번만 읽어 재사용한다 (.env를 바꾸면 서버를 재시작해야 반영된다)
@lru_cache
def get_settings() -> Settings:
    return Settings()
