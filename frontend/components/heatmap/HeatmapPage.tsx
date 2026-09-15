"use client"

import { useState } from "react"
import {
  AlertCircle,
  ArrowUpRight,
  ChartNoAxesCombined,
  Clock3,
  Flame,
  Info,
  Lightbulb,
  LoaderCircle,
  Newspaper,
  Radio,
  RefreshCw,
  Sparkles,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useHeatmap } from "@/hooks/use-heatmap"
import { formatKoreanAmount } from "@/lib/heatmap-layout"
import type {
  HeatmapMarket,
  HeatmapPeriod,
  HeatmapResponse,
} from "@/lib/types/HeatmapType"
import HeatmapTree from "./HeatmapTree"

const PERIOD_LABELS: Record<HeatmapPeriod, string> = {
  day: "일일",
  week: "주간",
  month: "월간",
}
const PERIOD_DESCRIPTIONS: Record<HeatmapPeriod, string> = {
  day: "전 거래일 종가 대비",
  week: "이번 주 시작 전 종가 대비",
  month: "이번 달 시작 전 종가 대비",
}
const PERIOD_VOLUME_LABELS: Record<HeatmapPeriod, string> = {
  day: "오늘",
  week: "이번 주",
  month: "이번 달",
}
const MARKET_STATUS: Record<HeatmapResponse["market_status"], string> = {
  pre_open: "장 시작 전",
  open: "장중",
  closed: "장 마감",
  holiday: "휴장일",
  unknown: "장 상태 확인 중",
}

function formatTimestamp(value: string | null | undefined, timeOnly = false) {
  if (!value || !Number.isFinite(Date.parse(value))) return "—"
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    ...(timeOnly ? {} : { month: "2-digit", day: "2-digit" }),
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(new Date(value))
}

export default function HeatmapPage() {
  const [market, setMarket] = useState<HeatmapMarket>("kospi")
  const [period, setPeriod] = useState<HeatmapPeriod>("day")

  return (
    <div className="-mx-8 min-w-0 sm:-mx-5 xl:mx-0" data-heatmap-page>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-2">
        <div>
          <div className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold tracking-wide text-point">
            <ChartNoAxesCombined className="size-3.5" /> MARKET HEATMAP
          </div>
          <h1 className="text-2xl font-bold tracking-tight">단물 지도</h1>
          <p className="mt-1.5 text-xs leading-relaxed text-neutral-500">
            시장의 온도와 거래가 모이는 업종을 한눈에 살펴보세요.
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-neutral-100 px-2.5 py-1.5 text-[10px] text-neutral-500">
          <Clock3 className="size-3" /> 정규장 중 10분마다 갱신
        </span>
      </div>

      {/* A new filter owns its own request lifecycle and cannot show the old market. */}
      <HeatmapDashboard
        key={`${market}:${period}`}
        market={market}
        period={period}
        onMarketChange={setMarket}
        onPeriodChange={setPeriod}
      />
    </div>
  )
}

function HeatmapDashboard({
  market,
  period,
  onMarketChange,
  onPeriodChange,
}: {
  market: HeatmapMarket
  period: HeatmapPeriod
  onMarketChange: (market: HeatmapMarket) => void
  onPeriodChange: (period: HeatmapPeriod) => void
}) {
  const { data, isLoading, error, refresh, refreshWaitSeconds } = useHeatmap(
    market,
    period
  )
  const manualRefreshDisabled = isLoading || refreshWaitSeconds > 0
  const hasData = Boolean(
    data?.sectors.some(
      (sector) => sector.stocks.length && sector.market_cap > 0
    )
  )
  const topSector = data?.top_sector
  const collecting = data?.is_refreshing
  const coverage = data?.coverage
  const marketIsOpen = data?.market_status === "open"
  const partial = Boolean(coverage?.missing_stocks)
  const today = new Intl.DateTimeFormat("sv-SE", {
    timeZone: "Asia/Seoul",
  }).format(new Date())
  const volumePeriodLabel =
    data?.as_of_date && data.as_of_date !== today
      ? period === "day"
        ? `${data.as_of_date} 기준`
        : `기준일의 ${PERIOD_LABELS[period]}`
      : PERIOD_VOLUME_LABELS[period]

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center gap-x-3 gap-y-2 rounded-xl border border-red-100 bg-gradient-to-r from-red-50/80 to-white px-4 py-3.5">
        <span className="inline-flex shrink-0 items-center gap-1 rounded-md bg-white px-2 py-1 text-[11px] font-bold text-point ring-1 ring-red-100">
          <Flame className="size-3.5 fill-red-100" /> HOT 1위
        </span>
        <p className="text-xs font-medium text-neutral-600">
          {volumePeriodLabel} 가장 많이 거래된 업종
        </p>
        {topSector ? (
          <>
            <strong className="text-base font-bold text-point">
              {topSector.name}
            </strong>
            <div className="flex flex-wrap items-center gap-2 text-[11px] text-neutral-500 xl:ml-auto">
              <span className="font-semibold text-neutral-700">
                {formatKoreanAmount(topSector.volume, "주")}
              </span>
              <span className="h-3 border-l border-neutral-200" />
              <span>
                {market.toUpperCase()} 거래량의{" "}
                {topSector.volume_share.toFixed(1)}%
              </span>
              {partial && (
                <span className="text-amber-700">· 수집된 종목 기준</span>
              )}
            </div>
          </>
        ) : (
          <span className="text-xs text-neutral-400">
            {isLoading || collecting
              ? "거래량을 집계하고 있어요"
              : "집계 데이터 대기 중"}
          </span>
        )}
      </div>

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2.5">
          <div
            role="group"
            aria-label="시장 선택"
            className="inline-flex gap-1 rounded-lg border border-neutral-200 bg-white p-1 shadow-xs"
          >
            {(["kospi", "kosdaq"] as const).map((value) => (
              <FilterButton
                key={value}
                active={market === value}
                onClick={() => onMarketChange(value)}
              >
                {value.toUpperCase()}
              </FilterButton>
            ))}
          </div>
          <div
            role="group"
            aria-label="기간 선택"
            className="inline-flex gap-1 rounded-lg border border-neutral-200 bg-white p-1 shadow-xs"
          >
            {(["day", "week", "month"] as const).map((value) => (
              <FilterButton
                key={value}
                active={period === value}
                onClick={() => onPeriodChange(value)}
              >
                {PERIOD_LABELS[value]}
              </FilterButton>
            ))}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="flex items-center gap-1.5 text-[11px] text-neutral-500">
            <span
              className={`size-1.5 rounded-full ${marketIsOpen ? "bg-point" : "bg-neutral-400"}`}
            />
            {data ? MARKET_STATUS[data.market_status] : "데이터 확인 중"}
          </span>
          <Button
            size="sm"
            disabled={manualRefreshDisabled}
            onClick={refresh}
            aria-label={
              refreshWaitSeconds > 0
                ? `${refreshWaitSeconds}초 후 수동 업데이트 가능`
                : "최신 히트맵 다시 확인"
            }
            title="수동 업데이트는 1분에 한 번 가능합니다."
            className="bg-point text-[10px] font-bold text-white tabular-nums hover:bg-point/90"
          >
            <RefreshCw className={isLoading ? "animate-spin" : ""} />
            {refreshWaitSeconds > 0
              ? `${refreshWaitSeconds}초 후 UPDATE`
              : "UPDATE"}
          </Button>
        </div>
      </div>

      <div className="mb-3 flex flex-wrap items-center justify-between gap-x-3 gap-y-1 text-[10px] leading-relaxed text-neutral-400">
        <p>
          {market.toUpperCase()} · {PERIOD_LABELS[period]} ·{" "}
          {PERIOD_DESCRIPTIONS[period]}
        </p>
        <p>
          기준일 {data?.as_of_date ?? "—"} <span className="mx-1">/</span> 수집{" "}
          {formatTimestamp(data?.updated_at)} KST
        </p>
      </div>

      {(error ||
        data?.is_stale ||
        data?.message ||
        (data && !marketIsOpen && hasData)) && (
        <div
          role={error ? "alert" : "status"}
          className={`mb-3 flex items-start gap-2 rounded-lg border px-3 py-2.5 text-xs leading-relaxed ${error || data?.is_stale ? "border-amber-200 bg-amber-50 text-amber-800" : "border-neutral-200 bg-neutral-50 text-neutral-500"}`}
        >
          {collecting ? (
            <LoaderCircle className="mt-0.5 size-3.5 shrink-0 animate-spin" />
          ) : (
            <Info className="mt-0.5 size-3.5 shrink-0" />
          )}
          <div>
            {error ? (
              <p>
                {error} {hasData && "마지막으로 수집한 데이터를 표시합니다."}
              </p>
            ) : (
              <p>
                {data?.message ||
                  (data?.is_stale
                    ? "데이터 갱신이 지연되어 마지막 수집값을 표시합니다."
                    : "정규장 외에는 마지막으로 수집한 데이터를 표시합니다.")}
              </p>
            )}
            {collecting && hasData && (
              <p className="mt-0.5">
                새 데이터를 수집 중입니다. 완료되면 자동으로 반영됩니다.
              </p>
            )}
          </div>
        </div>
      )}

      <div className="grid min-w-0 grid-cols-1 items-start gap-4 xl:grid-cols-[minmax(0,1fr)_230px] 2xl:grid-cols-[minmax(0,1fr)_248px]">
        <section aria-label="주식 히트맵" className="min-w-0">
          {hasData && data ? (
            <HeatmapTree sectors={data.sectors} />
          ) : isLoading && !data ? (
            <HeatmapLoading />
          ) : (
            <div className="flex min-h-[530px] flex-col items-center justify-center rounded-xl border border-dashed border-neutral-200 bg-neutral-50/70 px-6 text-center">
              <div
                className={`mb-4 flex size-14 items-center justify-center rounded-2xl ${error ? "bg-amber-50 text-amber-600" : "bg-red-50 text-point"}`}
              >
                {error ? (
                  <AlertCircle className="size-6" />
                ) : collecting ? (
                  <LoaderCircle className="size-6 animate-spin" />
                ) : (
                  <ChartNoAxesCombined className="size-6" />
                )}
              </div>
              <h2 className="text-base font-semibold">
                {error
                  ? "히트맵을 불러오지 못했어요"
                  : collecting
                    ? "시장의 온도를 모으고 있어요"
                    : "아직 표시할 데이터가 없어요"}
              </h2>
              <p className="mt-2 max-w-80 text-xs leading-6 text-neutral-500">
                {error
                  ? "백엔드 연결을 확인한 뒤 다시 시도해 주세요."
                  : collecting
                    ? "첫 수집에는 몇 분이 걸릴 수 있습니다. 수집이 완료되면 히트맵과 거래량 1위 업종이 자동으로 표시됩니다."
                    : data?.message ||
                      "시세가 준비되면 이곳에서 업종별 흐름을 확인할 수 있습니다."}
              </p>
              {coverage && coverage.total_stocks > 0 && (
                <div className="mt-5 w-full max-w-60">
                  <div
                    className="h-1.5 overflow-hidden rounded-full bg-neutral-200"
                    role="progressbar"
                    aria-label="시세 수집 진행률"
                    aria-valuemin={0}
                    aria-valuemax={coverage.total_stocks}
                    aria-valuenow={coverage.priced_stocks}
                  >
                    <div
                      className="h-full rounded-full bg-point transition-all"
                      style={{
                        width: `${Math.min(100, (coverage.priced_stocks / coverage.total_stocks) * 100)}%`,
                      }}
                    />
                  </div>
                  <p className="mt-2 text-[10px] text-neutral-400">
                    {coverage.priced_stocks.toLocaleString("ko-KR")} /{" "}
                    {coverage.total_stocks.toLocaleString("ko-KR")}개 종목
                  </p>
                </div>
              )}
              {error && (
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-5"
                  onClick={refresh}
                  disabled={manualRefreshDisabled}
                  title="수동 업데이트는 1분에 한 번 가능합니다."
                >
                  <RefreshCw />
                  {refreshWaitSeconds > 0
                    ? `${refreshWaitSeconds}초 후 다시 불러오기`
                    : "다시 불러오기"}
                </Button>
              )}
            </div>
          )}

          <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-[10px] text-neutral-500">
            <div
              className="flex flex-wrap items-center gap-2"
              aria-label="등락률 색상 범례"
            >
              <span>등락률</span>
              <div
                className="flex h-2.5 w-28 overflow-hidden rounded-sm"
                aria-hidden="true"
              >
                {["#2563eb", "#395fa9", "#4b5563", "#ab4447", "#ff2a2a"].map(
                  (color) => (
                    <span
                      key={color}
                      className="flex-1"
                      style={{ backgroundColor: color }}
                    />
                  )
                )}
              </div>
              <span>−5% 이하</span>
              <span className="text-neutral-300">/</span>
              <span>0%</span>
              <span className="text-neutral-300">/</span>
              <span>+5% 이상</span>
            </div>
            {coverage && (
              <span>
                전체 시세 수집 {coverage.priced_stocks.toLocaleString("ko-KR")}{" "}
                / {coverage.total_stocks.toLocaleString("ko-KR")}개 ·{" "}
                {partial ? `${coverage.missing_stocks}개 미수집` : "수집 완료"}
              </span>
            )}
          </div>
          <p className="mt-2 text-[10px] leading-5 text-neutral-400">
            기업은 각 업종의 시가총액 상위 순으로 표시하며, 거래량 1위는 전체
            대상 종목 기준입니다. 면적은 시가총액의 제곱근으로 업종·종목별 크기
            차이를 완화했습니다. 실제 시가총액은 종목 상세에서 확인하세요.
            회색은 보합 또는 등락률 미제공입니다.
          </p>
        </section>

        <RecommendationPlaceholder />
      </div>

      <section
        aria-labelledby="heatmap-news-title"
        className="mt-7 border-t border-neutral-200 pt-5"
      >
        <div className="mb-3.5 flex flex-wrap items-center justify-between gap-2">
          <h2
            id="heatmap-news-title"
            className="flex items-center gap-1.5 text-sm font-bold"
          >
            <Flame className="size-4 text-point" />{" "}
            {topSector?.name ? `${topSector.name} · ` : ""}HOT 1위 업종 관련
            뉴스
          </h2>
          <span className="rounded-full bg-neutral-100 px-2 py-1 text-[10px] text-neutral-400">
            준비 중
          </span>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {[1, 2, 3, 4].map((index) => (
            <article
              key={index}
              className="flex min-h-36 flex-col rounded-lg border border-neutral-200 bg-white p-3.5 shadow-xs"
            >
              <div className="mb-3 flex items-center justify-between text-neutral-300">
                <Newspaper className="size-4" />
                <span className="text-[10px] font-medium">NEWS 0{index}</span>
              </div>
              <p className="text-xs font-medium text-neutral-500">
                거래량 1위 업종의
                <br />
                관련 소식을 준비하고 있어요.
              </p>
              <p className="mt-auto pt-4 text-[10px] text-neutral-400">
                뉴스 연동 예정
              </p>
            </article>
          ))}
        </div>
      </section>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-2 text-[10px] text-neutral-400">
        <span>
          시세 제공 한국투자증권 KIS · 거래량은 선택 기간의 거래 주 수 합계
        </span>
        <span>
          {data?.next_update_at
            ? `다음 수집 예정 ${formatTimestamp(data.next_update_at)} KST`
            : "정규장 일정에 맞춰 자동 갱신"}
        </span>
      </div>
    </>
  )
}

function FilterButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={`min-w-11 cursor-pointer rounded-md px-2.5 py-1.5 text-[11px] font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-point ${active ? "bg-point text-white shadow-xs" : "text-neutral-600 hover:bg-neutral-100"}`}
    >
      {children}
    </button>
  )
}

function HeatmapLoading() {
  return (
    <div
      className="relative overflow-hidden rounded-xl border border-neutral-200 bg-neutral-50 p-3"
      role="status"
      aria-label="히트맵 불러오는 중"
    >
      <div className="mb-3 flex justify-between">
        <Skeleton className="h-7 w-28" />
        <Skeleton className="h-7 w-36" />
      </div>
      <div
        className="grid h-[490px] grid-cols-3 gap-2 sm:h-[540px] 2xl:h-[610px]"
        aria-hidden="true"
      >
        {[0, 1, 2].map((column) => (
          <div
            key={column}
            className="grid gap-2"
            style={{ gridTemplateRows: `${3 - column}fr ${column + 1}fr 1fr` }}
          >
            {[0, 1, 2].map((row) => (
              <Skeleton key={row} className="size-full rounded-md" />
            ))}
          </div>
        ))}
      </div>
      <div className="absolute top-1/2 right-4 left-4 flex justify-center">
        <span className="flex items-center gap-2 rounded-full border border-neutral-200 bg-white px-4 py-2 text-xs text-neutral-500 shadow-sm">
          <LoaderCircle className="size-3.5 animate-spin text-point" /> 히트맵을
          불러오고 있어요
        </span>
      </div>
    </div>
  )
}

function RecommendationPlaceholder() {
  return (
    <aside
      aria-labelledby="heatmap-recommendation-title"
      className="rounded-xl border border-neutral-200 bg-white p-4 shadow-xs"
    >
      <div className="flex items-start justify-between gap-2">
        <h2
          id="heatmap-recommendation-title"
          className="text-sm leading-5 font-bold"
        >
          지금 몰리고 있는
          <br className="hidden xl:block" /> 업종을 찾아보세요
        </h2>
        <Radio className="mt-0.5 size-4 shrink-0 text-point" />
      </div>
      <p className="mt-1.5 text-[10px] leading-5 text-neutral-400">
        주목할 업종 3가지를 소개할 예정이에요.
      </p>
      <div className="my-4 flex items-center gap-2">
        <span className="h-px flex-1 bg-neutral-100" />
        <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-1 text-[10px] font-semibold text-point">
          <Sparkles className="size-3" /> 추천 준비 중
        </span>
        <span className="h-px flex-1 bg-neutral-100" />
      </div>
      <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-3 xl:grid-cols-1">
        {[
          "시장이 주목하는 업종",
          "새로운 흐름이 보이는 업종",
          "함께 살펴볼 업종",
        ].map((title, index) => (
          <div
            key={title}
            className="rounded-lg border border-neutral-100 bg-neutral-50/80 p-3"
          >
            <div className="mb-2.5 flex items-center justify-between">
              <span className="flex size-6 items-center justify-center rounded-md bg-white text-[10px] font-bold text-neutral-400 ring-1 ring-neutral-200">
                0{index + 1}
              </span>
              <ArrowUpRight className="size-3.5 text-neutral-300" />
            </div>
            <p className="text-xs font-semibold text-neutral-600">{title}</p>
            <p className="mt-1.5 text-[10px] leading-5 text-neutral-400">
              추천 기능이 준비되면
              <br />
              이곳에서 확인할 수 있어요.
            </p>
            <div className="mt-3 flex gap-1.5">
              <span className="h-4 w-14 rounded bg-neutral-200/60" />
              <span className="h-4 w-10 rounded bg-neutral-200/40" />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 rounded-lg border border-amber-100 bg-amber-50/60 p-3">
        <p className="flex items-center gap-1 text-[11px] font-semibold text-amber-700">
          <Lightbulb className="size-3.5" /> 개미의 관찰 TIP
        </p>
        <p className="mt-1 text-[10px] leading-5 text-neutral-500">
          거래량이 많다고 상승하는 것은 아니에요. 업종의 색과 개별 종목의
          움직임을 함께 살펴보세요.
        </p>
      </div>
    </aside>
  )
}
