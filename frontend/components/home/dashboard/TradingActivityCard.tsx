"use client"

import { useEffect, useState } from "react"
import { BarChart3 } from "lucide-react"
import { format, subDays } from "date-fns"
import { ko } from "date-fns/locale/ko"
import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ReferenceLine,
  XAxis,
  YAxis,
} from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui"
import { investorFlow, tradingValueDistribution } from "@/lib/constant/home"
import { isAfterIntradayDataRefresh } from "@/lib/market-session"
import DashboardCard from "./DashboardCard"

const volumeChartConfig = {
  value: {
    label: "거래대금",
    color: "var(--color-point)",
  },
} satisfies ChartConfig

const flowChartConfig = {
  value: {
    label: "순매수",
  },
} satisfies ChartConfig

function useIntradayDataBasis() {
  const [basisDate, setBasisDate] = useState<Date | null>(null)

  useEffect(() => {
    const update = () => {
      const now = new Date()
      const isAfterRefresh = isAfterIntradayDataRefresh(
        now.getHours() * 60 + now.getMinutes()
      )
      setBasisDate(isAfterRefresh ? now : subDays(now, 1))
    }
    update()
    const timer = setInterval(update, 30_000)
    return () => clearInterval(timer)
  }, [])

  return basisDate
}

export default function TradingActivityCard() {
  const basisDate = useIntradayDataBasis()
  const basisDateLabel = basisDate ? format(basisDate, "M월d일(EEE)", { locale: ko }) : ""
  const basisLabel = basisDate
    ? `${format(basisDate, "M월d일", { locale: ko })} 15:30 장마감 기준`
    : ""

  return (
    <DashboardCard
      icon={<BarChart3 size={16} className="text-point" />}
      title={
        <>
          시간대별 거래대금 분포
          <span className="text-[11px] font-normal text-neutral-400">
            {basisDateLabel}
          </span>
        </>
      }
      action={
        <span className="text-[11px] text-neutral-400">단위: 억 원</span>
      }
    >
      <ChartContainer config={volumeChartConfig} className="aspect-auto h-32 w-full">
        <BarChart
          accessibilityLayer={false}
          data={tradingValueDistribution}
          margin={{ top: 4, left: 0, right: 0, bottom: 0 }}
        >
          <XAxis
            dataKey="time"
            tickLine={false}
            axisLine={false}
            interval={2}
            tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
          />
          <YAxis hide />
          <ChartTooltip cursor={{ fill: "var(--color-muted)" }} content={<ChartTooltipContent />} />
          <Bar dataKey="value" fill="var(--color-point)" radius={[4, 4, 0, 0]} opacity={0.85} />
        </BarChart>
      </ChartContainer>

      <div className="flex flex-col gap-2 border-t border-neutral-100 pt-4">
        <div className="flex items-center justify-between gap-2">
          <h4 className="text-sm font-bold">투자자별 매매동향</h4>
          <span className="text-[11px] text-neutral-400">{basisLabel}</span>
        </div>
        <ChartContainer config={flowChartConfig} className="aspect-auto h-28 w-full">
          <BarChart
            accessibilityLayer={false}
            data={investorFlow}
            layout="vertical"
            margin={{ top: 0, left: 8, right: 24, bottom: 0 }}
          >
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="investor"
              tickLine={false}
              axisLine={false}
              width={44}
              tick={{ fontSize: 12, fill: "var(--color-foreground)" }}
            />
            <ReferenceLine x={0} stroke="var(--color-border)" />
            <ChartTooltip
              cursor={{ fill: "var(--color-muted)" }}
              content={
                <ChartTooltipContent
                  formatter={(value) => `${Number(value).toLocaleString()}억 원`}
                />
              }
            />
            <Bar dataKey="value" radius={4} barSize={18}>
              {investorFlow.map((item) => (
                <Cell
                  key={item.investor}
                  fill={
                    item.value < 0
                      ? "var(--color-decrease)"
                      : "var(--color-increase)"
                  }
                />
              ))}
              <LabelList
                dataKey="value"
                content={({ x, y, width, height, value }) => {
                  const numValue = Number(value)
                  const cx = Number(x) + Number(width) / 2
                  const cy = Number(y) + Number(height) / 2
                  const label = `${numValue > 0 ? "+" : ""}${numValue.toLocaleString()}`
                  return (
                    <text
                      x={cx}
                      y={cy}
                      fill="#ffffff"
                      fontSize={12}
                      fontWeight={600}
                      textAnchor="middle"
                      dominantBaseline="middle"
                    >
                      {label}
                    </text>
                  )
                }}
              />
            </Bar>
          </BarChart>
        </ChartContainer>
      </div>
    </DashboardCard>
  )
}
