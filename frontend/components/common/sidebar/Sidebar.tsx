"use client"

import { useEffect } from "react"
import { usePathname } from "next/navigation"
import { Lightbulb, X } from "lucide-react"
import { cn, formatClock } from "@/lib/utils"

import { Separator } from "../../ui"
import { TimelineTimer, useTimelineSchedule } from "../timeline"

import SidebarNav from "./SidebarNav"
import { useMobileSidebar } from "./MobileSidebarContext"

export default function Sidebar() {
  const { isOpen, close } = useMobileSidebar()
  const pathname = usePathname()
  const { now, nextItem, remainingLabel } = useTimelineSchedule(1000)

  useEffect(() => {
    close()
  }, [pathname, close])

  return (
    <>
      <div
        onClick={close}
        aria-hidden="true"
        className={cn(
          "fixed inset-0 z-40 bg-black/40 transition-opacity duration-300 md:hidden",
          isOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
      />

      <aside
        className={cn(
          "fixed inset-y-0 right-0 z-50 w-67.5 translate-x-full bg-white transition-transform duration-300",
          "md:sticky md:top-18.75 md:z-auto md:h-[calc(100vh-75px)] md:w-auto md:max-w-67.5 md:translate-x-0 md:overflow-hidden",
          isOpen && "translate-x-0"
        )}
      >
        <div className="flex flex-col gap-2 px-5 py-3 md:hidden">
          <button
            type="button"
            onClick={close}
            aria-label="메뉴 닫기"
            className="w-fit self-end p-1 text-neutral-500"
          >
            <X size={20} />
          </button>
          <div className="flex items-start justify-between">
            <div className="flex flex-col gap-0.5">
              <span className="text-[12px]">현재 시간</span>
              <strong className="text-[24px] leading-6 font-semibold tracking-[1px]">
                {now ? formatClock(now) : "--:--:--"}
              </strong>
            </div>
            <div className="text-right text-[12px]">
              <p>다음 일정</p>
              <p className="pt-0.75">{nextItem ? nextItem.title : "-"}</p>
              <p className="font-semibold text-point">
                {remainingLabel ?? "-"}
              </p>
            </div>
          </div>
        </div>
        <Separator className="w-full md:hidden" />
        <SidebarNav />
        <Separator className="w-full" />
        <div className="hidden h-[calc(100%-240px)] md:block">
          <TimelineTimer />
        </div>
        <div className="hidden bg-point3/60 p-3 px-5 md:block">
          <p className="flex items-center gap-1 text-[14px] font-semibold text-point2">
            <Lightbulb size="16" />
            TIP 불개미 꿀팁!
          </p>
          <p className="mt-0.5 text-[12px] text-neutral-500">
            매크로 지표 발표 직후 5분은 뇌동매매를 멈추고 페로몬 신호의 방향성을
            확인하세요.
          </p>
        </div>
      </aside>
    </>
  )
}
