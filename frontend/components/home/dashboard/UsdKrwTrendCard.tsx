"use client"

import { useCallback, useEffect, useState } from "react"
import { DollarSign, TrendingDown, TrendingUp } from "lucide-react"
import { format } from "date-fns"
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  Skeleton,
  Tabs,
  TabsList,
  TabsTrigger,
  type ChartConfig,
} from "@/components/ui"
import {
  getExchangeRate,
  type ExchangeRatePeriod,
  type ExchangeRateResponse,
} from "@/lib/api/market"
import { usdKrwRangeLabels, type UsdKrwRange } from "@/lib/constant/home"
import { useIndicatorSchedule } from "@/hooks/use-indicator-schedule"
import DashboardCard from "./DashboardCard"

const chartConfig = {
  value: {
    label: "환율",
    color: "var(--color-decrease)",
  },
} satisfies ChartConfig

const RANGE_ORDER: UsdKrwRange[] = ["day", "week5", "month"]

const RANGE_TO_PERIOD: Record<UsdKrwRange, ExchangeRatePeriod> = {
  day: "today",
  week5: "5d",
  month: "1m",
}

function formatAxisLabel(timestamp: string, range: UsdKrwRange) {
  const date = new Date(timestamp)
  if (range === "day") return format(date, "HH:mm")
  if (range === "week5") return format(date, "M/d")
  return format(date, "M월")
}

export default function UsdKrwTrendCard() {
  const [range, setRange] = useState<UsdKrwRange>("day")
  const [dataByRange, setDataByRange] = useState<
    Partial<Record<UsdKrwRange, ExchangeRateResponse>>
  >({})
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)

  const fetchRange = useCallback(async (targetRange: UsdKrwRange) => {
    setLoading(true)
    setLoadError(false)
    try {
      const data = await getExchangeRate(RANGE_TO_PERIOD[targetRange])
      setDataByRange((prev) => ({ ...prev, [targetRange]: data }))
    } catch (error) {
      console.error("[getExchangeRate] 실패", error)
      setLoadError(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchRange(range)
  }, [range, fetchRange])

  useIndicatorSchedule(() => fetchRange(range))

  const current = dataByRange[range]
  const points = current?.points ?? []
  const values = points.map((point) => point.value)
  const latest = values.at(-1)
  const previous = values.at(-2)
  const change =
    latest !== undefined && previous !== undefined ? latest - previous : 0
  const changeRate =
    latest !== undefined && previous !== undefined && previous !== 0
      ? (change / previous) * 100
      : 0
  const isUp = change >= 0
  const domainPadding =
    values.length > 0
      ? (Math.max(...values) - Math.min(...values)) * 0.2 || 1
      : 1

  return (
    <DashboardCard
      icon={<DollarSign size={16} className="text-point" />}
      title="원/달러 환율 추이"
      className="h-full w-full"
      action={
        <Tabs
          value={range}
          onValueChange={(value) => setRange(value as UsdKrwRange)}
          className="h-5"
        >
          <TabsList variant="line">
            {RANGE_ORDER.map((key) => (
              <TabsTrigger
                key={key}
                value={key}
                className="h-5 cursor-pointer px-2 py-0 text-xs"
              >
                {usdKrwRangeLabels[key]}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      }
    >
      {loading && !current ? (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-8 w-40" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : loadError && !current ? (
        <p className="py-8 text-center text-sm text-neutral-400">
          환율 데이터를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.
        </p>
      ) : points.length === 0 ? (
        <p className="py-8 text-center text-sm text-neutral-400">
          아직 표시할 환율 데이터가 없어요.
        </p>
      ) : (
        <div className="flex flex-col gap-4">
          <p className="flex items-baseline gap-2">
            <span className="text-2xl font-bold">
              {(latest ?? 0).toLocaleString("ko-KR", {
                minimumFractionDigits: 1,
              })}
            </span>
            <span
              className={`inline-flex items-center gap-0.5 text-sm font-semibold ${isUp ? "text-increase" : "text-decrease"}`}
            >
              {isUp ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {Math.abs(change).toFixed(1)} ({Math.abs(changeRate).toFixed(2)}
              %)
            </span>
          </p>

          <ChartContainer
            config={chartConfig}
            className="aspect-auto h-24 w-full"
          >
            <AreaChart
              accessibilityLayer={false}
              data={points}
              margin={{ top: 8, left: 0, right: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="fill-usd-krw" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopColor="var(--color-decrease)"
                    stopOpacity={0.35}
                  />
                  <stop
                    offset="95%"
                    stopColor="var(--color-decrease)"
                    stopOpacity={0.02}
                  />
                </linearGradient>
              </defs>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickLine={false}
                axisLine={false}
                interval={range === "day" ? 2 : 0}
                tickFormatter={(value: string) => formatAxisLabel(value, range)}
                tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
              />
              <YAxis
                hide
                domain={[
                  Math.min(...values) - domainPadding,
                  Math.max(...values) + domainPadding,
                ]}
              />
              <ChartTooltip
                cursor={false}
                content={
                  <ChartTooltipContent
                    indicator="line"
                    labelFormatter={(value) =>
                      formatAxisLabel(value as string, range)
                    }
                  />
                }
              />
              <Area
                dataKey="value"
                type="monotone"
                fill="url(#fill-usd-krw)"
                fillOpacity={1}
                stroke="var(--color-decrease)"
                strokeWidth={2}
                dot={false}
              />
            </AreaChart>
          </ChartContainer>
        </div>
      )}
    </DashboardCard>
  )
}
