"use client"

import { cn } from "@/lib/utils"
import "flag-icons/css/flag-icons.min.css"
import {
  addDays,
  addMonths,
  differenceInCalendarWeeks,
  endOfMonth,
  endOfWeek,
  format,
  isSameDay,
  isSameMonth,
  startOfDay,
  startOfMonth,
  startOfWeek,
  subMonths,
} from "date-fns"
import { ko } from "date-fns/locale/ko"
import { ChevronLeft, ChevronRight, Play, Sparkles } from "lucide-react"
import { useMemo, useState } from "react"
import {
  CAT,
  CATEGORY_GROUPS,
  CATS,
  countryCodeOf,
  MARKET_HOLIDAYS,
  NEWS,
  scopeOf,
  type Category,
  type CategoryGroupId,
  type MarketHoliday,
  type NewsItem,
} from "./news-data"
import { DayDetailDialog, dayGroupOf, type DayGroup } from "./news-panel"

type ViewMode = "week" | "month"
type RegionFilter = "all" | "domestic" | "overseas"
type GroupFilter = "all" | CategoryGroupId

const WEEKDAY_LABELS = ["월", "화", "수", "목", "금", "토"]

const navBtn =
  "cursor-pointer text-muted-foreground transition-colors hover:text-foreground"

/** 월~토 6칸(일요일 제외) 주 단위 그리드 — 해당 월이 걸친 주 전체 */
function getMonthGridWeeks(monthAnchor: Date): Date[][] {
  const start = startOfWeek(startOfMonth(monthAnchor), { weekStartsOn: 1 })
  const end = endOfWeek(endOfMonth(monthAnchor), { weekStartsOn: 1 })
  const weeks: Date[][] = []
  for (let cur = start; cur <= end; cur = addDays(cur, 7)) {
    weeks.push(Array.from({ length: 6 }, (_, i) => addDays(cur, i)))
  }
  return weeks
}

/** 월 기준 몇 번째 주인지 (월요일 시작) */
function weekOfMonth(d: Date, monthAnchor: Date): number {
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
function announceLabel(d: Date): string {
  const base = format(d, "a h시", { locale: ko })
  const min = d.getMinutes()
  return min === 0 ? `${base} 발표 예정` : `${base} ${min}분 발표 예정`
}

const segBtn = (active: boolean) =>
  cn(
    "cursor-pointer rounded-md px-2.5 py-1 whitespace-nowrap transition-colors",
    active
      ? "bg-card font-semibold text-primary shadow-sm"
      : "text-muted-foreground hover:text-foreground"
  )

function toggleCategory(set: Set<Category>, value: Category) {
  const next = new Set(set)
  if (!next.delete(value)) next.add(value)
  return next
}

/* ------------------------------------------------------------------ */

export function CalendarWorkspace() {
  const today = useMemo(() => new Date(), [])
  const [month, setMonth] = useState<Date>(() => startOfMonth(today))
  const [selectedDate, setSelectedDate] = useState<Date>(today)
  const [viewMode, setViewMode] = useState<ViewMode>("month")
  // 상단 탭(전체/경제지표/실적) — 바뀌면 아래 서브 카테고리 선택은 초기화
  const [groupFilter, setGroupFilter] = useState<GroupFilter>("all")
  // 서브 카테고리 다중 선택(현재 탭이 갖는 카테고리 중에서만 선택 가능)
  const [categorySet, setCategorySet] = useState<Set<Category>>(new Set())
  const [regionFilter, setRegionFilter] = useState<RegionFilter>("all")
  const [popup, setPopup] = useState<{
    group: DayGroup
    itemId: string
  } | null>(null)

  const selectGroup = (g: GroupFilter) => {
    setGroupFilter(g)
    setCategorySet(new Set())
  }

  // 현재 탭에서 고를 수 있는 서브 카테고리 — '전체'면 전체 6종
  const subCategories =
    groupFilter === "all" ? CATS : CATEGORY_GROUPS[groupFilter].categories

  const selectDate = (d: Date) => {
    setSelectedDate(d)
    if (!isSameMonth(d, month)) setMonth(startOfMonth(d))
  }

  const openDay = (d: Date) => {
    const g = dayGroupOf(d)
    if (g) setPopup({ group: g, itemId: g.list[0].id })
  }

  const openItem = (g: DayGroup, itemId: string) =>
    setPopup({ group: g, itemId })

  const filteredNews = useMemo(
    () =>
      NEWS.filter(
        (n) =>
          (groupFilter === "all" ||
            CATEGORY_GROUPS[groupFilter].categories.includes(n.category)) &&
          (categorySet.size === 0 || categorySet.has(n.category)) &&
          (regionFilter === "all" || scopeOf(n.region) === regionFilter)
      ),
    [groupFilter, categorySet, regionFilter]
  )

  const filteredHolidays = useMemo(
    () =>
      MARKET_HOLIDAYS.filter(
        (h) => regionFilter === "all" || h.scope === regionFilter
      ),
    [regionFilter]
  )

  return (
    <div className="flex min-h-svh justify-center bg-background p-3 sm:p-4 lg:p-6">
      <div className="flex w-full max-w-7xl flex-col gap-3 lg:flex-row">
        {/* 왼쪽: 필터 + 월간/주간 뷰 */}
        <main className="flex min-w-0 flex-1 flex-col gap-3 rounded-xl border bg-card p-4 shadow-sm sm:p-5">
          <h1 className="text-lg font-bold">증시캘린더</h1>

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex max-w-full gap-1 overflow-x-auto rounded-lg bg-muted p-1 text-sm">
              <button
                type="button"
                onClick={() => selectGroup("all")}
                className={segBtn(groupFilter === "all")}
              >
                전체
              </button>
              {(Object.keys(CATEGORY_GROUPS) as CategoryGroupId[]).map((g) => (
                <button
                  key={g}
                  type="button"
                  onClick={() => selectGroup(g)}
                  className={segBtn(groupFilter === g)}
                >
                  {CATEGORY_GROUPS[g].label}
                </button>
              ))}
            </div>

            <div className="flex gap-1 rounded-lg bg-muted p-1 text-sm">
              {(["all", "domestic", "overseas"] as const).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRegionFilter(r)}
                  className={segBtn(regionFilter === r)}
                >
                  {r === "all" ? "전체" : r === "domestic" ? "국내" : "해외"}
                </button>
              ))}
            </div>

            <div className="flex gap-1 rounded-lg bg-muted p-1 text-sm sm:ml-auto">
              {(["week", "month"] as const).map((v) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => setViewMode(v)}
                  className={segBtn(viewMode === v)}
                >
                  {v === "week" ? "주별" : "월별"}
                </button>
              ))}
            </div>
          </div>

          {/* 서브 카테고리 — 현재 탭(전체/경제지표/실적)에 속한 카테고리만 다중 선택 */}
          <div className="flex flex-wrap items-center gap-1.5">
            {subCategories.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setCategorySet((s) => toggleCategory(s, c))}
                aria-pressed={categorySet.has(c)}
                className={cn(
                  "flex cursor-pointer items-center gap-1.5 rounded-full border bg-muted/60 px-2 py-1 text-xs transition-all hover:bg-muted",
                  categorySet.has(c) &&
                    "border-primary/40 bg-primary/10 font-medium text-primary",
                  categorySet.size > 0 && !categorySet.has(c) && "opacity-40"
                )}
              >
                <span className={cn("size-2 rounded-full", CAT[c].dot)} />
                {CAT[c].label}
              </button>
            ))}
          </div>

          <div>
            {viewMode === "month" ? (
              <MonthGrid
                month={month}
                today={today}
                selectedDate={selectedDate}
                news={filteredNews}
                holidays={filteredHolidays}
                colorActive={categorySet.size > 0}
                onSelectDate={selectDate}
                onOpenDay={openDay}
                onOpenItem={openItem}
              />
            ) : (
              <WeekList
                month={month}
                selectedDate={selectedDate}
                news={filteredNews}
                holidays={filteredHolidays}
                colorActive={categorySet.size > 0}
                onOpenItem={openItem}
              />
            )}
          </div>
        </main>

        {/* 오른쪽: 미니 달력 + AI 요약 */}
        <aside className="flex w-full shrink-0 flex-col gap-3 lg:w-72">
          <MiniCalendar
            month={month}
            today={today}
            selectedDate={selectedDate}
            viewMode={viewMode}
            onMonthChange={setMonth}
            onSelectDate={selectDate}
          />
          <AiSummaryCard />
        </aside>
      </div>

      <DayDetailDialog popup={popup} onClose={() => setPopup(null)} />
    </div>
  )
}

/* ------------------------------------------------------------------ */

function MiniCalendar({
  month,
  today,
  selectedDate,
  viewMode,
  onMonthChange,
  onSelectDate,
}: {
  month: Date
  today: Date
  selectedDate: Date
  viewMode: ViewMode
  onMonthChange: (d: Date) => void
  onSelectDate: (d: Date) => void
}) {
  const weeks = useMemo(() => getMonthGridWeeks(month), [month])

  return (
    <div className="rounded-xl border bg-card p-3 shadow-sm sm:p-4">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-sm font-semibold tabular-nums">
          {format(month, "yyyy년 M월")}
        </span>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => onMonthChange(subMonths(month, 1))}
            aria-label="이전 달"
            className={navBtn}
          >
            <ChevronLeft className="size-4" />
          </button>
          <button
            type="button"
            onClick={() => onMonthChange(addMonths(month, 1))}
            aria-label="다음 달"
            className={navBtn}
          >
            <ChevronRight className="size-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-6 text-center text-[11px] text-muted-foreground">
        {WEEKDAY_LABELS.map((d) => (
          <span key={d}>{d}</span>
        ))}
      </div>

      <div className="flex flex-col gap-y-1">
        {weeks.map((week) => {
          // 주별 뷰에서는 선택된 날짜가 속한 주 전체를 한 줄로 강조
          const isActiveWeek =
            viewMode === "week" && week.some((d) => isSameDay(d, selectedDate))
          return (
            <div
              key={+week[0]}
              className={cn(
                "grid grid-cols-6 rounded-full text-center text-xs transition-colors",
                isActiveWeek && "bg-red-50"
              )}
            >
              {week.map((d) => {
                const inMonth = isSameMonth(d, month)
                const isToday = isSameDay(d, today)
                const isSelected = isSameDay(d, selectedDate)
                return (
                  <button
                    key={+d}
                    type="button"
                    onClick={() => onSelectDate(d)}
                    className={cn(
                      "mx-auto flex size-7 cursor-pointer items-center justify-center rounded-full tabular-nums transition-colors",
                      !inMonth && "text-muted-foreground/40",
                      inMonth &&
                        !isToday &&
                        !isSelected &&
                        "text-foreground hover:bg-muted",
                      isSelected &&
                        !isToday &&
                        "bg-primary/15 font-semibold text-primary",
                      isToday && "bg-red-500 font-semibold text-white"
                    )}
                  >
                    {format(d, "d")}
                  </button>
                )
              })}
            </div>
          )
        })}
      </div>
    </div>
  )
}

/** 더미 카드 — 실제 AI 요약 생성 로직은 아직 없음 */
function AiSummaryCard() {
  return (
    <div className="rounded-xl border bg-primary/5 p-3 sm:p-4">
      <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-primary">
        <Sparkles className="size-3.5" />
        이번주 AI 요약
      </div>
      <p className="text-sm leading-snug font-medium">
        경제성장률 발표를 포함한 주요 경제지표 9개가 이번 주에 발표돼요
      </p>
      <span className="mt-2 flex w-fit items-center gap-0.5 text-xs text-muted-foreground">
        자세히 보기 <ChevronRight className="size-3" />
      </span>
    </div>
  )
}

/* ------------------------------------------------------------------ */

/** 국기 아이콘 — flag-icons 라이브러리(SVG) 사용, OS 이모지 폰트와 무관하게 동일하게 렌더링 */
function RegionBadge({ region }: { region: string }) {
  const code = countryCodeOf(region)
  return (
    <span
      aria-hidden
      title={region}
      className={cn(
        "fi shrink-0 rounded-xs align-middle ring-1 ring-black/10",
        `fi-${code}`
      )}
      style={{ fontSize: "11px" }}
    />
  )
}

/** 카테고리 색 바 — 기본은 연회색, 서브 카테고리 필터가 켜져 있을 때만 해당 카테고리 색으로 표시 */
function CategoryBar({
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

function EventRow({
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

function MonthGrid({
  month,
  today,
  selectedDate,
  news,
  holidays,
  colorActive,
  onSelectDate,
  onOpenDay,
  onOpenItem,
}: {
  month: Date
  today: Date
  selectedDate: Date
  news: NewsItem[]
  holidays: MarketHoliday[]
  colorActive: boolean
  onSelectDate: (d: Date) => void
  onOpenDay: (d: Date) => void
  onOpenItem: (g: DayGroup, itemId: string) => void
}) {
  const weeks = useMemo(() => getMonthGridWeeks(month), [month])

  const openItem = (n: NewsItem) => {
    const g = dayGroupOf(n.publishedAt)
    if (g) onOpenItem(g, n.id)
  }

  return (
    <div className="overflow-x-auto">
      <div className="flex min-w-175 flex-col">
        <div className="grid grid-cols-6 border-b pb-2">
          {WEEKDAY_LABELS.map((d) => (
            <div
              key={d}
              className="text-center text-xs font-medium text-muted-foreground sm:text-sm"
            >
              {d}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-6 gap-px overflow-hidden bg-border">
          {weeks.flat().map((d) => {
            const inMonth = isSameMonth(d, month)
            const dayNews = news
              .filter((n) => isSameDay(n.publishedAt, d))
              .sort((a, b) => a.publishedAt.getTime() - b.publishedAt.getTime())
            const holiday = holidays.find((h) => isSameDay(h.date, d))
            const holidayRows = holiday ? 1 : 0
            const total = holidayRows + dayNews.length
            const showAll = total <= 3
            const visibleCount = showAll
              ? dayNews.length
              : Math.max(0, 2 - holidayRows)
            const visibleNews = dayNews.slice(0, visibleCount)
            const hiddenCount = total - (holidayRows + visibleNews.length)
            const isToday = isSameDay(d, today)
            const isSelected = isSameDay(d, selectedDate)

            return (
              <div
                key={+d}
                className={cn(
                  "flex min-h-24 flex-col gap-0.5 p-1 sm:min-h-28 sm:p-1.5",
                  isSelected ? "bg-blue-50" : inMonth ? "bg-card" : "bg-muted/30"
                )}
              >
                <button
                  type="button"
                  onClick={() => onSelectDate(d)}
                  className={cn(
                    "w-fit cursor-pointer self-start rounded px-1 text-xs font-medium tabular-nums transition-colors sm:text-sm",
                    !inMonth && "text-muted-foreground/40",
                    isToday && "font-bold text-primary",
                    !isToday && inMonth && "text-foreground hover:bg-muted"
                  )}
                >
                  {format(d, "d")}
                  {isToday && (
                    <span className="ml-1 text-[10px] font-semibold">오늘</span>
                  )}
                </button>

                <div className="flex flex-1 flex-col gap-0.5 overflow-hidden">
                  {holiday && (
                    <span className="flex items-center gap-1 truncate text-[10px] text-rose-300 sm:text-[11px]">
                      📍 {holiday.scope === "domestic" ? "국내" : "해외"} 휴장일
                      ({holiday.label})
                    </span>
                  )}
                  {visibleNews.map((n) => (
                    <EventRow
                      key={n.id}
                      item={n}
                      colorActive={colorActive}
                      onClick={() => openItem(n)}
                    />
                  ))}
                  {hiddenCount > 0 && (
                    <button
                      type="button"
                      onClick={() => onOpenDay(d)}
                      className="cursor-pointer text-left text-[10px] text-muted-foreground hover:text-foreground sm:text-[11px]"
                    >
                      +{hiddenCount}개 더보기
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */

type DayEntry = { date: Date; news: NewsItem[]; holiday?: MarketHoliday }

function WeekList({
  month,
  selectedDate,
  news,
  holidays,
  colorActive,
  onOpenItem,
}: {
  month: Date
  selectedDate: Date
  news: NewsItem[]
  holidays: MarketHoliday[]
  colorActive: boolean
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
          <h3 className="mb-2 text-sm font-semibold text-primary">
            {format(month, "M월")} {weekNo}주차
          </h3>
          <div className="overflow-x-auto rounded-lg border">
            <table className="w-full min-w-125 text-sm">
              <thead>
                <tr className="border-b bg-muted/40 text-xs text-muted-foreground">
                  <th className="w-20 px-3 py-2 text-left font-medium">날짜</th>
                  <th className="px-3 py-2 text-left font-medium">일정</th>
                  <th className="w-36 px-3 py-2 text-right font-medium">
                    발표
                  </th>
                  <th className="w-20 px-3 py-2 text-right font-medium">
                    현재
                  </th>
                  <th className="w-20 px-3 py-2 text-right font-medium">
                    이전
                  </th>
                </tr>
              </thead>
              <tbody>
                {days.map((day) => (
                  <DayRows
                    key={+day.date}
                    day={day}
                    colorActive={colorActive}
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
  colorActive,
  onOpenItem,
}: {
  day: DayEntry
  colorActive: boolean
  onOpenItem: (g: DayGroup, itemId: string) => void
}) {
  const dateLabel = format(day.date, "d일 (EEE)", { locale: ko })

  const openItem = (n: NewsItem) => {
    const g = dayGroupOf(n.publishedAt)
    if (g) onOpenItem(g, n.id)
  }

  if (day.holiday) {
    return (
      <tr className="border-b last:border-b-0">
        <td className="px-3 py-2 align-top text-xs font-medium whitespace-nowrap text-primary">
          {dateLabel}
        </td>
        <td colSpan={4} className="px-3 py-2 text-xs text-rose-300">
          📍 {day.holiday.scope === "domestic" ? "국내" : "해외"} 휴장일 (
          {day.holiday.label})
        </td>
      </tr>
    )
  }

  return (
    <>
      {day.news.map((n, i) => (
        <tr key={n.id} className="border-b last:border-b-0 hover:bg-muted/30">
          {i === 0 && (
            <td
              rowSpan={day.news.length}
              className="px-3 py-2 align-top text-xs font-medium whitespace-nowrap text-primary"
            >
              {dateLabel}
            </td>
          )}
          <td className="px-3 py-2">
            <button
              type="button"
              onClick={() => openItem(n)}
              className="flex cursor-pointer items-center gap-1.5 text-left hover:text-primary"
            >
              <CategoryBar category={n.category} colorActive={colorActive} />
              <RegionBadge region={n.region} />
              <span
                className={cn(n.highlight === "special" && "font-semibold")}
              >
                {n.highlight === "special" && (
                  <span className="mr-1 rounded bg-emerald-500/10 px-1 py-0.5 text-[10px] font-semibold text-emerald-600">
                    주요
                  </span>
                )}
                {n.title}
              </span>
              {n.replay && (
                <span className="ml-1 inline-flex shrink-0 items-center gap-0.5 rounded-full border px-1.5 py-0.5 text-[10px] text-muted-foreground">
                  <Play className="size-2.5" /> 다시듣기
                </span>
              )}
            </button>
          </td>
          <td className="px-3 py-2 text-right text-xs whitespace-nowrap text-muted-foreground">
            {announceLabel(n.publishedAt)}
          </td>
          <td className="px-3 py-2 text-right text-xs whitespace-nowrap">
            {n.detail?.forecast ?? "-"}
          </td>
          <td className="px-3 py-2 text-right text-xs whitespace-nowrap">
            {n.detail?.previous ?? "-"}
          </td>
        </tr>
      ))}
    </>
  )
}
