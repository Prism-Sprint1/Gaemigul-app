"use client"

import {
  Card,
  CardContent,
  ChartContainer,
  type ChartConfig,
} from "@/components/ui"

import { Area, AreaChart } from "recharts"

import { Marquee } from "@/components/animations/marquee"

const indexData = [
  {
    name: "KOSPI123",
    value: "2,684.50",
    change: "+1.42%",
    isIncrease: false,
  },
  {
    name: "KOSPI456",
    value: "2,684.50",
    change: "-1.42%",
    isIncrease: true,
  },
  {
    name: "KOSPIaa",
    value: "2,684.50",
    change: "+1.42%",
    isIncrease: false,
  },
  {
    name: "KOSPIss",
    value: "2,684.50",
    change: "-1.42%",
    isIncrease: true,
  },
  {
    name: "KOSPIdd",
    value: "2,684.50",
    change: "+1.42%",
    isIncrease: true,
  },
  {
    name: "KOSPIcc",
    value: "2,684.50",
    change: "-1.42%",
    isIncrease: false,
  },
]

const chartData = [
  { desktop: 186 },
  { desktop: 305 },
  { desktop: 237 },
  { desktop: 73 },
  { desktop: 209 },
  { desktop: 214 },
]

const chartConfig = {
  desktop: {
    label: "Desktop",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig

const firstRow = indexData.slice(0, indexData.length / 2)

const IndexDataCard = ({
  name,
  value,
  change,
  isIncrease,
}: {
  name: string
  value: string
  change: string
  isIncrease: boolean
}) => {
  const chartColor = isIncrease
    ? "var(--color-increase)"
    : "var(--color-decrease)"
  const gradientId = `fill-${name}`
  return (
    <Card className="h-full rounded-lg border-border bg-card px-3.5 py-2.25 shadow-none">
      <CardContent className="flex min-w-42 gap-3 px-0">
        <div>
          <p className="flex items-center gap-1.25 text-[12px] font-medium text-neutral-600">
            {name}
            <span
              className={`text-[12px] ${isIncrease ? "text-increase" : "text-decrease"}`}
            >
              {change}
            </span>
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

export default function TestimonialMarqueeDemo() {
  return (
    <div className="relative flex w-full flex-1 flex-col items-center justify-center overflow-hidden">
      <Marquee pauseOnHover className="[--duration:30s]">
        {firstRow.map((index) => (
          <IndexDataCard key={index.name} {...index} />
        ))}
      </Marquee>
      <div className="pointer-events-none absolute inset-y-0 left-0 w-1/4 bg-gradient-to-r from-background"></div>
      <div className="pointer-events-none absolute inset-y-0 right-0 w-1/4 bg-gradient-to-l from-background"></div>
    </div>
  )
}
