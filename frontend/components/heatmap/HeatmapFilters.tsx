"use client"

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { PERIOD_LABELS } from "@/lib/heatmap-format"
import type { HeatmapMarket, HeatmapPeriod } from "@/lib/types/HeatmapType"

const MARKETS = ["kospi", "kosdaq"] as const
const PERIODS = ["day", "week", "month"] as const

export default function HeatmapFilters({
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
  return (
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
  )
}
