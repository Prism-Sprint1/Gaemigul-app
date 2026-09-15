# calendar.py
# GET /calendar/events 응답에 쓰이는 CalendarEvent DTO
#
# Supabase calendar_events 테이블과 필드명을 동일하게 유지한다 (CLAUDE.md 6, 7번 항목).
# "summaty" 오타는 쓰지 않는다 - 반드시 "summary".

from typing import Optional

from pydantic import BaseModel


class CalendarEvent(BaseModel):
    id: str

    # 발표 날짜. 한국시간(KST) 기준 경제지표 발표일이다.
    # FRED가 주는 미국 기준 날짜를 그대로 복사하지 않고, Service에서 Asia/Seoul로 변환한 값만 들어온다.
    publishedAt: str

    # 시작/종료 날짜 - 현재 보류, 항상 None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    # 발표 시각. 한국시간 기준. 정확히 확인되지 않으면 None (임의 생성 금지)
    time: Optional[str] = None

    region: str
    category: str
    title: str
    summary: str

    # FRED가 표준 중요도(★)를 제공하지 않으므로 현재 항상 None
    importance: Optional[int] = None

    # 직전 발표값
    previous: Optional[str] = None

    # 시장 컨센서스 예상값. FRED가 제공하지 않으므로 현재 항상 None
    forecast: Optional[str] = None

    # 실제 발표값
    actual: Optional[str] = None

    status: str
