# add_actual_label_column.py
# calendar_events에 actual_label 컬럼을 추가하고, 이미 저장돼 있는 배당/공모주/DART 실적
# 행에 라벨을 백필한다. 이 세 유형은 category/title만으로 라벨이 결정적으로 정해지므로
# (services/calendar.py의 _dividend_event_from_kis/_ipo_event_from_kis/_dart_earnings_event
# 참고) 원본 API를 다시 호출하지 않고 SQL UPDATE로 채운다. 새로 들어오는 행은 이제
# 각 ingest 함수가 actual_label을 직접 채워서 저장하므로 이 백필은 1회성이다.
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/add_actual_label_column.py`
# 전제: calendar_events 테이블이 Supabase에 이미 생성되어 있어야 한다(마이그레이션 도구 없이
# calendar_weekly_summaries 테이블을 만들 때와 동일하게 raw SQL을 직접 실행한다).

import asyncio

from sqlalchemy import text

from backend.core.database import async_session


async def main() -> None:
    async with async_session() as session:
        await session.execute(
            text("ALTER TABLE calendar_events ADD COLUMN IF NOT EXISTS actual_label text")
        )

        dividend = await session.execute(
            text(
                """
                UPDATE calendar_events SET actual_label = '주당'
                WHERE category = 'dividend' AND actual IS NOT NULL AND actual_label IS NULL
                """
            )
        )
        earnings = await session.execute(
            text(
                """
                UPDATE calendar_events SET actual_label = '매출액'
                WHERE category = 'earnings' AND title LIKE '%실적 발표'
                  AND actual IS NOT NULL AND actual_label IS NULL
                """
            )
        )
        ipo = await session.execute(
            text(
                """
                UPDATE calendar_events SET actual_label = '공모가'
                WHERE category = 'macro' AND title LIKE '%공모주 청약'
                  AND actual IS NOT NULL AND actual_label IS NULL
                """
            )
        )

        await session.commit()

        print("=== actual_label 컬럼 추가 + 백필 완료 ===")
        print(f"  배당(dividend) 라벨 채움: {dividend.rowcount}건")
        print(f"  DART 실적(earnings) 라벨 채움: {earnings.rowcount}건")
        print(f"  공모주(IPO) 라벨 채움: {ipo.rowcount}건")


if __name__ == "__main__":
    asyncio.run(main())
