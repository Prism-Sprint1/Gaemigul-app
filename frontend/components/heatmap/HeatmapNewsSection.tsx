import Link from "next/link"
import { Flame, Newspaper } from "lucide-react"
import { Badge } from "@/components/ui"

export default function HeatmapNewsSection({
  topSectorName,
}: {
  topSectorName: string | undefined
}) {
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
          🔥
          {topSectorName ? `${topSectorName} · ` : ""}HOT 1위 업종 관련 뉴스
        </h2>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {[1, 2, 3, 4].map((index) => (
          <Link
            key={index}
            href="#"
            aria-disabled="true"
            onClick={(event) => event.preventDefault()}
            className="flex h-max flex-col rounded-sm border border-neutral-200 bg-white p-3.5 shadow-xs transition-shadow hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-point"
          >
            <p className="text-xs font-medium text-neutral-500">
              거래량 1위 업종의
              <br />
              관련 소식을 준비하고 있어요.
            </p>
            <p className="mt-auto pt-4 text-[10px] text-neutral-400">NAVER</p>
          </Link>
        ))}
      </div>
    </section>
  )
}
