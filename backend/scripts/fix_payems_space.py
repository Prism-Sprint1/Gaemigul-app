# fix_payems_space.py
# 57번 항목(scripts/expand_payems_thousands.py)에서 PAYEMS previous/actual을 실제 인원
# 수로 풀어 쓸 때 "158861000 명"처럼 숫자와 "명" 사이에 공백을 넣었는데, 사용자가 공백
# 없이 "158861000명"으로 고쳐달라고 요청해서 이미 저장된 행의 공백만 제거한다. 값 자체는
# 전혀 바꾸지 않는다 - 문자열에서 " 명"을 "명"으로 치환하는 것뿐이다.
#
# 실행: backend/ 디렉토리에서 `uv run python scripts/fix_payems_space.py`

import asyncio

from sqlalchemy import text

from backend.core.database import async_session


async def main() -> None:
    async with async_session() as session:
        result = await session.execute(
            text(
                """
                UPDATE calendar_events
                SET previous = REPLACE(previous, ' 명', '명'),
                    actual = REPLACE(actual, ' 명', '명')
                WHERE id LIKE 'fred-PAYEMS-%'
                  AND (previous LIKE '% 명' OR actual LIKE '% 명')
                """
            )
        )
        await session.commit()
        print(f"=== PAYEMS ' 명' -> '명' 공백 제거 완료: {result.rowcount}건 ===")


if __name__ == "__main__":
    asyncio.run(main())
