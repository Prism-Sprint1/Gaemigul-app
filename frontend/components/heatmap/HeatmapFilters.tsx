"use client"

import { useEffect, useState } from "react"
import { Clock3, Lock, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  formatCountdown,
  isAfterMarketClose,
  PERIOD_LABELS,
} from "@/lib/heatmap-format"
import type { HeatmapMarket, HeatmapPeriod } from "@/lib/types/HeatmapType"

const MARKETS = ["kospi", "kosdaq"] as const
const PERIODS = ["day", "week", "month"] as const

export default function HeatmapFilters({
  market,
  period,
  onMarketChange,
  onPeriodChange,
  nextUpdateAt,
  manualRefreshDisabled,
  isLoading,
  refreshWaitSeconds,
  onRefresh,
}: {
  market: HeatmapMarket
  period: HeatmapPeriod
  onMarketChange: (market: HeatmapMarket) => void
  onPeriodChange: (period: HeatmapPeriod) => void
  nextUpdateAt: string | null | undefined
  manualRefreshDisabled: boolean
  isLoading: boolean
  refreshWaitSeconds: number
  onRefresh: () => void
}) {
  const isCoolingDown = refreshWaitSeconds > 0
  const [marketClosed, setMarketClosed] = useState(isAfterMarketClose)
  const [remainingMs, setRemainingMs] = useState(() =>
    nextUpdateAt ? Date.parse(nextUpdateAt) - Date.now() : null
  )

  useEffect(() => {
    function tick() {
      setMarketClosed(isAfterMarketClose())
      setRemainingMs(
        nextUpdateAt ? Date.parse(nextUpdateAt) - Date.now() : null
      )
    }
    tick()
    const timer = setInterval(tick, 1000)
    return () => clearInterval(timer)
  }, [nextUpdateAt])

  const updateDisabled = manualRefreshDisabled || marketClosed

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2.5">
          <Tabs
            value={market}
            onValueChange={(value) => onMarketChange(value as HeatmapMarket)}
          >
            <TabsList
              aria-label="시장 선택"
              className="h-auto rounded-xl bg-heatmap-canvas p-1"
            >
              {MARKETS.map((value) => (
                <TabsTrigger
                  key={value}
                  value={value}
                  className="min-h-9 min-w-12 rounded-lg px-3 py-2 text-xs font-semibold text-slate-500 data-active:bg-heatmap-soft data-active:text-heatmap-accent data-active:shadow-sm"
                >
                  {value.toUpperCase()}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
          <Tabs
            value={period}
            onValueChange={(value) => onPeriodChange(value as HeatmapPeriod)}
          >
            <TabsList
              aria-label="기간 선택"
              className="h-auto rounded-xl bg-heatmap-canvas p-1"
            >
              {PERIODS.map((value) => (
                <TabsTrigger
                  key={value}
                  value={value}
                  className="min-h-9 min-w-12 rounded-lg px-3 py-2 text-xs font-semibold text-slate-500 data-active:bg-heatmap-soft data-active:text-heatmap-accent data-active:shadow-sm"
                >
                  {PERIOD_LABELS[value]}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          {!marketClosed && remainingMs !== null && (
            <span
              className="flex items-center gap-1.5 text-xs font-medium text-slate-500 tabular-nums"
              aria-label="다음 자동 갱신까지 남은 시간"
            >
              <Clock3 className="size-3.5" />
              다음 갱신까지 {formatCountdown(remainingMs)}
            </span>
          )}
          <Button
            size="sm"
            disabled={updateDisabled}
            onClick={onRefresh}
            aria-label={
              marketClosed
                ? "장 마감 이후에는 업데이트할 수 없습니다"
                : isCoolingDown
                  ? `${refreshWaitSeconds}초 후 수동 업데이트 가능`
                  : "최신 히트맵 다시 확인"
            }
            title={
              marketClosed
                ? "정규장 마감(15:30) 이후에는 업데이트할 수 없습니다."
                : "수동 업데이트는 1분에 한 번 가능합니다."
            }
            className="h-10 rounded-lg bg-slate-900 px-3 text-xs font-semibold text-white tabular-nums hover:bg-slate-700 disabled:bg-slate-100 disabled:text-slate-500 disabled:opacity-100"
          >
            {marketClosed || isCoolingDown ? (
              <Lock />
            ) : (
              <RefreshCw
                className={isLoading ? "motion-safe:animate-spin" : ""}
              />
            )}
            {marketClosed
              ? "장 마감"
              : isCoolingDown
                ? `${refreshWaitSeconds}초`
                : "새로고침"}
          </Button>
        </div>
      </div>
      {marketClosed && (
        <p className="mt-3 text-xs leading-5 text-slate-500">
          장 마감 이후에는 마지막 수집 시세를 표시합니다. 다음 정규장에
          갱신됩니다.
        </p>
      )}
    </div>
  )
}
