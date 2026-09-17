"use client"

import { useCallback, useEffect, useState } from "react"
import { HelpCircle, Radio } from "lucide-react"

import { Skeleton } from "@/components/ui"
import { cn } from "@/lib/utils"
import { getSentiment, type SentimentResponse } from "@/lib/api/market"
import {
  getPheromoneSignalLevel,
  pheromoneSignalBarColors,
} from "@/lib/constant/home"
import { useIndicatorSchedule } from "@/hooks/use-indicator-schedule"
import DashboardCard from "./DashboardCard"

const SIGNAL_BAR_HEIGHTS = [12, 20, 28, 36, 44]

function SignalBars({
  filledCount,
  color,
}: {
  filledCount: number
  color: string
}) {
  return (
    <div className="flex items-end justify-center gap-2">
      {SIGNAL_BAR_HEIGHTS.map((height, index) => (
        <span
          key={height}
          className="w-4 rounded-sm transition-colors duration-300"
          style={{
            height,
            backgroundColor: index < filledCount ? color : "#E5E7EB",
          }}
        />
      ))}
    </div>
  )
}

function SignalInfoButton() {
  const [open, setOpen] = useState(false)

  return (
    <div
      className="relative"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        className="flex size-5 items-center justify-center rounded-full text-neutral-400 hover:bg-neutral-100 hover:text-neutral-600"
      >
        <HelpCircle size={16} />
      </button>
      <div
        className={cn(
          "absolute top-full right-0 z-20 mt-2 w-72 rounded-xl border border-line-bg bg-white p-4 text-xs leading-relaxed text-neutral-600 shadow-lg transition-opacity duration-150",
          open ? "opacity-100" : "pointer-events-none opacity-0"
        )}
      >
        <p className="mb-1.5 font-bold text-neutral-800">페로몬 신호 강도란?</p>
        <p className="mb-1.5">
          여러 시장 지표(VIX, 수급 동향, 등락 종목 비율 등)을 종합해, 지금
          시장에 얼마나 강한 움직임 신호가 퍼지고 있는지를 나타낸 자체
          지표입니다.
        </p>
        <p className="mb-1.5">
          신호가 강할수록 변동성이 크고 한 방향으로 자금이 몰리는 힘도 강하다는
          뜻이예요.
        </p>
        <p className="mb-1.5">
          1개: 약함, 2개: 감지됨, 3개 보통, 4개 강함, 5개 매우 강함
        </p>
        <p>
          이 지표는 투자 판단을 위한 참고 자료이며, 매수매도를 권유하는 지표가
          아닙니다.
        </p>
      </div>
    </div>
  )
}

export default function PheromoneSignalCard() {
  const [sentiment, setSentiment] = useState<SentimentResponse | null>(null)
  const [loadError, setLoadError] = useState(false)

  const fetchSentiment = useCallback(async () => {
    try {
      const data = await getSentiment()
      setSentiment(data)
      setLoadError(false)
    } catch (error) {
      console.error("[getSentiment] 실패", error)
      setLoadError(true)
    }
  }, [])

  useEffect(() => {
    fetchSentiment()
  }, [fetchSentiment])

  useIndicatorSchedule(fetchSentiment)

  return (
    <DashboardCard
      icon={<Radio size={16} className="text-point" />}
      title="페로몬 신호 강도"
      action={<SignalInfoButton />}
      className="h-full w-full"
    >
      {!sentiment && loadError ? (
        <div className="flex flex-1 items-center justify-center py-6">
          <p className="text-center text-xs text-neutral-400">
            신호 데이터를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.
          </p>
        </div>
      ) : !sentiment ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 py-1">
          <Skeleton className="h-11 w-full max-w-40" />
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-4 w-full" />
        </div>
      ) : (
        (() => {
          const level = getPheromoneSignalLevel(sentiment.score)
          const color = pheromoneSignalBarColors[level.bars - 1]
          return (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 py-1">
              <SignalBars filledCount={level.bars} color={color} />
              <p className="flex items-baseline gap-1.5">
                <span className="text-3xl font-bold" style={{ color }}>
                  {Math.round(sentiment.score)}
                </span>
                <span className="text-sm font-semibold text-neutral-500">
                  {level.label}
                </span>
              </p>
              <p className="text-xs text-neutral-500">{level.description}</p>
            </div>
          )
        })()
      )}
    </DashboardCard>
  )
}
