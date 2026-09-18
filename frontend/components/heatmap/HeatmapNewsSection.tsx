"use client"

import { ArrowUpRight, Newspaper } from "lucide-react"
import { useHeatmapNews } from "@/hooks/use-heatmap-news"
import { formatTimestamp } from "@/lib/heatmap-format"
import type {
  HeatmapMarket,
  HeatmapPeriod,
  HeatmapResponse,
} from "@/lib/types/HeatmapType"

export default function HeatmapNewsSection({
  market,
  period,
  snapshot,
}: {
  market: HeatmapMarket
  period: HeatmapPeriod
  snapshot: HeatmapResponse | null
}) {
  const { data, error, isLoading } = useHeatmapNews(market, period, snapshot)
  const topSectorName = snapshot?.top_sector?.name
  const items = data?.items ?? []
  return (
    <section
      aria-labelledby="heatmap-news-title"
      className="rounded-2xl border border-heatmap-border bg-white p-5 shadow-heatmap-card sm:p-6"
    >
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3 border-b border-heatmap-border pb-4">
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-500">
            <Newspaper className="size-4" aria-hidden="true" /> 관련 경제뉴스
          </div>
          <h2
            id="heatmap-news-title"
            className="text-lg font-bold tracking-tight text-slate-900"
          >
            상승률 1위 섹터 뉴스
          </h2>
          <p className="mt-1.5 text-xs leading-5 text-slate-500">
            {topSectorName
              ? `${topSectorName} 관련 최신 기사`
              : "상승률 1위 섹터의 최신 기사"}{" "}
            · 발행 시각순 최대 4건
          </p>
        </div>
        {topSectorName && (
          <span className="rounded-full border border-heatmap-border bg-heatmap-panel px-3 py-1.5 text-xs font-semibold text-slate-600">
            {topSectorName}
          </span>
        )}
      </div>
      {data?.is_stale && (
        <p
          role="status"
          className="mb-4 rounded-lg bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800"
        >
          최신 뉴스 연결을 확인 중입니다. 이전에 수집한 기사를 표시합니다.
        </p>
      )}
      {items.length ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {items.map((item, index) => (
            <a
              key={item.url}
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={`${item.title} (새 탭)`}
              className="group flex min-w-0 flex-col rounded-xl border border-heatmap-border bg-white p-4 transition-colors hover:border-slate-300 hover:bg-heatmap-panel focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-900 sm:min-h-56"
            >
              <div className="mb-4 flex items-center justify-between gap-2">
                <span className="truncate text-xs font-semibold text-slate-600">
                  {item.source || "언론사 미제공"}
                </span>
                <span
                  aria-hidden="true"
                  className="text-xs text-slate-400 tabular-nums"
                >
                  {String(index + 1).padStart(2, "0")}
                </span>
              </div>
              <h3 className="line-clamp-4 text-[15px] leading-6 font-semibold tracking-tight break-keep text-slate-900">
                {item.title}
              </h3>
              {item.summary && (
                <p className="mt-2 line-clamp-2 text-xs leading-5 text-slate-500">
                  {item.summary}
                </p>
              )}
              <div className="mt-auto flex items-center justify-between gap-2 pt-5">
                <time
                  dateTime={item.published_at ?? undefined}
                  className="text-[11px] text-slate-500 tabular-nums"
                >
                  {formatTimestamp(item.published_at)}
                </time>
                <ArrowUpRight
                  className="size-4 shrink-0 text-slate-400 transition-colors group-hover:text-slate-900"
                  aria-hidden="true"
                />
              </div>
            </a>
          ))}
        </div>
      ) : isLoading ? (
        <div
          role="status"
          aria-label="관련 뉴스 불러오는 중"
          className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4"
        >
          {Array.from({ length: 4 }, (_, index) => (
            <div
              key={index}
              className="min-h-48 rounded-xl border border-heatmap-border p-4 motion-safe:animate-pulse"
            >
              <div className="h-3 w-1/3 rounded bg-slate-100" />
              <div className="mt-6 h-4 w-full rounded bg-slate-100" />
              <div className="mt-3 h-4 w-5/6 rounded bg-slate-100" />
              <div className="mt-7 h-3 w-1/2 rounded bg-slate-100" />
            </div>
          ))}
          <span className="sr-only">관련 뉴스를 불러오고 있어요.</span>
        </div>
      ) : (
        <div
          role="status"
          className="flex min-h-40 items-center justify-center gap-3 rounded-xl bg-slate-50 px-5 py-8 text-sm leading-6 text-slate-500"
        >
          <Newspaper className="size-5 shrink-0" aria-hidden="true" />
          <p>
            {error ??
              data?.message ??
              (topSectorName
                ? "확인할 수 있는 최신 관련 기사가 없습니다."
                : "상승률 1위 업종이 집계되면 최신 뉴스를 보여드려요.")}
          </p>
        </div>
      )}
      <div className="mt-4 flex flex-wrap justify-between gap-2 text-[11px] leading-5 text-slate-500">
        <p>Google 뉴스 RSS · 기사 선택 시 원문 링크를 새 탭에서 엽니다.</p>
        <p>
          {data?.updated_at
            ? `수집 ${formatTimestamp(data.updated_at)} · 한국시간`
            : "발행 시각은 한국시간 기준"}
        </p>
      </div>
      {items.length > 0 && data?.message && !data.is_stale && (
        <p role="status" className="mt-1 text-xs text-slate-500">
          {data.message}
        </p>
      )}
    </section>
  )
}
