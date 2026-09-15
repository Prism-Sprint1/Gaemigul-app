"use client"

import "flag-icons/css/flag-icons.min.css"
import { isSameMonth, startOfMonth } from "date-fns"
import { useMemo, useState } from "react"
import { PageTitle } from "@/components/common"
import { AiSummaryCard } from "@/components/calendar/ai-summary-card"
import { FilterBar } from "@/components/calendar/filter-bar"
import { MiniCalendar } from "@/components/calendar/mini-calendar"
import { MonthGrid } from "@/components/calendar/month-grid"
import { WeekList } from "@/components/calendar/week-list"
import {
  toggleCategory,
  type GroupFilter,
  type RegionFilter,
  type ViewMode,
} from "@/lib/calendar"
import {
  CATEGORY_GROUPS,
  CATS,
  MARKET_HOLIDAYS,
  NEWS,
  scopeOf,
  type Category,
} from "./news-data"
import { DayDetailDialog, dayGroupOf, type DayGroup } from "./news-panel"

export default function CalendarPage() {
  const today = useMemo(() => new Date(), [])
  const [month, setMonth] = useState<Date>(() => startOfMonth(today))
  const [selectedDate, setSelectedDate] = useState<Date>(today)
  // 앱(모바일)은 주별 고정이라 기본값도 주별로 시작
  const [viewMode, setViewMode] = useState<ViewMode>("week")
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
      <div className="flex w-full flex-col gap-3">
        {/* 로고 바로 아래, 페이지 맨 위에 고정되는 타이틀 */}
        <PageTitle
          title="주요 경제 지표와 이벤트 일정"
          description="수익을 좌우할 미래의 주요 경제 지표와 기업 일정을 미리 모아 대비합니다."
        />

        <div className="flex min-w-0 flex-col-reverse gap-3 lg:flex-row">
          {/* 왼쪽: 필터 + 월간/주간 뷰 */}
          <main className="flex min-w-0 flex-1 flex-col gap-3 rounded-xl border bg-card px-3 py-4 shadow-sm sm:pb-5 lg:px-5">
            {/* 전체/경제지표/실적, 국내/해외, 주별/월별 + 서브 카테고리 필터 — 웹에서는 스크롤해도 상단에 붙어서 따라옴 */}
            <FilterBar
              groupFilter={groupFilter}
              onSelectGroup={selectGroup}
              regionFilter={regionFilter}
              onSetRegionFilter={setRegionFilter}
              viewMode={viewMode}
              onSetViewMode={setViewMode}
              subCategories={subCategories}
              categorySet={categorySet}
              onToggleCategory={(c) =>
                setCategorySet((s) => toggleCategory(s, c))
              }
            />

            {/* 앱(모바일): 커다란 월간 캘린더 없이 주별 일정만 표시 */}
            <div className="lg:hidden">
              <WeekList
                month={month}
                selectedDate={selectedDate}
                news={filteredNews}
                holidays={filteredHolidays}
                colorActive={categorySet.size > 0}
                onOpenItem={openItem}
              />
            </div>

            {/* 데스크톱: 주별/월별 전환 가능 */}
            <div className="hidden lg:block">
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

          {/* 오른쪽: 미니 달력 + AI 요약 — 앱(360) 사이즈에서는 페이지 최상단에 세로로 노출, 웹에서는 스크롤해도 따라오도록 sticky */}
          <aside className="flex w-full shrink-0 flex-col gap-3 lg:sticky lg:top-23.75 lg:w-72 lg:self-start">
            <MiniCalendar
              month={month}
              today={today}
              selectedDate={selectedDate}
              viewMode={viewMode}
              onMonthChange={setMonth}
              onSelectDate={selectDate}
              onToday={() => {
                setMonth(startOfMonth(today))
                setSelectedDate(today)
              }}
            />
            <AiSummaryCard />
          </aside>
        </div>
      </div>

      <DayDetailDialog popup={popup} onClose={() => setPopup(null)} />
    </div>
  )
}
