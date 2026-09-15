"use client"

import { cn } from "@/lib/utils"
import type { NewsItem } from "@/app/(main)/calendar/news-data"
import { CategoryBar } from "./category-bar"
import { RegionBadge } from "./region-badge"

export function EventRow({
  item,
  colorActive,
  onClick,
}: {
  item: NewsItem
  colorActive: boolean
  onClick: () => void
}) {
  const isSpecial = item.highlight === "special"
  return (
    <button
      type="button"
      onClick={onClick}
      title={item.title}
      className="flex w-full cursor-pointer items-center gap-1 truncate text-left text-[10px] transition-colors hover:text-primary sm:text-[11px]"
    >
      <CategoryBar category={item.category} colorActive={colorActive} />
      <RegionBadge region={item.region} />
      <span className={cn("truncate", isSpecial && "font-semibold")}>
        {isSpecial && <span className="text-emerald-600">주요 </span>}
        {item.title}
      </span>
    </button>
  )
}
