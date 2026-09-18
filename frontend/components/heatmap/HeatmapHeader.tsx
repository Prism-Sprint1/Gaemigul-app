"use client"

import { useEffect, useRef, useState } from "react"
import { ChevronDown, Clock3, Lock, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  formatCountdown,
  formatTimestamp,
  isAfterMarketClose,
  MARKET_STATUS,
  PERIOD_DESCRIPTIONS,
} from "@/lib/heatmap-format"
import type { HeatmapPeriod, HeatmapResponse } from "@/lib/types/HeatmapType"

export default function HeatmapHeader({
  data,
  period,
  manualRefreshDisabled,
  isLoading,
  refreshWaitSeconds,
  onRefresh,
}: {
  data: HeatmapResponse | null
  period: HeatmapPeriod
  manualRefreshDisabled: boolean
  isLoading: boolean
  refreshWaitSeconds: number
  onRefresh: () => void
}) {
  const criteriaRef = useRef<HTMLDetailsElement>(null)
  const nextUpdateAt = data?.next_update_at
  const isCoolingDown = refreshWaitSeconds > 0
  const [marketClosed, setMarketClosed] = useState(isAfterMarketClose)
  const [remainingMs, setRemainingMs] = useState(() =>
    nextUpdateAt ? Date.parse(nextUpdateAt) - Date.now() : null
  )

  useEffect(() => {
    function tick() {
      setMarketClosed(isAfterMarketClose())
      setRemainingMs(
        nextUpdateAt ? Date.parse(nextUpdateAt) - Date.now() : null
      )
    }
    tick()
    const timer = setInterval(tick, 1000)
    return () => clearInterval(timer)
  }, [nextUpdateAt])

  useEffect(() => {
    function closeOutside(event: PointerEvent) {
      const details = criteriaRef.current
      if (
        details?.open &&
        event.target instanceof Node &&
        !details.contains(event.target)
      )
        details.open = false
    }
    document.addEventListener("pointerdown", closeOutside)
    return () => document.removeEventListener("pointerdown", closeOutside)
  }, [])

  return (
    <header className="border-b border-line-bg pb-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="shrink-0 text-lg leading-none font-bold sm:text-xl lg:text-2xl">
          단물지도
        </h1>
        <div className="ml-auto flex items-center gap-1.5 sm:gap-3">
          {!marketClosed &&
            remainingMs !== null &&
            Number.isFinite(remainingMs) && (
              <span
                className="inline-flex items-center gap-1 text-[10px] font-medium whitespace-nowrap text-slate-500 tabular-nums sm:text-xs"
                aria-label={`다음 자동 갱신까지 ${formatCountdown(remainingMs)}`}
                title="다음 자동 갱신까지 남은 시간"
              >
                <Clock3
                  className="size-3 shrink-0 sm:size-3.5"
                  aria-hidden="true"
                />
                <span className="hidden md:inline">다음 갱신</span>
                {formatCountdown(remainingMs)}
              </span>
            )}
          <Button
            size="sm"
            disabled={manualRefreshDisabled || marketClosed}
            onClick={onRefresh}
            aria-label={
              marketClosed
                ? "장 마감 이후에는 업데이트할 수 없습니다"
                : isCoolingDown
                  ? `${refreshWaitSeconds}초 후 수동 업데이트 가능`
                  : "최신 히트맵 다시 확인"
            }
            title={
              marketClosed
                ? "정규장 마감(15:30) 이후에는 업데이트할 수 없습니다."
                : isCoolingDown
                  ? `${refreshWaitSeconds}초 후 수동 업데이트 가능`
                  : "수동 업데이트는 1분에 한 번 가능합니다."
            }
            className="size-9 shrink-0 rounded-lg bg-slate-900 px-0 text-xs font-semibold text-white tabular-nums hover:bg-slate-700 disabled:bg-slate-100 disabled:text-slate-500 disabled:opacity-100 sm:h-10 sm:w-auto sm:px-3"
          >
            {marketClosed || isCoolingDown ? (
              <Lock aria-hidden="true" />
            ) : (
              <RefreshCw
                aria-hidden="true"
                className={isLoading ? "motion-safe:animate-spin" : ""}
              />
            )}
            <span className="hidden sm:inline">
              {marketClosed
                ? "장 마감"
                : isCoolingDown
                  ? `${refreshWaitSeconds}초`
                  : "새로고침"}
            </span>
          </Button>
          <details
            ref={criteriaRef}
            className="group relative"
            onKeyDown={(event) => {
              if (event.key === "Escape") {
                event.currentTarget.open = false
                event.currentTarget.querySelector("summary")?.focus()
              }
            }}
          >
            <summary className="flex min-h-8 cursor-pointer list-none items-center gap-1 rounded px-1 text-[11px] whitespace-nowrap text-slate-500 outline-offset-2 hover:text-slate-800 focus-visible:outline-slate-700 [&::-webkit-details-marker]:hidden">
              <span>
                <span className="hidden sm:inline">데이터 </span>기준
              </span>
              <ChevronDown
                className="size-3.5 group-open:rotate-180"
                aria-hidden="true"
              />
            </summary>
            <div className="absolute top-full right-0 z-30 mt-2 w-72 max-w-[calc(100vw-4rem)] rounded-xl border border-heatmap-border bg-white p-4 shadow-lg">
              <p className="mb-3 text-xs font-semibold text-slate-800">
                데이터 기준
              </p>
              <dl className="space-y-2 text-[11px] leading-5 text-slate-600">
                <div className="flex justify-between gap-3">
                  <dt className="shrink-0 text-slate-500">시세 출처</dt>
                  <dd className="text-right">한국투자증권</dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="shrink-0 text-slate-500">수집 시각</dt>
                  <dd className="text-right">
                    <time dateTime={data?.updated_at ?? undefined}>
                      {formatTimestamp(data?.updated_at)}
                    </time>{" "}
                    · 한국시간
                  </dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="shrink-0 text-slate-500">시세 기준일</dt>
                  <dd>{data?.as_of_date ?? "—"}</dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="shrink-0 text-slate-500">시장 상태</dt>
                  <dd className="text-right">
                    {data ? MARKET_STATUS[data.market_status] : "시세 확인 중"}
                    {data?.is_refreshing ? " · 수집 중" : ""}
                  </dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="shrink-0 text-slate-500">갱신 주기</dt>
                  <dd>장중 10분 간격</dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="shrink-0 text-slate-500">등락률 기준</dt>
                  <dd className="text-right">{PERIOD_DESCRIPTIONS[period]}</dd>
                </div>
              </dl>
              {marketClosed && (
                <p className="mt-3 border-t border-heatmap-border pt-3 text-[11px] leading-5 text-slate-500">
                  장 마감 이후에는 마지막 수집 시세를 표시합니다. 다음 정규장에
                  갱신됩니다.
                </p>
              )}
            </div>
          </details>
        </div>
      </div>
      <p className="mt-2 truncate text-[10px] text-muted-foreground sm:text-xs">
        시장의 온도를 한눈에. 상승률부터 연관 산업, 최신 뉴스까지 함께
        살펴보세요.
      </p>
    </header>
  )
}
