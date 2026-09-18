# expand_payems_thousands.py
# calendar_events에 이미 저장된 PAYEMS(미국 비농업 고용) 행의 previous/actual을
# "158861천 명"(축약값) → "158861000 명"(실제 인원 수) 형태로 백필한다. 값을 추정하거나
# 바꾸는 게 아니라 "천 명" 단위 배수를 실제 숫자로 풀어서 다시 쓰는 것뿐이다(158861 * 1000
# = 158861000, 수학적으로 동일한 값) - services/calendar.py의 _expand_payems_thousands와
# 정확히 같은 규칙을 새로 들어오는 행뿐 아니라 이미 저장된 행에도 적용한다.
#
# id가 "fred-PAYEMS-"로 시작하는 행만 대상으로 한다 - 다른 지표(GDP/CPI 등)는 건드리지 않는다.
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/expand_payems_thousands.py`

import asyncio
import re

from sqlalchemy import text

from backend.core.database import async_session

_THOUSANDS_PATTERN = re.compile(r"^(-?\d+(?:\.\d+)?)천 명$")


def _expand(value: str | None) -> str | None:
    if value is None:
        return None
    match = _THOUSANDS_PATTERN.match(value)
    if not match:
        return None  # 이미 변환됐거나 예상 못한 형식 - 건드리지 않는다
    return f"{round(float(match.group(1)) * 1000)} 명"


async def main() -> None:
    async with async_session() as session:
        result = await session.execute(
            text(
                """
                SELECT id, previous, actual FROM calendar_events
                WHERE id LIKE 'fred-PAYEMS-%'
                """
            )
        )
        rows = result.mappings().all()

        updated = 0
        skipped = 0
        for row in rows:
            new_previous = _expand(row["previous"])
            new_actual = _expand(row["actual"])
            # previous/actual 둘 다 이미 변환된 형식이면(재실행 시) 건드리지 않는다
            if row["previous"] is not None and new_previous is None and row["actual"] is not None and new_actual is None:
                skipped += 1
                continue
            await session.execute(
                text(
                    """
                    UPDATE calendar_events
                    SET previous = COALESCE(:new_previous, previous),
                        actual = COALESCE(:new_actual, actual)
                    WHERE id = :id
                    """
                ),
                {
                    "id": row["id"],
                    "new_previous": new_previous,
                    "new_actual": new_actual,
                },
            )
            updated += 1

        await session.commit()
        print(f"=== PAYEMS 천 명 -> 실제 인원 수 백필 완료: {updated}건 변경, {skipped}건 스킵(이미 변환됨) ===")


if __name__ == "__main__":
    asyncio.run(main())
