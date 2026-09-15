"use client"

import { cn } from "@/lib/utils"
import {
  CAT,
  CATEGORY_GROUPS,
  type Category,
  type CategoryGroupId,
} from "@/app/(main)/calendar/news-data"
import {
  groupSegBtn,
  segBtn,
  type GroupFilter,
  type RegionFilter,
  type ViewMode,
} from "@/lib/calendar"

export function FilterBar({
  groupFilter,
  onSelectGroup,
  regionFilter,
  onSetRegionFilter,
  viewMode,
  onSetViewMode,
  subCategories,
  categorySet,
  onToggleCategory,
}: {
  groupFilter: GroupFilter
  onSelectGroup: (g: GroupFilter) => void
  regionFilter: RegionFilter
  onSetRegionFilter: (r: RegionFilter) => void
  viewMode: ViewMode
  onSetViewMode: (v: ViewMode) => void
  subCategories: Category[]
  categorySet: Set<Category>
  onToggleCategory: (c: Category) => void
}) {
  return (
    <div className="flex flex-col gap-3 rounded-2xl lg:sticky lg:top-18.75 lg:z-10 lg:-mx-5 lg:bg-card lg:px-5 lg:pt-4 lg:pb-3">
      <div className="flex flex-nowrap items-center gap-1">
        <div className="flex flex-1 gap-1 rounded-lg bg-muted p-1 text-xs lg:flex-none lg:shrink-0">
          <button
            type="button"
            onClick={() => onSelectGroup("all")}
            className={groupSegBtn(groupFilter === "all")}
          >
            전체
          </button>
          {(Object.keys(CATEGORY_GROUPS) as CategoryGroupId[]).map((g) => (
            <button
              key={g}
              type="button"
              onClick={() => onSelectGroup(g)}
              className={groupSegBtn(groupFilter === g)}
            >
              {CATEGORY_GROUPS[g].label}
            </button>
          ))}
        </div>

        {/* 국내/해외, 뷰 전환(주별/월별) — 앱(모바일)에서는 둘 다 숨김 */}
        <div className="ml-auto hidden shrink-0 items-center gap-1 lg:flex">
          <div className="flex gap-1 rounded-lg bg-muted p-1 text-xs">
            {(["domestic", "overseas"] as const).map((r) => (
              <button
                key={r}
                type="button"
                onClick={() =>
                  onSetRegionFilter(regionFilter === r ? "all" : r)
                }
                className={segBtn(regionFilter === r)}
              >
                {r === "domestic" ? "국내" : "해외"}
              </button>
            ))}
          </div>

          <div className="flex gap-1 rounded-lg bg-muted p-1 text-xs">
            {(["week", "month"] as const).map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => onSetViewMode(v)}
                className={segBtn(viewMode === v)}
              >
                {v === "week" ? "주별" : "월별"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 서브 카테고리 — 현재 탭(전체/경제지표/실적)에 속한 카테고리만 다중 선택 */}
      <div className="flex flex-nowrap items-center gap-1">
        {subCategories.map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => onToggleCategory(c)}
            aria-pressed={categorySet.has(c)}
            className={cn(
              "flex shrink-0 cursor-pointer items-center gap-1 rounded-full border bg-muted/60 px-1.5 py-0.5 text-[11px] whitespace-nowrap transition-all hover:bg-muted",
              categorySet.has(c) &&
                "border-primary/40 bg-primary/10 font-medium text-primary",
              categorySet.size > 0 && !categorySet.has(c) && "opacity-40"
            )}
          >
            <span
              className={cn("size-1.5 shrink-0 rounded-full", CAT[c].dot)}
            />
            {CAT[c].label}
          </button>
        ))}
      </div>
    </div>
  )
}
