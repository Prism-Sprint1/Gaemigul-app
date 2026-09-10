"use client"

import {
  Card,
  CardContent,
  ChartContainer,
  Skeleton,
  type ChartConfig,
} from "@/components/ui"

import { Area, AreaChart } from "recharts"

import { Marquee } from "@/components/animations/marquee"

import {
  getTimelineIndicators,
  type MarketIndicatorItem,
} from "@/lib/api/indicator"

import { useIndicatorSchedule } from "@/hooks/use-indicator-schedule"

import { useCallback, useEffect, useState } from "react"

import {
  uptrendChartData,
  downtrendChartData,
  flatChartData,
} from "@/lib/constant/indicatorChartData"

const chartConfig = {
  desktop: {
    label: "Desktop",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig

const IndexDataCard = ({
  code,
  name,
  price,
  change_rate,
}: MarketIndicatorItem) => {
  const direction: "up" | "down" | "flat" =
    change_rate > 0 ? "up" : change_rate < 0 ? "down" : "flat"
  const value = price.toLocaleString("ko-KR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  const change = `${change_rate > 0 ? "+" : ""}${change_rate.toFixed(2)}%`
  const chartColor = {
    up: "var(--color-increase)",
    down: "var(--color-decrease)",
    flat: "var(--muted-foreground)",
  }[direction]
  const changeTextClass = {
    up: "text-increase",
    down: "text-decrease",
    flat: "text-neutral-500",
  }[direction]
  const chartData = {
    up: uptrendChartData,
    down: downtrendChartData,
    flat: flatChartData,
  }[direction]
  const gradientId = `fill-${code}`
  return (
    <Card className="h-full rounded-lg border-border bg-card px-3.5 py-2.25 shadow-none">
      <CardContent className="flex min-w-42 gap-3 px-0">
        <div>
          <p className="flex items-center gap-1.25 text-[12px] font-medium text-neutral-600">
            {name}
            <span className={`text-[12px] ${changeTextClass}`}>{change}</span>
          </p>
          <strong className="text-base font-semibold">{value}</strong>
        </div>
        <ChartContainer
          config={chartConfig}
          className="h-10 w-20 **:outline-none [&_.recharts-cartesian-grid]:hidden"
        >
          <AreaChart
            data={chartData}
            margin={{
              top: 2,
              bottom: 2,
              right: 2,
            }}
          >
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={chartColor} stopOpacity={0.8} />
                <stop offset="95%" stopColor={chartColor} stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <Area
              dataKey="desktop"
              type="linear"
              fill={`url(#${gradientId})`}
              fillOpacity={0.4}
              stroke={chartColor}
              stackId="a"
              dot={false}
              activeDot={false}
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}

const IndexDataCardSkeleton = () => (
  <Card className="h-full rounded-lg border-border bg-card px-3.5 py-2.25 shadow-none">
    <CardContent className="flex min-w-42 gap-3 px-0">
      <div className="flex flex-col gap-1.5">
        <Skeleton className="h-3.5 w-24" />
        <Skeleton className="h-5 w-20" />
      </div>
      <Skeleton className="h-10 w-20" />
    </CardContent>
  </Card>
)

const SKELETON_KEYS = ["s1", "s2", "s3", "s4", "s5", "s6"]

export default function TestimonialMarqueeDemo() {
  const [items, setItems] = useState<MarketIndicatorItem[]>([])

  const fetchTimelineIndicators = useCallback(async () => {
    try {
      const data = await getTimelineIndicators()
      setItems(data.items)
    } catch (error) {
      console.error("[getTimelineIndicators] 실패", error)
    }
  }, [])

  // 최초 진입 시 1회 실행
  useEffect(() => {
    fetchTimelineIndicators()
  }, [fetchTimelineIndicators])

  // 정시 기준 30분 간격마다 실행
  useIndicatorSchedule(fetchTimelineIndicators)

  const isLoading = items.length === 0

  return (
    <div className="relative flex w-full flex-1 flex-col items-center justify-center overflow-hidden">
      <Marquee pauseOnHover className="[--duration:30s]">
        {isLoading
          ? SKELETON_KEYS.map((key) => <IndexDataCardSkeleton key={key} />)
          : items.map((item) => <IndexDataCard key={item.code} {...item} />)}
      </Marquee>
      <div className="pointer-events-none absolute inset-y-0 left-0 w-1/4 bg-gradient-to-r from-background"></div>
      <div className="pointer-events-none absolute inset-y-0 right-0 w-1/4 bg-gradient-to-l from-background"></div>
    </div>
  )
}
