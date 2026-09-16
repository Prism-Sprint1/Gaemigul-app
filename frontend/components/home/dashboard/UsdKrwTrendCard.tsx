"use client"

import { DollarSign, TrendingDown, TrendingUp } from "lucide-react"
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui"
import { usdKrwTrend } from "@/lib/constant/home"
import DashboardCard from "./DashboardCard"

const chartConfig = {
  value: {
    label: "환율",
    color: "var(--color-decrease)",
  },
} satisfies ChartConfig

export default function UsdKrwTrendCard() {
  const { current, change, changeRate, series } = usdKrwTrend
  const isUp = change >= 0
  const values = series.map((point) => point.value)
  const domainPadding = (Math.max(...values) - Math.min(...values)) * 0.2 || 1

  return (
    <DashboardCard
      icon={<DollarSign size={16} className="text-point" />}
      title="원/달러 환율 추이"
    >
      <div className="flex flex-col gap-4">
        <p className="flex items-baseline gap-2">
          <span className="text-2xl font-bold">
            {current.toLocaleString("ko-KR", { minimumFractionDigits: 1 })}
          </span>
          <span
            className={`inline-flex items-center gap-0.5 text-sm font-semibold ${isUp ? "text-increase" : "text-decrease"}`}
          >
            {isUp ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            {Math.abs(change).toFixed(1)} ({Math.abs(changeRate).toFixed(2)}%)
          </span>
        </p>

        <ChartContainer config={chartConfig} className="aspect-auto h-44 w-full">
          <AreaChart data={series} margin={{ top: 8, left: 0, right: 0, bottom: 0 }}>
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
              dataKey="time"
              tickLine={false}
              axisLine={false}
              interval={2}
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
              content={<ChartTooltipContent indicator="line" />}
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
    </DashboardCard>
  )
}
