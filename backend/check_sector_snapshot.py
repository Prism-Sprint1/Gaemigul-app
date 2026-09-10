# check_sector_snapshot.py
# 업종 등락률이 시간대별로 바뀌는지 확인하는 일회성 검증 스크립트
#
# 확인하려는 것: 정규장(09:00~15:30) 밖에서도 업종 등락률이 갱신되는가
#   - 갱신되지 않으면 07:30/08:30/17:30/20:00 슬롯은 주도 섹터를 새로 뽑을 필요가 없다
#   - 프리마켓(NXT 08:00~08:50)은 그 전후를 나눠 찍어야 판별된다
#
# 두 가지를 같이 본다
#   1. 업종 시간별지수의 마지막 체결 시각 - 이 값 하나로 바로 판별된다.
#      17:35에 돌렸는데 마지막 시각이 15:30이면 그 사이에 지수가 안 움직였다는 뜻이다
#   2. 업종 21개의 등락률 - 이전 실행분과 비교해서 값이 실제로 달라졌는지 교차 확인용
#
# 사용법 - 아래 시각에 한 번씩 실행한다
#   uv run python check_sector_snapshot.py A_마감      (15:35)
#   uv run python check_sector_snapshot.py B_애프터    (17:35)
#   uv run python check_sector_snapshot.py C_개장전    (다음날 07:35)
#   uv run python check_sector_snapshot.py D_프리마켓  (다음날 08:35)
#
# 결과는 .cache/sector_snapshots.json에 쌓이고, 실행할 때마다 이전 기록과 비교해서 보여준다
# 검증이 끝나면 이 파일과 위 json은 지워도 된다

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "src")

from backend.core import kis_client
from backend.domain.timeline.services.leading_sector_service import KOSPI_SECTOR_CODES

_SNAPSHOT_PATH = Path(__file__).resolve().parent / ".cache" / "sector_snapshots.json"
_KST = ZoneInfo("Asia/Seoul")


# 지금 시점의 업종 등락률을 {업종코드: 등락률} 형태로 가져온다
def take_snapshot() -> dict[str, float]:
    rows = kis_client.get_index_category_price("K").get("output2") or []
    return {row["bstp_cls_code"]: float(row["bstp_nmix_prdy_ctrt"]) for row in rows if row["bstp_cls_code"] in KOSPI_SECTOR_CODES}


# 코스피 지수가 마지막으로 체결된 시각을 가져온다 ("122900" 형태, 데이터가 없으면 None)
# 이 API는 지금 시점부터 거슬러 올라가며 최근 100틱만 준다. 과거 특정 시각은 지정할 수 없다
def take_last_tick_hour() -> str | None:
    rows = kis_client.get_index_tick_price("0001").get("output") or []
    return rows[0]["bsop_hour"] if rows else None


# 두 스냅샷을 비교해서 값이 달라진 업종 수를 센다
def compare(old: dict, new: dict) -> None:
    changed = [code for code in new if code in old and old[code] != new[code]]
    if not changed:
        print("    -> 값이 하나도 안 바뀜 (이 시간대에는 갱신되지 않는다는 뜻)")
        return

    print(f"    -> {len(changed)}개 업종의 값이 바뀜 (이 시간대에도 갱신된다는 뜻)")
    for code in changed[:5]:
        print(f"       {KOSPI_SECTOR_CODES[code]}: {old[code]:+.2f}% -> {new[code]:+.2f}%")


def main() -> None:
    if len(sys.argv) < 2:
        print("라벨을 넣어주세요. 예: uv run python check_sector_snapshot.py A_마감")
        raise SystemExit(1)

    label = sys.argv[1]
    saved = json.loads(_SNAPSHOT_PATH.read_text()) if _SNAPSHOT_PATH.exists() else {}

    snapshot = take_snapshot()
    last_tick = take_last_tick_hour()
    now = datetime.now(_KST)
    print(f"[{label}] {now:%Y-%m-%d %H:%M} 기준 / 업종 {len(snapshot)}개 수집")

    if last_tick is None:
        print("    지수 체결 데이터 없음 -> 이 시간대에는 업종 지수가 아예 안 돈다")
    else:
        print(f"    코스피 지수 마지막 체결 시각: {last_tick[:2]}:{last_tick[2:4]}:{last_tick[4:6]}")

    for old_label, old in saved.items():
        print(f"  vs [{old_label}] ({old['taken_at']})")
        compare(old["rates"], snapshot)

    saved[label] = {"taken_at": now.strftime("%Y-%m-%d %H:%M"), "last_tick": last_tick, "rates": snapshot}
    _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SNAPSHOT_PATH.write_text(json.dumps(saved, ensure_ascii=False, indent=2))
    print(f"  저장됨 -> {_SNAPSHOT_PATH}")


if __name__ == "__main__":
    main()
