import { Flame } from "lucide-react"
import { Badge } from "@/components/ui"
import { formatKoreanAmount } from "@/lib/heatmap-layout"
import type { HeatmapMarket, HeatmapResponse } from "@/lib/types/HeatmapType"

export default function HeatmapTopSectorBanner({
  market,
  topSector,
  volumePeriodLabel,
  partial,
  isLoading,
  collecting,
}: {
  market: HeatmapMarket
  topSector: HeatmapResponse["top_sector"] | undefined
  volumePeriodLabel: string
  partial: boolean
  isLoading: boolean
  collecting: boolean | undefined
}) {
  return (
    <div className="mb-5 flex flex-wrap items-center gap-x-3 gap-y-2 rounded-sm border border-line-bg bg-white px-2 py-2 shadow-sm">
      <Badge
        variant="outline"
        className="gap-1 rounded-sm border-point bg-white px-2 py-1 text-[11px] font-bold text-point"
      >
        🔥 HOT 1위
      </Badge>
      <p className="text-xs font-medium text-point2">
        {volumePeriodLabel} 개미가 가장 많이 몰린 단물 섹터는?
      </p>
      {topSector ? (
        <>
          <strong className="text-sm font-bold text-point">
            {topSector.name}
          </strong>
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-neutral-500 xl:ml-auto">
            <span className="font-semibold text-neutral-700">
              {formatKoreanAmount(topSector.volume, "주")}
            </span>
            <span className="h-3 border-l border-neutral-200" />
            <span>
              {market.toUpperCase()} 거래량의{" "}
              {topSector.volume_share.toFixed(1)}%
            </span>
            {partial && (
              <Badge
                variant="outline"
                className="border-amber-200 text-amber-700"
              >
                수집된 종목 기준
              </Badge>
            )}
          </div>
        </>
      ) : (
        <span className="text-xs text-neutral-400">
          {isLoading || collecting
            ? "거래량을 집계하고 있어요"
            : "집계 데이터 대기 중"}
        </span>
      )}
    </div>
  )
}
