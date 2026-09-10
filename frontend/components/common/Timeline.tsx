"use client"

import { usePathname, useRouter } from "next/navigation"
import { cn } from "cn"

import { Badge } from "../ui"
import type { TimelineStatus } from "./timeline-items"
import { useTimelineSchedule } from "./use-timeline-schedule"

const TIMELINE_PAGE_PATH = "/timeline"

const dotClassName: Record<TimelineStatus, string> = {
  past: "bg-neutral-300",
  current: "bg-point",
  next: "bg-decrease",
  upcoming: "bg-neutral-300",
}

const badgeClassName: Record<TimelineStatus, string> = {
  past: "bg-neutral-500 text-white",
  current: "bg-point text-white",
  next: "bg-decrease text-white",
  upcoming: "",
}

const mutedStatuses = new Set<TimelineStatus>(["past", "upcoming"])

export default function Timeline() {
  const router = useRouter()
  const pathname = usePathname()
  const { items } = useTimelineSchedule(30000)

  const goToSection = (id: string) => {
    if (pathname === TIMELINE_PAGE_PATH) {
      document.getElementById(id)?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      })
      return
    }

    router.push(`${TIMELINE_PAGE_PATH}#${id}`)
  }

  return (
    <ol className="relative flex flex-col bg-ant-bg px-5 py-3">
      <span className="absolute top-5.5 bottom-5.5 left-6.75 w-0.5 bg-neutral-200" />
      {items.map((item) => {
        const isMuted = mutedStatuses.has(item.status)

        return (
          <li key={item.id} className="pb-5 last:pb-0">
            <button
              type="button"
              onClick={() => goToSection(item.id)}
              className={cn(
                "flex w-full cursor-pointer items-start gap-3 rounded-lg py-1 text-left transition-colors duration-200",
                item.status !== "current" && "hover:bg-neutral-100"
              )}
            >
              <div className="flex h-5 w-4 shrink-0 items-center justify-center">
                {item.status === "current" ? (
                  <span className="relative flex size-3.5 items-center justify-center">
                    <span className="absolute inline-flex size-full animate-ping rounded-full bg-point opacity-75" />
                    <span className="relative z-10 size-2.5 rounded-full bg-point ring-2 ring-white" />
                  </span>
                ) : (
                  <span
                    className={cn(
                      "z-10 size-2 rounded-full transition-colors duration-200",
                      dotClassName[item.status]
                    )}
                  />
                )}
              </div>
              <div
                className={cn(
                  "flex-1 rounded-lg",
                  item.status === "current" &&
                    "border border-point/60 bg-point/5 p-3"
                )}
              >
                <div className="flex items-center gap-1.5">
                  <span
                    className={cn(
                      "text-[12px] font-medium transition-colors duration-200",
                      isMuted ? "text-neutral-400" : "text-neutral-500"
                    )}
                  >
                    {item.time}
                  </span>
                  {item.status !== "upcoming" && (
                    <Badge
                      className={cn(
                        "text-[10px] transition-colors duration-200",
                        badgeClassName[item.status]
                      )}
                    >
                      {item.badgeLabel}
                    </Badge>
                  )}
                </div>
                <strong
                  className={cn(
                    "mt-1 block text-[14px] font-semibold transition-colors duration-200",
                    isMuted ? "text-neutral-400" : "text-foreground"
                  )}
                >
                  {item.title}
                </strong>
                <p
                  className={cn(
                    "mt-0.5 text-[12px] transition-colors duration-200",
                    isMuted ? "text-neutral-400" : "text-neutral-500"
                  )}
                >
                  {item.description}
                </p>
              </div>
            </button>
          </li>
        )
      })}
    </ol>
  )
}
