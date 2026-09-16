"use client"

import {
  addDays,
  endOfMonth,
  format,
  isSameDay,
  isSameMonth,
  startOfDay,
  startOfMonth,
} from "date-fns"
import { ko } from "date-fns/locale/ko"
import { useMemo } from "react"
import type { MarketHoliday, NewsItem } from "@/app/(main)/calendar/news-data"
import { dayGroupOf, type DayGroup } from "@/app/(main)/calendar/news-panel"
import { announceLabel, weekOfMonth } from "@/lib/calendar"
import { CategoryBar } from "./category-bar"
import { RegionBadge } from "./region-badge"

type DayEntry = { date: Date; news: NewsItem[]; holiday?: MarketHoliday }

export function WeekList({
  month,
  selectedDate,
  news,
  allNews,
  holidays,
  onOpenItem,
}: {
  month: Date
  selectedDate: Date
  news: NewsItem[]
  allNews: NewsItem[]
  holidays: MarketHoliday[]
  onOpenItem: (g: DayGroup, itemId: string) => void
}) {
  // 이번 달을 보는 중이면 '오늘(선택일)'부터, 다른 달이면 1일부터 표시
  const rangeStart = isSameMonth(selectedDate, month)
    ? startOfDay(selectedDate)
    : startOfMonth(month)
  const rangeEnd = endOfMonth(month)

  const dayEntries = useMemo(() => {
    const entries: DayEntry[] = []
    for (let cur = rangeStart; cur <= rangeEnd; cur = addDays(cur, 1)) {
      const dayNews = news
        .filter((n) => isSameDay(n.publishedAt, cur))
        .sort((a, b) => a.publishedAt.getTime() - b.publishedAt.getTime())
      const holiday = holidays.find((h) => isSameDay(h.date, cur))
      if (dayNews.length > 0 || holiday) {
        entries.push({ date: new Date(cur), news: dayNews, holiday })
      }
    }
    return entries
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [+rangeStart, +rangeEnd, news, holidays])

  const weeks = useMemo(() => {
    const map = new Map<number, DayEntry[]>()
    for (const entry of dayEntries) {
      const w = weekOfMonth(entry.date, month)
      map.set(w, [...(map.get(w) ?? []), entry])
    }
    return [...map.entries()].sort(([a], [b]) => a - b)
  }, [dayEntries, month])

  if (weeks.length === 0) {
    return (
      <p className="py-16 text-center text-sm text-muted-foreground">
        표시할 일정이 없습니다
      </p>
    )
  }

  return (
    <div className="space-y-6">
      {weeks.map(([weekNo, days]) => (
        <div key={weekNo}>
          <h3 className="mb-2 text-[14px] font-bold text-primary">
            {format(month, "M월")} {weekNo}주차
          </h3>
          <div className="overflow-x-auto rounded-lg border">
            <table className="w-full min-w-135 text-sm">
              <thead>
                <tr className="border-b bg-muted/40 text-[12px] text-muted-foreground">
                  <th className="w-20 p-2 text-left font-semibold">날짜</th>
                  <th className="p-2 text-left font-semibold">일정</th>
                  <th className="w-36 p-2 text-left font-semibold">
                    발표 시간
                  </th>
                  <th className="w-20 p-2 text-left font-semibold">현재</th>
                  <th className="w-20 p-2 text-left font-semibold">이전</th>
                </tr>
              </thead>
              <tbody>
                {days.map((day) => (
                  <DayRows
                    key={+day.date}
                    day={day}
                    allNews={allNews}
                    onOpenItem={onOpenItem}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  )
}

function DayRows({
  day,
  allNews,
  onOpenItem,
}: {
  day: DayEntry
  allNews: NewsItem[]
  onOpenItem: (g: DayGroup, itemId: string) => void
}) {
  const dateLabel = format(day.date, "d일 (EEE)", { locale: ko })

  const openItem = (n: NewsItem) => {
    const g = dayGroupOf(n.publishedAt, allNews)
    if (g) onOpenItem(g, n.id)
  }

  if (day.holiday) {
    return (
      <tr className="border-b last:border-b-0">
        <td className="p-2 text-left text-[12px] font-medium whitespace-nowrap text-primary">
          {dateLabel}
        </td>
        <td colSpan={4} className="p-2 text-left text-[12px] text-red-500">
          📍 {day.holiday.scope === "domestic" ? "국내" : "해외"} 휴장일 (
          {day.holiday.label})
        </td>
      </tr>
    )
  }

  return (
    <>
      {day.news.map((n, i) => (
        <tr key={n.id} className="border-b last:border-b-0">
          {i === 0 && (
            <td
              rowSpan={day.news.length}
              className={`p-2 text-left text-[12px] font-medium whitespace-nowrap text-primary${day.news.length > 1 ? "align-top" : ""}`}
            >
              {dateLabel}
            </td>
          )}
          <td className="p-2 text-left">
            <button
              type="button"
              onClick={() => openItem(n)}
              title={n.title}
              className="flex w-full min-w-0 cursor-pointer items-center gap-1.5 rounded-md px-1.5 py-1 text-[12px] transition-colors hover:bg-primary/5 hover:text-primary"
            >
              <CategoryBar category={n.category} />
              <RegionBadge region={n.region} />
              <span className="truncate">{n.title}</span>
            </button>
          </td>
          <td className="p-2 text-left text-[12px] whitespace-nowrap text-muted-foreground">
            {announceLabel(n.publishedAt)}
          </td>
          <td className="p-2 text-left text-[12px] whitespace-nowrap">
            {n.detail?.forecast ?? "-"}
          </td>
          <td className="p-2 text-left text-[12px] whitespace-nowrap">
            {n.detail?.previous ?? "-"}
          </td>
        </tr>
      ))}
    </>
  )
}
