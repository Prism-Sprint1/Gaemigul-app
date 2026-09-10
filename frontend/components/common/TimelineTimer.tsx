"use client"

import { Separator } from "../ui"
import Timeline from "./Timeline"
import { useTimelineSchedule } from "./use-timeline-schedule"

function formatClock(date: Date) {
  const hours = String(date.getHours()).padStart(2, "0")
  const minutes = String(date.getMinutes()).padStart(2, "0")
  const seconds = String(date.getSeconds()).padStart(2, "0")
  return `${hours}:${minutes}:${seconds}`
}

export default function TimelineTimer() {
  const { now, nextItem, remainingLabel } = useTimelineSchedule(1000)

  return (
    <>
      <div className="flex w-full items-end justify-between px-5 py-3">
        {/* 타임라인 타이머 */}
        <div className="flex flex-col gap-0.5">
          <span className="text-[12px]">현재 시간</span>
          <strong className="text-[24px] leading-6 font-semibold tracking-[1px]">
            {now ? formatClock(now) : "--:--:--"}
          </strong>
        </div>
        <div className="text-right text-[12px]">
          <p>다음 일정</p>
          <p className="pt-0.75">{nextItem ? nextItem.title : "-"}</p>
          <p className="font-semibold text-point">{remainingLabel ?? "-"}</p>
        </div>
      </div>
      <Separator className="w-full" />
      <Timeline />
    </>
  )
}
