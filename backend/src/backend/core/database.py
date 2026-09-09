"""Supabase 클라이언트를 만드는 파일. DB가 필요한 곳에서는 여기 있는 get_supabase()만 가져다 쓰면 된다."""

from functools import lru_cache

from supabase import Client, create_client

from backend.core.config import get_settings


@lru_cache
def get_supabase() -> Client:
    """Supabase 클라이언트를 한 번만 만들어서 재사용한다. 설정값이 필요하면 항상 이 함수를 통해 가져올 것.

    사용 예: get_supabase().table("테이블명").select("*").execute()

    .env에 SUPABASE_URL/SUPABASE_KEY가 없으면 여기서 에러가 난다 — DB를 안 쓰는 기능은
    이 함수를 안 부르니 영향 없다.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_KEY가 .env에 없습니다. backend/.env에 추가해주세요."
        )
    return create_client(settings.supabase_url, settings.supabase_key)
