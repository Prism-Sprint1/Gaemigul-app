# top_gainer_service.py
# 정규장 밖 슬롯(08:30 / 17:30 / 20:00)에 넣을 급상승 종목 TOP3를 뽑는다
#
# 왜 주도 섹터 대신 이걸 쓰는가
#   주도 섹터는 "업종 등락률 TOP3"인데, 거래소가 업종 지수를 정규장(09:00~15:30)에만 산출한다.
#   08:30에는 업종 등락률이 전부 0.00%로 나와서 순위 자체가 성립하지 않고,
#   17:30 이후에는 15:30 마감값에 멈춰 있어서 15:30 슬롯과 같은 값이 된다(둘 다 실측 확인).
#   반면 종목 단위 데이터는 그 시간대에도 살아 있어서 급상승 종목으로 대체한다.
#
# 시간대마다 봐야 할 시장이 다르다
#   08:30 - KRX 장전 동시호가의 예상체결 (08:30~09:00)
#   17:30 / 20:00 - 넥스트레이드 애프터마켓 (15:40~20:00)

from backend.core import kis_client

# 뽑을 종목 수 (화면 카드가 3장)
_TOP_COUNT = 3

# 슬롯별로 어느 시장을 볼지. slot_key -> 조회 방식
#   "expected" : 장전 예상체결 (KRX 동시호가)
#   "nxt"      : 넥스트레이드 애프터마켓
# 슬롯을 추가하거나 방식을 바꾸려면 이 표만 고치면 된다
SOURCE_BY_SLOT = {
    "0830": "expected",
    "1730": "nxt",
    "2000": "nxt",
}


# 순위 응답에서 필요한 값만 뽑는다
# 두 API 모두 hts_kor_isnm(종목명) / prdy_ctrt(등락률) / stck_prpr(가격)을 같은 이름으로 준다
def _to_rows(raw: dict) -> list[dict]:
    rows = raw.get("output") or []

    result = []
    for seq, item in enumerate(rows[:_TOP_COUNT], start=1):
        # 값이 비어 오는 행이 있어서 숫자로 못 바꾸면 건너뛴다
        try:
            change_rate = float(item["prdy_ctrt"])
            price = float(item["stck_prpr"])
        except (KeyError, TypeError, ValueError):
            continue

        result.append({"seq": seq, "name": item["hts_kor_isnm"], "change_rate": change_rate, "price": price})
    return result


# 급상승 종목을 모아서 돌려준다. 타임라인 슬롯을 만들 때 호출한다
# slot_key: "0830" / "1730" / "2000". SOURCE_BY_SLOT에 없는 슬롯이면 빈 목록을 돌려준다
#
# 반환 형태: [{"seq": 순서, "name": 종목명, "change_rate": 등락률, "price": 가격}, ...]
def collect(slot_key: str) -> list[dict]:
    source = SOURCE_BY_SLOT.get(slot_key)
    if source is None:
        return []

    if source == "expected":
        # 장전 예상체결. 그날 하루 종일 값이 남아 있어서 나중에 채워도 같은 결과가 나온다
        return _to_rows(kis_client.get_expected_ranking(market_open_code="0", rank_sort_code="0"))

    # 넥스트레이드 애프터마켓. 거래소(J)로 조회하면 15:30 종가에 멈춰 있어서 의미가 없다
    return _to_rows(kis_client.get_fluctuation_ranking(sector_code="0000", market_div_code="NX"))
