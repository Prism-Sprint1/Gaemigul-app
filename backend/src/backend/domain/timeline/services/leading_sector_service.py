# leading_sector_service.py
# 코스피 업종 중 등락률 상위 3개(주도 섹터)를 뽑고, 각 섹터의 대표 종목을 붙여서 돌려준다
#
# 지표 바(market_indicator_service.py)와 달리 캐시를 두지 않는다. 주도 섹터는 타임라인 슬롯을
# 만들 때 한 번만 필요한 값이라, 조회한 결과를 바로 DB에 저장하는 쪽이 맞기 때문이다.
#
# 한 번 실행할 때 KIS 호출 7회 (업종 목록 1 + 섹터 3개 x 종목 순위 2)

from backend.core import kis_client

# 주도 섹터 계산에 쓸 코스피 업종코드 목록
#
# KIS 업종 목록 API는 코스피에 38행을 돌려주는데, 여기엔 업종이 아닌 것들이 섞여 있다.
# 그대로 등락률 정렬하면 "오늘의 주도 섹터 1위: 종합" 같은 결과가 나오므로 화이트리스트로 고정한다.
#
# 제외한 것들:
#   0001 종합 / 0002 대형주 / 0003 중형주 / 0004 소형주 - 시장 전체·규모별 지수
#   0027 제조 - 화학·금속·전기전자 등을 묶은 대분류(거래량 비중 40%, 등락률이 종합과 거의 같음)
#   0024 증권 / 0025 보험 - 0021 금융의 하위 분류라서 뺐다. 금융 업종의 종목 순위를 조회해보면
#                          증권사·보험사가 같이 나온다(실제 호출로 확인). 둘 다 넣으면 TOP3에
#                          금융과 증권이 나란히 떠서 같은 얘기를 두 번 하게 된다
#   0163 고배당50 / 0164 배당성장50 / 0165 우선주 - 전략 지수
#   0195 코스피 TR / 0241 / 0242 / 0244 / 2180 ESG / 2283 기후변화 - 전략 지수
#   0503 VKOSPI - 변동성 지수. 시장이 하락할수록 오르기 때문에 넣으면 결과가 뒤집힌다
#
# 거래소가 업종을 개편하면 이 목록만 고치면 된다
KOSPI_SECTOR_CODES = {
    "0005": "음식료·담배",
    "0006": "섬유·의류",
    "0007": "종이·목재",
    "0008": "화학",
    "0009": "제약",
    "0010": "비금속",
    "0011": "금속",
    "0012": "기계·장비",
    "0013": "전기·전자",
    "0014": "의료·정밀기기",
    "0015": "운송장비·부품",
    "0016": "유통",
    "0017": "전기·가스",
    "0018": "건설",
    "0019": "운송·창고",
    "0020": "통신",
    "0021": "금융",
    "0026": "일반서비스",
    "0028": "부동산",
    "0029": "IT 서비스",
    "0030": "오락·문화",
}

# 종목 옆에 붙일 꼬리표. 화면 문구를 바꾸려면 여기만 고치면 된다
_LABEL_TOP_GAINER = "상승 1위"
_LABEL_TOP_TRADED = "거래 1위"
_LABEL_BOTH = "상승·거래 1위"


# 순위 응답에서 1위 종목만 꺼낸다 (종목이 하나도 없으면 None)
# 등락률 순위와 거래대금 순위 응답 모두 이 함수로 처리한다 - 둘 다 output 배열의 첫 번째가 1위다
def _top_row(raw: dict) -> dict | None:
    rows = raw.get("output") or []
    return rows[0] if rows else None


# 섹터 하나의 대표 종목을 만든다 (상승 1위 / 거래 1위, 같은 종목이면 하나로 합침)
# 반환 형태: [{"name": 종목명, "change_rate": 등락률, "label": 꼬리표}, ...] - 0~2개
def _collect_sector_stocks(sector_code: str) -> list[dict]:
    top_gainer = _top_row(kis_client.get_fluctuation_ranking(sector_code))
    top_traded = _top_row(kis_client.get_volume_ranking(sector_code))

    stocks = []
    # 두 API가 같은 종목을 가리키면 줄을 하나로 합친다 (세시반도 이렇게 표시한다)
    if top_gainer and top_traded and top_gainer["hts_kor_isnm"] == top_traded["hts_kor_isnm"]:
        stocks.append(
            {
                "name": top_gainer["hts_kor_isnm"],
                "change_rate": float(top_gainer["prdy_ctrt"]),
                "label": _LABEL_BOTH,
            }
        )
        return stocks

    if top_gainer:
        stocks.append(
            {
                "name": top_gainer["hts_kor_isnm"],
                "change_rate": float(top_gainer["prdy_ctrt"]),
                "label": _LABEL_TOP_GAINER,
            }
        )
    if top_traded:
        stocks.append(
            {
                "name": top_traded["hts_kor_isnm"],
                "change_rate": float(top_traded["prdy_ctrt"]),
                "label": _LABEL_TOP_TRADED,
            }
        )
    return stocks


# 주도 섹터를 모아서 돌려준다. 타임라인 슬롯을 만들 때 호출한다
# limit로 뽑을 섹터 수 변경 가능 - 기본 3개(화면 카드가 3장이라 3으로 맞춰둠)
#
# "등락률 상위"라서 시장 전체가 빠지는 날에는 3개 모두 마이너스로 나온다. 이건 정상이고,
# 그런 날은 "가장 덜 빠진 섹터"가 곧 주도 섹터다(세시반도 같은 방식으로 표시한다).
# 부호 처리는 프런트에서 change_rate 값이 0보다 큰지 작은지로 나눠서 하면 된다
#
# 반환 형태:
#   [{"code": 업종코드, "name": 업종명, "change_rate": 등락률, "stocks": [...]}, ...]
def collect(limit: int = 3) -> list[dict]:
    raw = kis_client.get_index_category_price("K")
    rows = raw.get("output2") or []

    # 업종 아닌 행(종합, 대형주, VKOSPI 등)을 먼저 걸러낸 뒤 등락률 내림차순으로 정렬한다
    sectors = [row for row in rows if row.get("bstp_cls_code") in KOSPI_SECTOR_CODES]
    sectors.sort(key=lambda row: float(row["bstp_nmix_prdy_ctrt"]), reverse=True)

    result = []
    for row in sectors[:limit]:
        sector_code = row["bstp_cls_code"]
        result.append(
            {
                "code": sector_code,
                # 업종명은 응답 값(hts_kor_isnm)을 그대로 쓴다. 거래소가 이름을 바꿔도 화면에 바로 반영된다
                "name": row["hts_kor_isnm"],
                "change_rate": float(row["bstp_nmix_prdy_ctrt"]),
                "stocks": _collect_sector_stocks(sector_code),
            }
        )
    return result
