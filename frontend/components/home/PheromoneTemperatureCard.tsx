"use client"

import { useCallback, useEffect, useState } from "react"
import { TrendingDown, TrendingUp } from "lucide-react"

import { Skeleton } from "@/components/ui"
import { getVix, type VixResponse } from "@/lib/api/market"
import {
  getPheromoneLevel,
  pheromoneMaxScale,
  pheromoneScale,
} from "@/lib/constant/home"
import { useIndicatorSchedule } from "@/hooks/use-indicator-schedule"

export default function PheromoneTemperatureCard() {
  const [vix, setVix] = useState<VixResponse | null>(null)

  const fetchVix = useCallback(async () => {
    try {
      const data = await getVix()
      setVix(data)
    } catch (error) {
      console.error("[getVix] 실패", error)
    }
  }, [])

  useEffect(() => {
    fetchVix()
  }, [fetchVix])

  useIndicatorSchedule(fetchVix)

  if (!vix) {
    return (
      <div className="flex flex-col gap-4 py-0">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-2 w-full rounded-full" />
        <Skeleton className="h-4 w-full" />
      </div>
    )
  }

  const level = getPheromoneLevel(vix.value)
  const pointerPercent = Math.min(
    100,
    Math.max(0, (vix.value / pheromoneMaxScale) * 100)
  )
  const isDown = vix.change_value < 0

  return (
    <div className="rounded-none py-0">
      <div className="flex flex-col gap-4 px-0">
        <p className="flex items-baseline gap-2 text-base font-bold">
          페로몬 온도
          <span className="text-2xl font-bold" style={{ color: level.color }}>
            {vix.value.toFixed(2)}
          </span>
          <span className="text-sm font-semibold text-neutral-400">
            ({level.statusEn})
          </span>
        </p>

        <div className="flex flex-col gap-2">
          <div className="relative h-2 w-full rounded-full bg-linear-[90deg,#4A90D926_0%,#6FCF9726_33%,#F0A63E26_66%,#FF2A2A26_100%]">
            <div
              className="absolute top-1/2 size-4 -translate-y-1/2 rounded-full border-2 bg-white shadow transition-[left,border-color] duration-500"
              style={{
                left: `calc(${pointerPercent}% - 8px)`,
                borderColor: level.color,
              }}
            />
          </div>
          <div className="relative flex text-[11px] text-neutral-400">
            {pheromoneScale.map((point) => (
              <span
                key={point.value}
                className="absolute -translate-x-1/2 first:translate-x-0 last:-translate-x-full"
                style={{
                  left: `${Math.min(100, (point.value / pheromoneMaxScale) * 100)}%`,
                }}
              >
                {point.value}
                {point.value === pheromoneScale.at(-1)?.value ? "+" : ""} (
                {point.label})
              </span>
            ))}
          </div>
        </div>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-neutral-500">
          <p>
            {level.status} 등급 · {level.description}
          </p>
          <p className="shrink-0">
            VIX 지수 {vix.value.toFixed(2)} (
            <span
              className={`inline-flex items-center gap-0.5 ${isDown ? "text-decrease" : "text-increase"}`}
            >
              {isDown ? (
                <TrendingDown size={12} />
              ) : (
                <TrendingUp size={12} />
              )}
              {Math.abs(vix.change_value).toFixed(2)}
            </span>
            )
          </p>
        </div>
      </div>
    </div>
  )
}
