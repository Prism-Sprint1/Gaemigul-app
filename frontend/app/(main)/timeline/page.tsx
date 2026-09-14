"use client"

import { useState } from "react"
import { isSameDay, startOfDay } from "date-fns"

import { PageTitle } from "@/components/common"
import { useTimelineSchedule } from "@/components/common/timeline"
import { TimelineDateHeader, TimelineSection } from "@/components/timeline"
import { timelineContents } from "@/lib/constant/timelineContent"

// 백엔드 연동 전이라 DB에 데이터가 있는 날짜는 오늘 하루뿐이다.
// 추후 연동 시 실제로 데이터가 존재하는 날짜 목록으로 교체한다.
const TODAY = startOfDay(new Date())
const AVAILABLE_DATES = [TODAY]

export default function TimelinePage() {
  const { items } = useTimelineSchedule(30000)
  const [selectedDate, setSelectedDate] = useState(TODAY)
  // 오늘이 아닌 날짜는 하루치 데이터가 이미 확정돼 있으므로 시간대 잠금 없이 전부 보여준다.
  const isViewingToday = isSameDay(selectedDate, TODAY)

  return (
    <div className="flex flex-1 flex-col gap-6">
      <PageTitle
        title="개미들을 위한 실시간 시장 신호"
        description="시장의 급박한 변화와 핵심 뉴스 요약을 페로몬 흔적처럼 빠르게 따라갑니다."
      />

      <TimelineDateHeader
        selectedDate={selectedDate}
        availableDates={AVAILABLE_DATES}
        onSelect={setSelectedDate}
      />

      <div className="flex flex-col gap-15">
        {items.map((item) => {
          const content = timelineContents.find(
            (timelineContent) => timelineContent.id === item.id
          )

          if (!content) return null

          return (
            <TimelineSection
              key={item.id}
              item={item}
              content={content}
              forceOpen={!isViewingToday}
            />
          )
        })}
      </div>
    </div>
  )
}
