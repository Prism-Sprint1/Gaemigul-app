'use client'

import {
  Calendar,
  CalendarCurrentDate,
  CalendarMonthView,
  CalendarNextTrigger,
  CalendarPrevTrigger,
  CalendarTodayTrigger,
} from '@/components/ui/full-calendar'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useState } from 'react'
import { NEWS_EVENTS } from './news-data'
import { DayDetailDialog, NewsPanel, dayGroupOf, type DayGroup } from './news-panel'

export default function CalendarPage() {
  // 카드 클릭 / 캘린더 날짜 클릭 시 뜨는 상세 팝업
  const [popup, setPopup] = useState<{ group: DayGroup; itemId: string } | null>(
    null
  )

  return (
    // 위치·여백만 담당하는 바깥 래퍼 (모바일은 세로 스크롤, lg 이상은 한 화면 고정)
    <div className="flex min-h-svh justify-center bg-background p-3 sm:p-4 lg:h-svh lg:overflow-hidden lg:p-6">
      {/* ▼▼ 캘린더 카드 — 좁은 화면: 오른쪽 카드만 / lg: 좌우 2분할 ▼▼ */}
      <div className="flex w-full max-w-280 flex-col overflow-hidden rounded-xl border bg-card shadow-sm lg:h-full lg:flex-row">
        <Calendar
          enableHotkeys={false}
          events={NEWS_EVENTS}
          onDateSelect={(d) => {
            const g = dayGroupOf(d)
            if (g) setPopup({ group: g, itemId: g.list[0].id })
          }}
        >
          {/* 왼쪽: 큰 달력 — lg 이상에서만. 좁은 화면에서는 '사용자' 탭 안 달력으로 대체 */}
          <div className="hidden min-w-0 flex-1 flex-col gap-3 p-4 sm:p-5 lg:flex">
            <header className="flex flex-wrap items-center justify-center gap-3 py-1 sm:gap-4">
              <CalendarPrevTrigger aria-label="이전 달">
                <ChevronLeft className="size-4" />
              </CalendarPrevTrigger>
              <span className="text-base font-semibold sm:text-lg">
                <CalendarCurrentDate />
              </span>
              <CalendarNextTrigger aria-label="다음 달">
                <ChevronRight className="size-4" />
              </CalendarNextTrigger>
              <CalendarTodayTrigger className="ml-2 text-xs">
                오늘
              </CalendarTodayTrigger>
            </header>

            <div className="min-h-0 flex-1 overflow-hidden">
              <CalendarMonthView />
            </div>

            <p className="text-center text-xs text-muted-foreground">
              시간 기준: 사용자 현지 시간
            </p>
          </div>

          {/* 오른쪽(좁은 화면: 전체): 뉴스 패널 — 같은 카드 안, 구분선으로 분리 */}
          <NewsPanel onOpenItem={(group, itemId) => setPopup({ group, itemId })} />
        </Calendar>
      </div>
      {/* ▲▲ 캘린더 카드 ▲▲ */}

      <DayDetailDialog popup={popup} onClose={() => setPopup(null)} />
    </div>
  )
}
