import { cn } from "@/lib/utils"
import {
  addDays,
  differenceInCalendarWeeks,
  endOfMonth,
  endOfWeek,
  format,
  startOfMonth,
  startOfWeek,
} from "date-fns"
import { ko } from "date-fns/locale/ko"
import type { Category, CategoryGroupId } from "@/app/(main)/calendar/news-data"

export type ViewMode = "week" | "month"
export type RegionFilter = "all" | "domestic" | "overseas"
export type GroupFilter = "all" | CategoryGroupId

export const WEEKDAY_LABELS = ["월", "화", "수", "목", "금", "토"]

export const navBtn =
  "cursor-pointer text-muted-foreground transition-colors hover:text-foreground"

/** 월~토 6칸(일요일 제외) 주 단위 그리드 — 해당 월이 걸친 주 전체 */
export function getMonthGridWeeks(monthAnchor: Date): Date[][] {
  const start = startOfWeek(startOfMonth(monthAnchor), { weekStartsOn: 1 })
  const end = endOfWeek(endOfMonth(monthAnchor), { weekStartsOn: 1 })
  const weeks: Date[][] = []
  for (let cur = start; cur <= end; cur = addDays(cur, 7)) {
    weeks.push(Array.from({ length: 6 }, (_, i) => addDays(cur, i)))
  }
  return weeks
}

/** 월 기준 몇 번째 주인지 (월요일 시작) */
export function weekOfMonth(d: Date, monthAnchor: Date): number {
  const firstWeekStart = startOfWeek(startOfMonth(monthAnchor), {
    weekStartsOn: 1,
  })
  const thisWeekStart = startOfWeek(d, { weekStartsOn: 1 })
  return (
    differenceInCalendarWeeks(thisWeekStart, firstWeekStart, {
      weekStartsOn: 1,
    }) + 1
  )
}

/** '오후 9시 30분 발표 예정' 형태로 변환 (정각이면 분 생략) */
export function announceLabel(d: Date): string {
  const base = format(d, "a h시", { locale: ko })
  const min = d.getMinutes()
  return min === 0 ? `${base} 발표 예정` : `${base} ${min}분 발표 예정`
}

export const segBtn = (active: boolean) =>
  cn(
    "cursor-pointer rounded-md px-2.5 py-1.5 whitespace-nowrap transition-colors",
    active
      ? "bg-card font-semibold text-primary shadow-sm"
      : "text-muted-foreground hover:text-foreground"
  )

// 앱(모바일)에서는 줄을 꽉 채우도록 늘어나고, 웹(lg 이상)에서는 원래대로 콘텐츠 너비만 차지
export const groupSegBtn = (active: boolean) =>
  cn(segBtn(active), "flex-1 text-center lg:flex-none")

export function toggleCategory(set: Set<Category>, value: Category) {
  const next = new Set(set)
  if (!next.delete(value)) next.add(value)
  return next
}
