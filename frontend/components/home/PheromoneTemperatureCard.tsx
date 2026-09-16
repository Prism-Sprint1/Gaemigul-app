import { TrendingDown } from "lucide-react"

// import { Card, CardContent } from "@/components/ui"
import { pheromoneTemperature } from "@/lib/constant/home"

export default function PheromoneTemperatureCard() {
  const {
    value,
    status,
    statusEn,
    description,
    vixValue,
    vixChange,
    fiveDayAverage,
    scale,
    maxScale,
  } = pheromoneTemperature

  const pointerPercent = Math.min(100, Math.max(0, (value / maxScale) * 100))

  return (
    <div className="rounded-none py-0">
      <div className="flex flex-col gap-4 px-0">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <p className="flex items-baseline gap-2 text-base font-bold">
            페로몬 온도
            <span className="text-2xl font-bold text-point">
              {value.toFixed(2)}
            </span>
            <span className="text-sm font-semibold text-neutral-400">
              ({statusEn})
            </span>
          </p>
          <p className="text-xs text-neutral-500">
            VIX 지수 {vixValue.toFixed(2)} (
            <span className="inline-flex items-center gap-0.5 text-decrease">
              <TrendingDown size={12} />
              {Math.abs(vixChange).toFixed(2)}
            </span>
            ) · 5일 평균 온도 {fiveDayAverage.toFixed(1)}
          </p>
        </div>

        <div className="flex flex-col gap-2">
          <div className="relative h-2 w-full rounded-full bg-linear-[90deg,#4A90D926_0%,#6FCF9726_33%,#F0A63E26_66%,#FF2A2A26_100%]">
            <div
              className="absolute top-1/2 size-4 -translate-y-1/2 rounded-full border-2 border-point bg-white shadow"
              style={{ left: `calc(${pointerPercent}% - 8px)` }}
            />
          </div>
          <div className="relative flex text-[11px] text-neutral-400">
            {scale.map((point) => (
              <span
                key={point.value}
                className="absolute -translate-x-1/2 first:translate-x-0 last:-translate-x-full"
                style={{
                  left: `${Math.min(100, (point.value / maxScale) * 100)}%`,
                }}
              >
                {point.value}
                {point.value === scale.at(-1)?.value ? "+" : ""} ({point.label})
              </span>
            ))}
          </div>
        </div>
        <p className="mt-3 text-xs text-neutral-500">
          {status} 등급 · {description}
        </p>
      </div>
    </div>
  )
}
