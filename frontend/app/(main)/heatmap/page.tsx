"use client"

import { useState } from "react"
import HeatmapDashboard from "@/components/heatmap/HeatmapDashboard"
import type { HeatmapMarket, HeatmapPeriod } from "@/lib/types/HeatmapType"
import { PageTitle } from "@/components/common"

export default function Page() {
  const [market, setMarket] = useState<HeatmapMarket>("kospi")
  const [period, setPeriod] = useState<HeatmapPeriod>("day")

  return (
    <div className="flex w-full flex-col gap-6 px-0 py-0 md:px-6 md:py-4">
      <PageTitle
        title="시장 자금이 몰리는 섹터 한눈에 보기"
        description="지금 가장 달콤한 수익이 흐르는 섹터와 종목을 열 지도로 실시간 추적합니다."
      />

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
