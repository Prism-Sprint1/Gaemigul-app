# market_hours.py
# 지표별 장 운영시간 판단 (장마감이면 갱신을 멈추는 데 사용)
# 국내 개장일 판단 (주말·공휴일이면 슬롯 수집을 건너뛰는 데 사용)

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from backend.core import kis_client

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


# 국내 장이 열리는 날인지 판단할 때 쓰는 캐시. {날짜: 개장 여부}
# 휴장일 API가 한 번에 20여 일치를 주므로 며칠에 한 번만 호출하면 된다
_open_day_cache: dict[date, bool] = {}


# 휴장일 정보를 받아와 캐시에 채운다
def _load_open_days(base_day: date) -> None:
    rows = kis_client.get_holiday_calendar(base_day.strftime("%Y%m%d")).get("output") or []
    for row in rows:
        parsed = datetime.strptime(row["bass_dt"], "%Y%m%d").date()
        _open_day_cache[parsed] = row["opnd_yn"] == "Y"


# 그날 국내 장이 열리는지 확인 (주말·공휴일이면 False)
#
# 거래소가 정한 휴장일을 그대로 쓴다. 우리가 요일을 따지거나 공휴일 목록을 관리하지 않아도 되고,
# 임시공휴일이나 대체공휴일도 거래소가 반영한 대로 따라간다.
#
# 조회에 실패하면 True(장이 열린다)로 본다.
# 휴장일에 괜히 수집하는 건 데이터를 지우면 되지만, 개장일인데 건너뛰면 그 슬롯을 영영 못 채운다.
# 특히 07:30 환율은 그 시점을 놓치면 되살릴 방법이 없어서, 실패 시에는 수집하는 쪽으로 기울인다
def is_trading_day(day: date | None = None) -> bool:
    day = day or datetime.now(_KST).date()

    if day not in _open_day_cache:
        try:
            _load_open_days(day)
        except Exception as error:
            print(f"[경고] 휴장일 조회 실패, 개장일로 보고 진행합니다 - {type(error).__name__}: {error}")
            return True

    return _open_day_cache.get(day, True)
