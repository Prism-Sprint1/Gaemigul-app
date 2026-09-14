"use client"

import { useState } from "react"
import { startOfDay } from "date-fns"

import { PageTitle } from "@/components/common"
import { useTimelineSchedule } from "@/components/common/timeline"
import { TimelineDateHeader, TimelineSection } from "@/components/timeline"
import { timelineContents } from "@/lib/constant/timelineContent"

// 백엔드 연동 전이라 조회 가능한 날짜 범위는 오늘 하루로 고정한다.
const TODAY = startOfDay(new Date())

export default function TimelinePage() {
  const { items } = useTimelineSchedule(30000)
  const [selectedDate, setSelectedDate] = useState(TODAY)

  return (
    <div className="flex flex-col gap-6">
      <PageTitle
        title="개미들을 위한 실시간 시장 신호"
        description="시장의 급박한 변화와 핵심 뉴스 요약을 페로몬 흔적처럼 빠르게 따라갑니다."
      />

      <TimelineDateHeader
        selectedDate={selectedDate}
        minDate={TODAY}
        maxDate={TODAY}
        onSelect={setSelectedDate}
      />

      <div className="flex flex-col gap-15">
        {items.map((item) => {
          const content = timelineContents.find(
            (timelineContent) => timelineContent.id === item.id
          )

          if (!content) return null

          return <TimelineSection key={item.id} item={item} content={content} />
        })}
      </div>
    </div>
  )
}
