"""backend/.env에 저장된 값(API 키 등)을 읽어오는 파일."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """새 설정값을 추가하려면 여기랑 .env.example에 같이 추가할 것."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    kis_app_key: str
    kis_app_secret: str
    kis_base_url: str = "https://openapi.koreainvestment.com:9443"

    # 아직 안 만든 사람도 있을 수 있어서 필수값 아님 — 없으면 앱은 정상적으로 뜨고,
    # database.py의 get_supabase()를 실제로 호출하는 시점에만 에러가 난다.
    supabase_url: str | None = None
    supabase_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    """설정값을 한 번만 읽어서 재사용한다. 설정값이 필요하면 항상 이 함수를 통해 가져올 것.

    .env 파일이 없거나 필수 값이 비어있으면 여기서 에러가 난다 — 그럴 땐 backend/.env부터 확인.
    """
    return Settings()
