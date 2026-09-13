# top_gainer_service.py
# 정규장 밖 슬롯(08:30 / 17:30 / 20:00)에 넣을 급상승 종목 TOP3를 뽑는다.
# 이 시간대에는 업종 지수가 산출되지 않아 주도 섹터 대신 이 값을 쓴다.

from backend.core import kis_client

# 뽑을 종목 수. 바꾸면 슬롯에 저장되는 급상승 종목 개수가 바뀐다
_TOP_COUNT = 3

# 슬롯별 조회 방식. slot_key -> 방식
#   "nxt"      : 넥스트레이드 등락률 순위 (08:30 프리마켓 / 17:30·20:00 애프터마켓)
#   "expected" : KRX 장전 동시호가 예상체결 순위 (08:30 대체 수단)
# 08:30 NXT 값이 비면 "0830"을 "expected"로 바꾼다. 여기 없는 슬롯은 급상승 종목을 넣지 않는다
SOURCE_BY_SLOT = {
    "0830": "nxt",
    "1730": "nxt",
    "2000": "nxt",
}


# 순위 응답을 [{seq, name, change_rate, price}] 형태의 TOP3로 만든다
# NX 응답의 순서는 등락률순이 아니므로 prdy_ctrt로 다시 정렬한다
def _to_rows(raw: dict) -> list[dict]:
    rows = raw.get("output") or []

    parsed = []
    for item in rows:
        # 숫자가 비어 오는 행은 건너뛴다
        try:
            change_rate = float(item["prdy_ctrt"])
            price = float(item["stck_prpr"])
        except (KeyError, TypeError, ValueError):
            continue
        parsed.append({"name": item["hts_kor_isnm"], "change_rate": change_rate, "price": price})

    parsed.sort(key=lambda row: row["change_rate"], reverse=True)
    return [{"seq": seq, **row} for seq, row in enumerate(parsed[:_TOP_COUNT], start=1)]


# 슬롯의 급상승 종목 TOP3를 돌려준다. SOURCE_BY_SLOT에 없는 슬롯이면 빈 목록
def collect(slot_key: str) -> list[dict]:
    source = SOURCE_BY_SLOT.get(slot_key)
    if source is None:
        return []

    if source == "expected":
        return _to_rows(kis_client.get_expected_ranking(market_open_code="0", rank_sort_code="0"))

    return _to_rows(kis_client.get_fluctuation_ranking(sector_code="0000", market_div_code="NX"))
