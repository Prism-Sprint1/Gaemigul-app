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
    <div className="mb-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2.5">
          <Tabs
            value={market}
            onValueChange={(value) => onMarketChange(value as HeatmapMarket)}
          >
            <TabsList
              aria-label="시장 선택"
              className="h-auto rounded-sm bg-white p-1 shadow-sm"
            >
              {MARKETS.map((value) => (
                <TabsTrigger
                  key={value}
                  value={value}
                  className="min-w-11 rounded-md px-2.5 py-1.5 text-[11px] font-semibold text-neutral-600 data-active:bg-point data-active:text-white data-active:shadow-xs"
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
              className="h-auto rounded-sm bg-white p-1 shadow-sm"
            >
              {PERIODS.map((value) => (
                <TabsTrigger
                  key={value}
                  value={value}
                  className="min-w-11 rounded-md px-2.5 py-1.5 text-[11px] font-semibold text-neutral-600 data-active:bg-point data-active:text-white data-active:shadow-xs"
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
              className="flex items-center gap-1.5 text-[11px] font-semibold text-point tabular-nums"
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
            className="bg-point text-[10px] font-bold text-white tabular-nums hover:bg-point/90 disabled:bg-neutral-300 disabled:text-neutral-500 disabled:opacity-100"
          >
            {marketClosed || isCoolingDown ? (
              <Lock />
            ) : (
              <RefreshCw className={isLoading ? "animate-spin" : ""} />
            )}
            {marketClosed
              ? "UPDATE"
              : isCoolingDown
                ? `${refreshWaitSeconds}초`
                : "UPDATE"}
          </Button>
        </div>
      </div>
      {marketClosed && (
        <p className="mt-2 text-right text-[10px] leading-relaxed text-neutral-400">
          정규장 마감(15:30) 이후에는 자동 갱신과 수동 업데이트가 제공되지
          않습니다. 다음 정규장 시작 후 다시 갱신됩니다.
        </p>
      )}
    </div>
  )
}
