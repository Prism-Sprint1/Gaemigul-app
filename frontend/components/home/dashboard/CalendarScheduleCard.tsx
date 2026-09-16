import Link from "next/link"
import { CalendarDays, ChevronRight } from "lucide-react"

import { Badge, Button } from "@/components/ui"
import { todayCalendarSchedule } from "@/lib/constant/home"
import DashboardCard from "./DashboardCard"

const TAG_CLASSES: Record<string, string> = {
  국장: "bg-point3/60 text-point2",
  미장: "bg-blue-50 text-blue-600",
  지표: "bg-neutral-100 text-neutral-600",
  채권: "bg-emerald-50 text-emerald-600",
}

export default function CalendarScheduleCard() {
  return (
    <DashboardCard
      icon={<CalendarDays size={16} className="text-point" />}
      title="오늘의 비축 캘린더 일정"
      action={
        <Button
          render={<Link href="/calendar" />}
          nativeButton={false}
          variant="ghost"
          size="sm"
          className="text-neutral-400"
        >
          전체 보기
          <ChevronRight size={14} />
        </Button>
      }
    >
      <ul className="flex flex-col gap-1">
        {todayCalendarSchedule.map((item) => (
          <li
            key={`${item.time}-${item.title}`}
            className="flex items-center gap-3 border-b border-neutral-50 py-2.5 last:border-b-0"
          >
            <span className="w-12 shrink-0 text-xs font-semibold text-neutral-500">
              {item.time}
            </span>
            <span className="min-w-0 flex-1 truncate text-sm text-neutral-700">
              {item.title}
            </span>
            <Badge
              className={`shrink-0 text-[11px] ${TAG_CLASSES[item.tag] ?? "bg-neutral-100 text-neutral-600"}`}
            >
              {item.tag}
            </Badge>
          </li>
        ))}
      </ul>
    </DashboardCard>
  )
}
