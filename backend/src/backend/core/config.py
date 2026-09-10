# config.py
# .env에 저장된 값(API 키 등) 읽어오기

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# [현재 정책] 모든 API 키는 str | None = None (선택값)으로 둔다.
#   키가 없어도 앱은 정상적으로 뜨고, 그 키를 실제로 쓰는 클라이언트를 호출하는 시점에만 에러가 난다.
#   개발 중에는 새 키를 추가한 사람과 아직 .env에 그 키를 못 받은 팀원 사이에 시차가 생기는데,
#   필수값으로 두면 그동안 팀원 전체가 서버를 못 띄우게 되기 때문이다.
#
# [최종 방향] 배포·제출 시점에는 전부 필수값(str)으로 바꾼다.
#   그때는 모든 키가 채워져 있는 게 정상이므로, 설정 누락을 시작 단계에서 바로 잡는 편이 낫다.
#   전환할 때 같이 손봐야 하는 곳: 각 *_client.py의 키 확인 가드, main.py 시작 시 스케줄러 처리
#
# 새 API 키를 추가하려면:
#   1. 여기에 "# OO API - 어느 도메인에서 씀" 주석 + 필드 추가
#   2. .env.example에도 같은 이름으로 추가
#   3. 그 키를 쓰는 클라이언트에 "키 없으면 RuntimeError" 가드 추가
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # 한국투자증권(KIS) 오픈API - timeline 도메인(지표 바), heatmap 도메인에서 사용 예정
    kis_app_key: str | None = None
    kis_app_secret: str | None = None
    kis_base_url: str = "https://openapi.koreainvestment.com:9443"

    # 네이버 검색 API - timeline 도메인(주요 뉴스)에서 사용
    # 네이버 클라우드 플랫폼(NCP)에서 발급받은 키 (developers.naver.com 쪽 키와 다름)
    naver_api_key_id: str | None = None
    naver_api_key: str | None = None

    # 제미나이 API - 브리핑·주린이 해설 생성(timeline), 일정 중요도 판단(calendar)에서 사용
    gemini_api_key: str | None = None

    # Supabase Postgres 연결 문자열 (SQLAlchemy용, asyncpg 드라이버 사용) - 전체 공용
    database_url: str | None = None


# 설정값을 한 번만 읽어서 재사용 (설정값은 항상 이 함수로 가져올 것)
@lru_cache
def get_settings() -> Settings:
    # .env 파일이 없거나 필수 값이 비어있으면 여기서 에러가 난다 -> backend/.env부터 확인
    return Settings()
