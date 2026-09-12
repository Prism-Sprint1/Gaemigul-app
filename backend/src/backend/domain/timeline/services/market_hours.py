# market_hours.py
# 지표별 장 운영시간 판단 - 지표 바가 장마감 시 갱신을 멈추는 데 쓴다
# 국내 개장일 판단 - 두 곳에서 쓴다
#   1. 슬롯 수집: 휴장일이면 아무것도 하지 않는다 (timeline_service.run_scheduled_collect)
#   2. 지표 바: 휴장일이면 코스피·코스닥을 갱신하지 않는다 (is_market_open)

import logging
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from backend.core import kis_client

_KST = ZoneInfo("Asia/Seoul")
_US_EASTERN = ZoneInfo("America/New_York")

logger = logging.getLogger(__name__)

# 지표별 개장/마감 시간과 휴장일 판정 기준.
# (시간대, 개장, 마감, 국내 휴장일을 따르는지) - 여기를 바꾸면 그 지표의 갱신 조건이 바뀐다.
#
# 코스피/코스닥/니케이는 한국 시간 기준(한국이랑 일본이 시차가 없어서 같이 씀)
# 나스닥/S&P500은 미국 동부시간 기준 - 이 시간대는 미국 서머타임을 자동으로 반영해준다
#
# 마지막 값은 국내휴장일 조회(CTCA0903R)를 적용할지 여부다.
# 국내 지표만 True고, 해외 지표는 주말과 시간대만 본다(아래 is_market_open 주석 참고)
_MARKET_HOURS: dict[str, tuple[ZoneInfo, time, time, bool]] = {
    "kospi": (_KST, time(9, 0), time(15, 30), True),
    "kosdaq": (_KST, time(9, 0), time(15, 30), True),
    "nikkei": (_KST, time(9, 0), time(15, 30), False),
    "sp500": (_US_EASTERN, time(9, 30), time(16, 0), False),
    "nasdaq": (_US_EASTERN, time(9, 30), time(16, 0), False),
}

# 환율(usdkrw)은 정해진 마감시간이 없어서 위 목록에 안 넣고, 항상 갱신하도록 여기 따로 뺐다
ALWAYS_REFRESH_CODES = {"usdkrw"}


# 지금 이 지표의 시장이 열려있는지 확인
#
# 국내 지표는 주말 -> 국내 휴장일 -> 개장 시간 순으로 세 가지를 본다.
# 해외 지표는 주말과 개장 시간만 본다.
#
# 해외 공휴일은 보지 않는다 (알려진 한계, 의도한 선택)
#   KIS에 해외 개장일을 알 수 있는 API가 있다(CTOS5011R "해외결제일자조회").
#   거래가 있는 시장만 행으로 오는 성질을 쓰면 미국·일본 휴장을 실제로 가려낼 수 있고,
#   2026-09-23 일본 추분에 JP만 빠지는 것까지 확인했다. 그런데 붙이지 않기로 했다.
#
#   이유는 이득이 비용에 비해 작다는 것이다.
#     아끼는 호출    연간 약 1,000회 = 하루 3회 (미국 9일 + 일본 17일 x 10분 주기)
#     드는 비용      개장 여부 필드가 없어서 "행이 있으면 개장"으로 해석해야 하고,
#                   조회 범위가 당월 말까지라 0행이 "휴장"인지 "데이터 없음"인지 구분이 안 된다.
#                   0행을 휴장으로 믿으면 10월 1일에 해외 지표 갱신이 통째로 멈춘다
#                   (실제로 그렇게 짰다가 발견해서 고쳤다)
#   KIS 호출 한도는 초당 기준이라 하루 3회는 의미가 없다. 애매한 API를 하나 더 물고
#   조용히 멈출 위험을 안는 것보다, 해외 공휴일에 값 안 변하는 호출을 몇 번 더 하는 편이 낫다.
#
#   해외 공휴일에 갱신을 시도해도 화면은 틀어지지 않는다. KIS가 마지막 종가를 주므로
#   캐시 값이 그대로 유지된다. 낭비되는 것은 호출 횟수뿐이다.
def is_market_open(code: str, now: datetime | None = None) -> bool:
    if code not in _MARKET_HOURS:
        raise ValueError(f"'{code}'는 market_hours 대상이 아닙니다 (ALWAYS_REFRESH_CODES 확인).")

    tz, open_time, close_time, follows_domestic_holiday = _MARKET_HOURS[code]
    local_now = now.astimezone(tz) if now else datetime.now(tz)

    if local_now.weekday() >= 5:  # 5=토요일, 6=일요일
        return False

    if follows_domestic_holiday and not is_trading_day(local_now.date()):
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
            logger.warning("휴장일 조회 실패, 개장일로 보고 진행합니다 - %s: %s", type(error).__name__, error)
            return True

    return _open_day_cache.get(day, True)
