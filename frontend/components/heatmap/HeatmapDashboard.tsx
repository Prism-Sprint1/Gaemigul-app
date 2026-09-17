"use client"

import { useHeatmap } from "@/hooks/use-heatmap"
import { getVolumePeriodLabel } from "@/lib/heatmap-format"
import type { HeatmapMarket, HeatmapPeriod } from "@/lib/types/HeatmapType"
import HeatmapTopSectorBanner from "./HeatmapTopSectorBanner"
import HeatmapFilters from "./HeatmapFilters"
import HeatmapEmptyState from "./HeatmapEmptyState"
import HeatmapLoadingSkeleton from "./HeatmapLoadingSkeleton"
import { HeatmapLegendFootnote } from "./HeatmapLegend"
import HeatmapNewsSection from "./HeatmapNewsSection"
import HeatmapRecommendation from "./HeatmapRecommendation"
import HeatmapTree from "./HeatmapTree"

export default function HeatmapDashboard({
  market,
  period,
  onMarketChange,
  onPeriodChange,
}: {
  market: HeatmapMarket
  period: HeatmapPeriod
  onMarketChange: (market: HeatmapMarket) => void
  onPeriodChange: (period: HeatmapPeriod) => void
}) {
  const { data, isLoading, error, refresh, refreshWaitSeconds } = useHeatmap(
    market,
    period
  )
  const manualRefreshDisabled = isLoading || refreshWaitSeconds > 0
  const hasData = Boolean(
    data?.sectors.some(
      (sector) => sector.stocks.length && sector.market_cap > 0
    )
  )
  const topSector = data?.top_sector
  const collecting = data?.is_refreshing
  const coverage = data?.coverage
  const partial = Boolean(coverage?.missing_stocks)
  const periodLabel = getVolumePeriodLabel(period, data?.as_of_date)

  return (
    <div className="bg-ant-bg p-5">
      <HeatmapTopSectorBanner
        market={market}
        topSector={topSector}
        periodLabel={periodLabel}
        partial={partial}
        isLoading={isLoading}
        collecting={collecting}
      />

      <HeatmapFilters
        market={market}
        period={period}
        onMarketChange={onMarketChange}
        onPeriodChange={onPeriodChange}
        nextUpdateAt={data?.next_update_at}
        manualRefreshDisabled={manualRefreshDisabled}
        isLoading={isLoading}
        refreshWaitSeconds={refreshWaitSeconds}
        onRefresh={refresh}
      />

      <div className="grid min-w-0 grid-cols-1 items-start gap-4 xl:grid-cols-[minmax(0,1fr)_230px] 2xl:grid-cols-[minmax(0,1fr)_320px]">
        <section aria-label="주식 히트맵" className="min-w-0">
          {hasData && data ? (
            <HeatmapTree sectors={data.sectors} />
          ) : isLoading && !data ? (
            <HeatmapLoadingSkeleton />
          ) : (
            <HeatmapEmptyState
              error={error}
              collecting={collecting}
              message={data?.message}
              coverage={coverage}
              manualRefreshDisabled={manualRefreshDisabled}
              refreshWaitSeconds={refreshWaitSeconds}
              onRefresh={refresh}
            />
          )}

          <HeatmapLegendFootnote />
        </section>

        <HeatmapRecommendation
          topSectorName={topSector?.name}
          relatedSectors={data?.related_sectors ?? []}
          isLoading={isLoading || Boolean(collecting)}
        />
      </div>

      <HeatmapNewsSection market={market} period={period} snapshot={data} />
    </div>
  )
}
