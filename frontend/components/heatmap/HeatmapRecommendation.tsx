import { Lightbulb } from "lucide-react"
import { formatChange } from "@/lib/heatmap-layout"
import type { HeatmapRelatedSector } from "@/lib/types/HeatmapType"

const ASSOCIATION_EMOJIS = ["🏠", "🍲", "👕"]

function changeColor(rate: number | null) {
  return rate === null || rate === 0
    ? "text-neutral-500"
    : rate > 0
      ? "text-point"
      : "text-blue-600"
}

export default function HeatmapRecommendation({
  topSectorName,
  relatedSectors,
  isLoading,
}: {
  topSectorName: string | undefined
  relatedSectors: HeatmapRelatedSector[]
  isLoading: boolean
}) {
  return (
    <aside
      aria-labelledby="heatmap-recommendation-title"
      className="rounded-xl border border-neutral-200 bg-white p-4 shadow-xs"
    >
      <h2
        id="heatmap-recommendation-title"
        className="text-sm leading-5 font-bold"
      >
        지금 몰리고 있는 섹터 의식주!
      </h2>
      <p className="mt-1.5 text-[10px] leading-5 text-neutral-500">
        상승률 1위 업종에서 이어지는 산업과 대표 기업
      </p>

      <div className="my-4 h-px bg-neutral-100" />
      <div className="rounded-full bg-point px-4 py-2.5 text-center text-sm font-bold text-white shadow-sm">
        {topSectorName ?? "상승률 집계 중"}
      </div>
      <div className="mx-auto h-3 w-px border-l-2 border-dashed border-point/40" />

      {relatedSectors.length ? (
        <div className="flex flex-col gap-2.5">
          {relatedSectors.slice(0, 3).map((sector, index) => (
            <article
              key={sector.code}
              className="rounded-lg border border-neutral-100 bg-neutral-50/80 p-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-1.5">
                <h3 className="text-xs font-bold text-neutral-800">
                  {ASSOCIATION_EMOJIS[index]} {sector.name}
                </h3>
                <span
                  className={`text-[11px] font-semibold tabular-nums ${changeColor(sector.change_rate)}`}
                >
                  {formatChange(sector.change_rate)}
                </span>
              </div>
              <p className="mt-2 text-[10px] font-medium text-neutral-500">
                {sector.relationship_kind === "market_trend"
                  ? "시장 흐름 참고"
                  : "산업 연관"}
              </p>
              <p className="mt-1 text-[11px] leading-5 text-neutral-600">
                {sector.reason}
              </p>
              <ul
                className="mt-2.5 space-y-1.5"
                aria-label={`${sector.name} 대표 기업`}
              >
                {sector.stocks.slice(0, 2).map((stock) => (
                  <li
                    key={stock.code}
                    className="flex items-start justify-between gap-2 rounded-md border border-neutral-200 bg-white px-2.5 py-2"
                  >
                    <span className="min-w-0 text-[11px] font-semibold text-neutral-700">
                      {stock.name}
                      <span className="mt-0.5 block text-[9px] font-normal text-neutral-400">
                        {stock.code}
                      </span>
                    </span>
                    <span
                      className={`shrink-0 pt-0.5 text-[10px] tabular-nums ${changeColor(stock.change_rate)}`}
                    >
                      {stock.change_rate === null
                        ? "—"
                        : formatChange(stock.change_rate)}
                    </span>
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      ) : (
        <p
          role="status"
          className="rounded-lg bg-neutral-50 px-3 py-5 text-xs leading-6 text-neutral-500"
        >
          {isLoading
            ? "연관 업종과 대표 기업을 확인하고 있어요."
            : "현재 데이터에서 확인할 수 있는 연관 업종이 없습니다."}
        </p>
      )}

      <div className="mt-3 rounded-lg border border-amber-100 bg-amber-50/60 p-3">
        <p className="flex items-center gap-1 text-[11px] font-semibold text-amber-700">
          <Lightbulb className="size-3.5" /> 개미 연상 TIP
        </p>
        <p className="mt-1 text-[11px] leading-5 text-neutral-600">
          산업 간 연결 이유와 선택한 기간의 등락률을 함께 살펴보세요. 대표
          기업은 각 업종의 시가총액 상위 2개입니다.
        </p>
      </div>
    </aside>
  )
}
