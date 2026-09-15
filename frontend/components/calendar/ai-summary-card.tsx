"use client"

import { cn } from "@/lib/utils"
import { CAT, type NewsItem } from "@/app/(main)/calendar/news-data"

/** 이번 주 실제 일정 목록을 받아 카테고리별 요약 형태로 보여주는 카드 (실제 AI 생성 로직은 아직 없음 — 백엔드가 만든 요약 문구를 그대로 사용) */
export function AiSummaryCard({
  items,
  onOpenItem,
}: {
  items: NewsItem[]
  onOpenItem: (item: NewsItem) => void
}) {
  return (
    <div className="rounded-xl border bg-primary/5 p-3 sm:p-4">
      <div className="mb-2 flex items-center justify-start gap-1.5 truncate text-left text-xs font-semibold whitespace-nowrap text-primary">
        <span className="shrink-0">✨</span>
        이번주 AI 요약
      </div>
      {items.length === 0 ? (
        <p className="text-[11px] text-muted-foreground">
          이번 주에는 예정된 일정이 없습니다.
        </p>
      ) : (
        <ul className="flex flex-col gap-2.5">
          {items.map((n) => (
            <li key={n.id}>
              {/* 요약이 길면 카드 안에서 다 안 보이므로, 클릭하면 상세 팝업으로 전체 내용을 볼 수 있게 한다 */}
              <button
                type="button"
                onClick={() => onOpenItem(n)}
                className="flex w-full cursor-pointer flex-col gap-0.5 rounded-md text-left transition-colors hover:bg-primary/10"
              >
                <div className="flex items-center gap-1.5 text-[12px] font-semibold text-foreground">
                  <span
                    className={cn(
                      "size-1.5 shrink-0 rounded-full",
                      CAT[n.category].dot
                    )}
                  />
                  <span className="truncate">{n.title}</span>
                </div>
                <p className="line-clamp-2 pl-3 text-[11px] leading-snug break-keep text-muted-foreground">
                  {n.summary}
                </p>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
