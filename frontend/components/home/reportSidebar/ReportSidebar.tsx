"use client"

import { useState } from "react"
import { usePathname } from "next/navigation"
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp } from "lucide-react"
import { cn } from "cn"

import { Badge, Separator } from "@/components/ui"
import { reportMonths, reportWeekGroups } from "@/lib/constant/report"

const TIMELINE_PAGE_PATH = "/timeline"

const DEFAULT_MONTH_INDEX = reportMonths.findIndex(
  (month) => month.subLabel === "SEPTEMBER"
)

const DEFAULT_ACTIVE_REPORT_ID =
  reportWeekGroups
    .flatMap((group) => group.items)
    .find((item) => item.isHighlighted)?.id ?? null

export default function ReportSidebar() {
  const pathname = usePathname()
  const [monthIndex, setMonthIndex] = useState(
    DEFAULT_MONTH_INDEX === -1 ? 0 : DEFAULT_MONTH_INDEX
  )
  const [openGroupId, setOpenGroupId] = useState<string | null>(
    reportWeekGroups[0]?.id ?? null
  )
  const [activeReportId, setActiveReportId] = useState<string | null>(
    DEFAULT_ACTIVE_REPORT_ID
  )

  if (pathname !== TIMELINE_PAGE_PATH) {
    return null
  }

  const month = reportMonths[monthIndex]

  return (
    <aside className="max-w-67.5">
      <div>
        {/* 상단 월 교체 영역 */}
        <div className="flex items-center justify-between px-5 py-3">
          <div className="flex items-baseline gap-1.5">
            <strong className="text-[22px] font-bold">{month.label}</strong>
            <span className="text-[12px] font-medium text-neutral-400">
              {month.subLabel}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <button
              type="button"
              aria-label="이전 달"
              disabled={monthIndex === 0}
              onClick={() => setMonthIndex((index) => Math.max(0, index - 1))}
              className="cursor-pointer rounded-md p-1 text-neutral-400 transition-colors duration-200 hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronLeft size="16" />
            </button>
            <button
              type="button"
              aria-label="다음 달"
              disabled={monthIndex === reportMonths.length - 1}
              onClick={() =>
                setMonthIndex((index) =>
                  Math.min(reportMonths.length - 1, index + 1)
                )
              }
              className="cursor-pointer rounded-md p-1 text-neutral-400 transition-colors duration-200 hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronRight size="16" />
            </button>
          </div>
        </div>
        <Separator className="w-full" />
      </div>

      <div className="flex flex-col py-3">
        {/* 주간 드롭다운 리스트 */}
        {reportWeekGroups.map((group) => {
          const isOpen = openGroupId === group.id

          return (
            <div
              key={group.id}
              className="border-b border-neutral-100 last:border-b-0"
            >
              <button
                type="button"
                onClick={() =>
                  setOpenGroupId((current) =>
                    current === group.id ? null : group.id
                  )
                }
                className="flex w-full cursor-pointer items-center justify-between px-5 py-3 text-left"
              >
                <span className="flex items-center gap-2 text-[13px] font-semibold">
                  <span
                    className={cn(
                      "size-1.5 rounded-full transition-all duration-300",
                      isOpen ? "bg-point" : "bg-neutral-300"
                    )}
                  />
                  {group.rangeLabel}
                </span>
                {isOpen ? (
                  <ChevronUp size="16" className="text-neutral-400" />
                ) : (
                  <ChevronDown size="16" className="text-neutral-400" />
                )}
              </button>

              <div
                className={cn(
                  "grid transition-all duration-300 ease-in-out",
                  isOpen
                    ? "grid-rows-[1fr] bg-[#f4f4f5] opacity-100"
                    : "grid-rows-[0fr] opacity-0"
                )}
              >
                <ul
                  className={cn(
                    "flex flex-col gap-2.5 overflow-hidden px-5 transition-all duration-300",
                    isOpen ? "py-3" : "py-0"
                  )}
                >
                  {group.items.map((item) => {
                    const isActive = activeReportId === item.id

                    return (
                      <li key={item.id}>
                        <button
                          type="button"
                          onClick={() => setActiveReportId(item.id)}
                          className={cn(
                            "relative flex w-full cursor-pointer items-start gap-3 rounded-xl border bg-white px-2 py-3 text-left shadow-sm transition-colors duration-200",
                            isActive
                              ? "border-point shadow-point/40"
                              : "border-neutral-200 hover:bg-neutral-50"
                          )}
                        >
                          <Badge
                            className={cn(
                              "absolute -top-2 right-3 text-[10px] transition-colors duration-200",
                              isActive
                                ? "bg-point text-white"
                                : "border border-neutral-200 bg-white text-neutral-400"
                            )}
                          >
                            {item.badgeLabel}
                          </Badge>
                          <div
                            className={cn(
                              "flex w-9 flex-col items-center justify-center rounded-lg py-1 text-[10px] font-medium transition-colors duration-200",
                              isActive
                                ? "bg-point text-white"
                                : "bg-neutral-100 text-neutral-500"
                            )}
                          >
                            <span className="opacity-80">{item.month}</span>
                            <strong className="text-[18px] leading-4 font-bold">
                              {item.date}
                            </strong>
                            <span className="opacity-80">{item.day}</span>
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="text-[13px] font-semibold">
                              {item.title}
                            </p>
                            <p className="mt-0.5 line-clamp-2 text-[11px] text-neutral-500">
                              {item.description}
                            </p>
                          </div>
                        </button>
                      </li>
                    )
                  })}
                </ul>
              </div>
            </div>
          )
        })}
      </div>
    </aside>
  )
}
