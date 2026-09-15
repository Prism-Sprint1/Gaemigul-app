"use client"

import { cn } from "@/lib/utils"
import { CAT, type NewsItem } from "@/app/(main)/calendar/news-data"

/** 카테고리 색 바 — 기본은 연회색, 서브 카테고리 필터가 켜져 있을 때만 해당 카테고리 색으로 표시 */
export function CategoryBar({
  category,
  colorActive,
}: {
  category: NewsItem["category"]
  colorActive: boolean
}) {
  return (
    <span
      className={cn(
        "h-3 w-0.5 shrink-0 rounded-full",
        colorActive ? CAT[category].dot : "bg-muted-foreground/25"
      )}
    />
  )
}
