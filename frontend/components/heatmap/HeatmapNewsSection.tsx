"use client"

import { ExternalLink, Newspaper } from "lucide-react"
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
      className="mt-7 border-t border-neutral-200 pt-5"
    >
      <div className="mb-3.5 flex flex-wrap items-center justify-between gap-2">
        <h2
          id="heatmap-news-title"
          className="flex items-center gap-1.5 text-sm font-bold"
        >
          🔥 {topSectorName ? `${topSectorName} · ` : ""}HOT 1위 업종 최신
          경제뉴스
        </h2>
        <p className="text-[10px] text-neutral-500">
          Google 뉴스 RSS · 최신순 최대 4건
          {data?.is_stale && " · 저장된 기사 표시 중"}
        </p>
      </div>

      {items.length ? (
        <>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {items.map((item) => (
              <a
                key={item.url}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={`${item.title} (새 탭)`}
                className="group flex min-h-44 flex-col rounded-sm border border-neutral-200 bg-white p-3.5 shadow-xs transition-shadow hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-point"
              >
                <h3 className="line-clamp-3 text-xs leading-6 font-semibold text-neutral-800 group-hover:text-point">
                  {item.title}
                </h3>
                {item.summary && (
                  <p className="mt-2 line-clamp-2 text-[11px] leading-5 text-neutral-500">
                    {item.summary}
                  </p>
                )}
                <div className="mt-auto flex flex-wrap items-end justify-between gap-2 pt-4 text-[10px] text-neutral-500">
                  <span>{item.source || "언론사 미제공"}</span>
                  <span className="flex items-center gap-1">
                    <time dateTime={item.published_at ?? undefined}>
                      {formatTimestamp(item.published_at)}
                    </time>
                    <ExternalLink className="size-3" aria-hidden="true" />
                  </span>
                </div>
              </a>
            ))}
          </div>
          {data?.message && (
            <p role="status" className="mt-2 text-[11px] text-neutral-500">
              {data.message}
            </p>
          )}
        </>
      ) : isLoading ? (
        <div
          aria-label="관련 뉴스 불러오는 중"
          role="status"
          className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4"
        >
          {Array.from({ length: 4 }, (_, index) => (
            <div
              key={index}
              className="min-h-36 animate-pulse rounded-sm border border-neutral-200 bg-white p-3.5"
            >
              <div className="h-3 w-5/6 rounded bg-neutral-100" />
              <div className="mt-3 h-3 w-full rounded bg-neutral-100" />
              <div className="mt-3 h-3 w-2/3 rounded bg-neutral-100" />
            </div>
          ))}
          <span className="sr-only">관련 뉴스를 불러오고 있어요.</span>
        </div>
      ) : (
        <div
          role="status"
          className="flex min-h-32 items-center justify-center gap-2 rounded-sm border border-neutral-200 bg-white p-5 text-xs leading-6 text-neutral-500"
        >
          <Newspaper className="size-4 shrink-0" aria-hidden="true" />
          <p>
            {error ??
              data?.message ??
              (topSectorName
                ? "확인할 수 있는 최신 관련 기사가 없습니다."
                : "상승률 1위 업종이 집계되면 최신 뉴스를 보여드려요.")}
          </p>
        </div>
      )}
    </section>
  )
}
