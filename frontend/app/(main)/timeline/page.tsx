"use client"

import { useEffect, useMemo, useState } from "react"
import { format, isSameDay, startOfDay } from "date-fns"

import { PageTitle } from "@/components/common"
import { useTimelineSchedule } from "@/components/common/timeline"
import { TimelineDateHeader, TimelineSection } from "@/components/timeline"
import { getTimelineDay, getTimelineGlossary } from "@/lib/api/timeline"
import { mapSlotToContent } from "@/lib/timeline-mapper"
import type { ApiTimelineSlot } from "@/lib/types/TimelineType"

const TODAY = startOfDay(new Date())
// 백엔드가 실데이터를 쌓기 시작한 날짜. 이전 날짜는 캘린더에서 선택할 수 없다.
const MIN_DATE = startOfDay(new Date(2026, 8, 14))
// 오늘은 새 슬롯이 계속 쌓이므로 이 주기로 다시 불러온다.
const REFRESH_INTERVAL_MS = 60_000

export default function TimelinePage() {
  const { items } = useTimelineSchedule(30000)
  const [selectedDate, setSelectedDate] = useState(TODAY)
  const isViewingToday = isSameDay(selectedDate, TODAY)

  const [slots, setSlots] = useState<ApiTimelineSlot[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [glossary, setGlossary] = useState<Record<string, string>>({})

  useEffect(() => {
    getTimelineGlossary()
      .then(setGlossary)
      .catch(() => setGlossary({}))
  }, [])

  useEffect(() => {
    let cancelled = false
    const dateParam = format(selectedDate, "yyyy-MM-dd")

    const load = (showLoading: boolean) => {
      if (showLoading) setIsLoading(true)

      getTimelineDay(dateParam)
        .then((data) => {
          if (cancelled) return
          setSlots(data)
          setError(null)
        })
        .catch(() => {
          if (cancelled) return
          setError(
            "타임라인 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."
          )
          setSlots([])
        })
        .finally(() => {
          if (!cancelled && showLoading) setIsLoading(false)
        })
    }

    load(true)

    const isToday = isSameDay(selectedDate, TODAY)
    const timer = isToday
      ? setInterval(() => load(false), REFRESH_INTERVAL_MS)
      : undefined

    return () => {
      cancelled = true
      if (timer) clearInterval(timer)
    }
  }, [selectedDate])

  const slotByKey = useMemo(() => {
    const map = new Map<string, ApiTimelineSlot>()
    slots.forEach((slot) => map.set(slot.slot_key, slot))
    return map
  }, [slots])

  return (
    <div className="flex w-full flex-col gap-6 px-6 py-4">
      <PageTitle
        title="개미들을 위한 실시간 시장 신호"
        description="시장의 급박한 변화와 핵심 뉴스 요약을 페로몬 흔적처럼 빠르게 따라갑니다."
      />

      <TimelineDateHeader
        selectedDate={selectedDate}
        minDate={MIN_DATE}
        maxDate={TODAY}
        onSelect={setSelectedDate}
      />

      {isLoading && (
        <p className="py-10 text-center text-sm text-neutral-400">
          타임라인을 불러오는 중이에요...
        </p>
      )}

      {!isLoading && error && (
        <p className="py-10 text-center text-sm text-decrease">{error}</p>
      )}

      {!isLoading && !error && slots.length === 0 && (
        <p className="py-10 text-center text-sm text-neutral-400">
          이 날짜에는 데이터가 없어요. 휴장일이거나 아직 수집되지 않았어요.
        </p>
      )}

      {!isLoading && !error && slots.length > 0 && (
        <div className="flex w-full flex-col gap-15">
          {items.map((item) => {
            const slot = slotByKey.get(item.id)
            if (!slot && !isViewingToday) return null

            return (
              <TimelineSection
                key={item.id}
                item={item}
                content={slot ? mapSlotToContent(slot) : null}
                glossary={glossary}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}
