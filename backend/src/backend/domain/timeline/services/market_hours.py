# market_hours.py
# 지표별 장 운영시간 판단 (장마감이면 갱신을 멈추는 데 사용)

from datetime import datetime, time
from zoneinfo import ZoneInfo

_KST = ZoneInfo("Asia/Seoul")
_US_EASTERN = ZoneInfo("America/New_York")

# 지표별 개장/마감 시간. 여기 시간을 바꾸면 그 지표의 개장/마감 시간이 바뀐다.
# 코스피/코스닥/니케이는 한국 시간 기준(한국이랑 일본이 시차가 없어서 같이 씀)
# 나스닥/S&P500은 미국 동부시간 기준 - 이 시간대는 미국 서머타임을 자동으로 반영해준다
_MARKET_HOURS: dict[str, tuple[ZoneInfo, time, time]] = {
    "kospi": (_KST, time(9, 0), time(15, 30)),
    "kosdaq": (_KST, time(9, 0), time(15, 30)),
    "nikkei": (_KST, time(9, 0), time(15, 30)),
    "sp500": (_US_EASTERN, time(9, 30), time(16, 0)),
    "nasdaq": (_US_EASTERN, time(9, 30), time(16, 0)),
}

# 환율(usdkrw)은 정해진 마감시간이 없어서 위 목록에 안 넣고, 항상 갱신하도록 여기 따로 뺐다
ALWAYS_REFRESH_CODES = {"usdkrw"}


# 지금 이 지표의 시장이 열려있는지 확인 (주말이면 무조건 닫힘)
# 공휴일은 따로 체크하지 않음 - 공휴일에도 "열려있다"고 잘못 판단할 수 있음(알려진 한계)
def is_market_open(code: str, now: datetime | None = None) -> bool:
    if code not in _MARKET_HOURS:
        raise ValueError(f"'{code}'는 market_hours 대상이 아닙니다 (ALWAYS_REFRESH_CODES 확인).")

    tz, open_time, close_time = _MARKET_HOURS[code]
    local_now = now.astimezone(tz) if now else datetime.now(tz)

    if local_now.weekday() >= 5:  # 5=토요일, 6=일요일
        return False

    return open_time <= local_now.time() <= close_time
