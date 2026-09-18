"use client"

import { useState } from "react"
import HeatmapDashboard from "@/components/heatmap/HeatmapDashboard"
import type { HeatmapMarket, HeatmapPeriod } from "@/lib/types/HeatmapType"

export default function Page() {
  const [market, setMarket] = useState<HeatmapMarket>("kospi")
  const [period, setPeriod] = useState<HeatmapPeriod>("day")

  return (
    <div className="flex w-full flex-col gap-5 bg-white px-3 py-5 sm:px-5 md:px-6 md:py-6">
      {/* A new filter owns its own request lifecycle and cannot show the old market. */}
      <HeatmapDashboard
        key={`${market}:${period}`}
        market={market}
        period={period}
        onMarketChange={setMarket}
        onPeriodChange={setPeriod}
      />
    </div>
  )
}
