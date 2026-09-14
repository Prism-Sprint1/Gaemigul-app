"use client"

import { Bar, CartesianGrid, ComposedChart, Line, XAxis, YAxis } from "recharts"

import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui"
import type { BriefingCorrelationChart as BriefingCorrelationChartType } from "@/lib/types/BriefingType"

const chartConfig = {
  fxRate: { label: "원/달러 환율(KRW)", color: "#94a3b8" },
  netSell: { label: "외인 누적 순매도(조원)", color: "#ef4444" },
}

type BriefingCorrelationChartProps = {
  chart: BriefingCorrelationChartType
}

export default function BriefingCorrelationChart({
  chart,
}: BriefingCorrelationChartProps) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-neutral-200 bg-white p-4">
      <p className="text-xs font-semibold text-neutral-600">{chart.title}</p>

      <ChartContainer config={chartConfig} className="aspect-auto h-56 w-full">
        <ComposedChart
          data={chart.data}
          margin={{ left: -20, right: 8, top: 8, bottom: 0 }}
        >
          <CartesianGrid vertical={false} stroke="#f1f5f9" />
          <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
          <YAxis
            yAxisId="left"
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 11 }}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 11 }}
          />
          <ChartTooltip content={<ChartTooltipContent />} />
          <Bar
            yAxisId="left"
            dataKey="fxRate"
            fill="var(--color-fxRate)"
            radius={[4, 4, 0, 0]}
            barSize={28}
          />
          <Line
            yAxisId="right"
            dataKey="netSell"
            type="monotone"
            stroke="var(--color-netSell)"
            strokeWidth={2.5}
            dot={{ r: 3 }}
          />
        </ComposedChart>
      </ChartContainer>

      <div className="flex flex-col gap-1 border-t border-neutral-100 pt-2 text-[11px] text-neutral-400 sm:flex-row sm:items-center sm:justify-between">
        <span>{chart.footnoteLeft}</span>
        <span>{chart.footnoteRight}</span>
      </div>
    </div>
  )
}
