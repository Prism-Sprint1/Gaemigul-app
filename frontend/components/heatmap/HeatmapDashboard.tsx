"use client"

import { AlertCircle, ChevronDown, Clock3, Database } from "lucide-react"
import { useHeatmap } from "@/hooks/use-heatmap"
import {
  formatTimestamp,
  getVolumePeriodLabel,
  MARKET_STATUS,
  PERIOD_DESCRIPTIONS,
} from "@/lib/heatmap-format"
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
  const warning =
    error ||
    (data?.is_stale
      ? "최신 시세를 확인하지 못해 마지막으로 수집한 데이터를 표시합니다."
      : partial
        ? "일부 종목의 시세를 수집 중입니다. 순위와 표시 범위가 달라질 수 있습니다."
        : null)

  return (
    <div className="space-y-5 text-slate-900">
      <HeatmapTopSectorBanner
        market={market}
        topSector={topSector}
        periodLabel={periodLabel}
        partial={partial}
        isLoading={isLoading}
        collecting={collecting}
      />
      <div className="rounded-2xl border border-heatmap-border bg-white px-4 py-4 shadow-sm sm:px-5">
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
        <details className="group mt-2">
          <summary className="ml-auto flex min-h-6 w-fit cursor-pointer list-none items-center gap-1 rounded text-[11px] text-slate-500 outline-offset-2 hover:text-slate-800 focus-visible:outline-slate-700 [&::-webkit-details-marker]:hidden">
            데이터 기준
            <ChevronDown
              className="size-3.5 group-open:rotate-180"
              aria-hidden="true"
            />
          </summary>
          <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-heatmap-border/60 pt-2 text-[11px] leading-5 text-slate-500">
            <span className="inline-flex items-center gap-1.5">
              <Database className="size-3.5" aria-hidden="true" /> 한국투자증권
              시세
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Clock3 className="size-3.5" aria-hidden="true" /> 수집{" "}
              <time dateTime={data?.updated_at ?? undefined}>
                {formatTimestamp(data?.updated_at)}
              </time>{" "}
              · 한국시간
            </span>
            <span>
              {data ? MARKET_STATUS[data.market_status] : "시세 확인 중"}
              {collecting ? " · 수집 중" : ""} · 장중 10분 간격
            </span>
            <span className="sm:ml-auto">{PERIOD_DESCRIPTIONS[period]}</span>
          </div>
          {data?.as_of_date && (
            <p className="mt-1 text-[11px] text-slate-500">
              시세 기준일 {data.as_of_date}
            </p>
          )}
        </details>
      </div>
      {warning && (
        <div
          role="status"
          className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-900"
        >
          <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <p>{warning}</p>
        </div>
      )}
      <div className="grid min-w-0 grid-cols-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_300px] 2xl:grid-cols-[minmax(0,1fr)_320px]">
        <section
          aria-label="주식 히트맵"
          className="min-w-0 rounded-2xl border border-heatmap-border bg-white p-4 shadow-heatmap-card sm:p-5"
        >
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
