# test_dart_samsung.py
#
# DART(전자공시시스템) API 연결이 정상적으로 되는지 삼성전자(종목코드 005930) 1개 기업으로만
# 테스트한다. 이 스크립트는 조회만 하고 아무 것도 DB에 저장하지 않는다 - calendar_events는
# 손대지 않는다.
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/test_dart_samsung.py`
# 전제: backend/.env에 DART_API_KEY가 설정되어 있어야 한다.

from backend.core import dart_client

SAMSUNG_STOCK_CODE = "005930"

# 최근 1년 9개월 정도로 넉넉히 잡아서 사업보고서(연 1회)·반기보고서(연 1회)·분기보고서(연 2회)가
# 최소 한 번씩은 걸리도록 한다. end_de는 오늘 날짜.
SEARCH_BGN_DE = "20250101"
SEARCH_END_DE = "20260915"

_PERIODIC_REPORT_KEYWORDS = ("사업보고서", "반기보고서", "분기보고서")


def main() -> None:
    print("=== 1. corp_code 목록 조회 ===")
    try:
        corp_codes = dart_client.get_corp_codes()
    except dart_client.DartApiError as e:
        print(f"실패: [{e.status}] {e.message}")
        return
    print(f"전체 {len(corp_codes)}건 (상장사만 필터 전)")

    print("\n=== 2. 삼성전자 corp_code 확인 ===")
    samsung = dart_client.find_corp_by_stock_code(corp_codes, SAMSUNG_STOCK_CODE)
    if samsung is None:
        print(f"실패: 종목코드 {SAMSUNG_STOCK_CODE}에 해당하는 corp_code를 찾지 못함")
        return
    print(samsung)

    print(f"\n=== 3. 공시검색 API 호출 ({SEARCH_BGN_DE} ~ {SEARCH_END_DE}) ===")
    try:
        disclosures = dart_client.get_disclosure_list(
            samsung["corp_code"], SEARCH_BGN_DE, SEARCH_END_DE
        )
    except dart_client.DartApiError as e:
        print(f"실패: [{e.status}] {e.message}")
        return
    print(f"전체 공시 {len(disclosures)}건")

    # 실제 list.json 응답 필드는 corp_code/corp_name/stock_code/corp_cls/report_nm/rcept_no/
    # flr_nm/rcept_dt/rm 뿐이다 - pblntf_ty/pblntf_detail_ty는 응답 필드가 아니라 "요청" 파라미터
    # 이름이라서(공시유형으로 검색 결과를 필터링할 때 씀), 실제 라이브 호출로 확인 후 뺐다.
    print("\n=== 4. 공시 목록 (최근 10건) ===")
    for item in disclosures[:10]:
        print(
            f"  corp_name={item.get('corp_name')} stock_code={item.get('stock_code')} "
            f"report_nm={item.get('report_nm')} rcept_dt={item.get('rcept_dt')} "
            f"rcept_no={item.get('rcept_no')} corp_cls={item.get('corp_cls')}"
        )

    print("\n=== 5. 정기보고서(사업/반기/분기보고서)만 조회 (pblntf_ty=A 요청 파라미터로 필터) ===")
    try:
        periodic = dart_client.get_disclosure_list(
            samsung["corp_code"], SEARCH_BGN_DE, SEARCH_END_DE, pblntf_ty="A"
        )
    except dart_client.DartApiError as e:
        print(f"실패: [{e.status}] {e.message}")
        return
    print(f"정기공시(A유형) {len(periodic)}건")
    for item in periodic:
        report_nm = item.get("report_nm", "")
        is_periodic_report = any(keyword in report_nm for keyword in _PERIODIC_REPORT_KEYWORDS)
        print(f"  report_nm={report_nm} rcept_dt={item.get('rcept_dt')} 실적보고서={is_periodic_report}")


if __name__ == "__main__":
    main()
