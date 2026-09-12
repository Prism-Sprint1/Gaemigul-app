# top_gainer_service.py
# 정규장 밖 슬롯(08:30 / 17:30 / 20:00)에 넣을 급상승 종목 TOP3를 뽑는다
#
# 왜 주도 섹터 대신 이걸 쓰는가
#   주도 섹터는 "업종 등락률 TOP3"인데, 거래소가 업종 지수를 정규장(09:00~15:30)에만 산출한다.
#   08:30에는 업종 등락률이 전부 0.00%로 나와서 순위 자체가 성립하지 않고,
#   17:30 이후에는 15:30 마감값에 멈춰 있어서 15:30 슬롯과 같은 값이 된다(둘 다 실측 확인).
#   반면 종목 단위 데이터는 그 시간대에도 살아 있어서 급상승 종목으로 대체한다.
#
# 세 슬롯 모두 넥스트레이드(NXT)에서 뽑는다
#   08:30 - NXT 프리마켓 (08:00~08:50)
#   17:30 / 20:00 - NXT 애프터마켓 (15:40~20:00)
#
# 넥스트레이드를 쓰는 이유
#   정규장 밖에 실제로 거래가 돌아가는 시장이 NXT다. `market_div_code="NX"`로 조회하면
#   그 시간대의 순위가 나온다. 2026-09-11 애프터마켓에 실측으로 확인했다
#   (10분 만에 순위가 바뀌고, 거래소(J) 조회는 15:30 종가에 멈춰 있었다).
#
# 08:30을 KRX 장전 예상체결(FHPST01820000)에서 NXT로 바꿨다 (2026-09-12)
#   처음에는 예상체결을 썼다. 값이 하루 종일 남아서 슬롯을 놓쳐도 나중에 채울 수 있다는 장점이 있다.
#   바꾼 이유는 두 가지다.
#     1. 슬롯 이름이 "NXT 프리마켓"인데 데이터는 KRX였다. 이름과 출처가 어긋났다.
#     2. **KRX 장전 동시호가는 08:30에 시작한다.** 08:30:00 정각에 조회하면 주문이 막 모이기
#        시작한 시점이라 예상체결이 비거나 몇 건뿐일 수 있다. NXT 프리마켓은 08:00부터
#        돌고 있어서 08:30에는 이미 거래가 쌓여 있다.
#
#   월요일(9/14) 08:30에 실제로 값이 채워지는지 확인할 것. NXT가 비면
#   아래 표의 "0830"을 "expected"로 되돌리면 예상체결로 돌아간다(함수는 그대로 남겨뒀다)

from backend.core import kis_client

# 뽑을 종목 수 (화면 카드가 3장)
_TOP_COUNT = 3

# 슬롯별로 어느 시장을 볼지. slot_key -> 조회 방식
#   "nxt"      : 넥스트레이드 프리마켓·애프터마켓 (기본)
#   "expected" : KRX 장전 동시호가 예상체결 (08:30 대체 수단으로 남겨둠)
# 슬롯을 추가하거나 방식을 바꾸려면 이 표만 고치면 된다
SOURCE_BY_SLOT = {
    "0830": "nxt",
    "1730": "nxt",
    "2000": "nxt",
}


# 순위 응답에서 필요한 값만 뽑아 등락률 높은 순으로 TOP3를 만든다
# 두 API 모두 hts_kor_isnm(종목명) / prdy_ctrt(등락률) / stck_prpr(가격)을 같은 이름으로 준다
#
# **API가 준 순서를 그대로 믿지 않고 등락률로 다시 정렬한다.**
#   넥스트레이드(NX) 응답의 data_rank가 등락률 내림차순이 아니다. 2026-09-12에 확인한 상위 3개다.
#     1위 영풍 +26.40%  /  2위 에스투더블유 +29.96%  /  3위 나우로보틱스 +13.66%
#   거래소(J)로 같이 조회하면 상위 30개가 전부 29.8~30.0%(상한가)로 정상이었다.
#   NX의 순위 기준이 prdy_ctrt(전일 종가 대비)와 다른 값으로 보인다. 화면에는 prdy_ctrt를
#   보여주므로, 그대로 쓰면 "1위인데 등락률이 2위보다 낮은" 카드가 나온다.
#
#   휴장일에 조회한 값이라 장중에는 다를 수 있지만, 어느 쪽이든 우리가 보여주는 숫자로
#   정렬하는 편이 맞다. 30행을 받아서 정렬한 뒤 상위 3개만 남긴다
def _to_rows(raw: dict) -> list[dict]:
    rows = raw.get("output") or []

    parsed = []
    for item in rows:
        # 값이 비어 오는 행이 있어서 숫자로 못 바꾸면 건너뛴다
        try:
            change_rate = float(item["prdy_ctrt"])
            price = float(item["stck_prpr"])
        except (KeyError, TypeError, ValueError):
            continue

        parsed.append({"name": item["hts_kor_isnm"], "change_rate": change_rate, "price": price})

    parsed.sort(key=lambda row: row["change_rate"], reverse=True)
    return [{"seq": seq, **row} for seq, row in enumerate(parsed[:_TOP_COUNT], start=1)]


# 급상승 종목을 모아서 돌려준다. 타임라인 슬롯을 만들 때 호출한다
# slot_key: "0830" / "1730" / "2000". SOURCE_BY_SLOT에 없는 슬롯이면 빈 목록을 돌려준다
#
# 반환 형태: [{"seq": 순서, "name": 종목명, "change_rate": 등락률, "price": 가격}, ...]
def collect(slot_key: str) -> list[dict]:
    source = SOURCE_BY_SLOT.get(slot_key)
    if source is None:
        return []

    if source == "expected":
        # KRX 장전 동시호가 예상체결. 그날 하루 종일 값이 남아 있어서 나중에 채워도 같은 결과가 나온다.
        # 지금은 쓰지 않지만 08:30 NXT가 비었을 때 돌아갈 수단으로 남겨둔다
        return _to_rows(kis_client.get_expected_ranking(market_open_code="0", rank_sort_code="0"))

    # 넥스트레이드 프리마켓·애프터마켓. 거래소(J)로 조회하면 정규장 밖에는 종가에 멈춰 있어서 의미가 없다
    return _to_rows(kis_client.get_fluctuation_ranking(sector_code="0000", market_div_code="NX"))
