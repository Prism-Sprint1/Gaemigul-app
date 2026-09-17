"use client"

import { Suspense, useEffect, useMemo, useState } from "react"
import { usePathname, useRouter, useSearchParams } from "next/navigation"
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp } from "lucide-react"
import { cn } from "cn"

import { Badge, Separator, Skeleton } from "@/components/ui"
import { getReportList } from "@/lib/api/report"
import { mapWeeksToSections } from "@/lib/report-list-mapper"
import type { ReportWeekSection } from "@/lib/types/ReportType"

const TIMELINE_PAGE_PATH = "/timeline"
const BRIEFING_PAGE_PATH = "/briefing"

// 백엔드가 실데이터를 쌓기 시작한 달. 이전 달로는 넘어갈 수 없다.
const MIN_YEAR_MONTH = { year: 2026, month: 9 }

function getCurrentYearMonth() {
  const now = new Date()
  return { year: now.getFullYear(), month: now.getMonth() + 1 }
}

function shiftMonth(yearMonth: { year: number; month: number }, delta: number) {
  const total = yearMonth.year * 12 + (yearMonth.month - 1) + delta
  return { year: Math.floor(total / 12), month: (total % 12) + 1 }
}

function compareYearMonth(
  a: { year: number; month: number },
  b: { year: number; month: number }
) {
  return a.year * 12 + a.month - (b.year * 12 + b.month)
}

function ReportSidebarContent() {
  const pathname = usePathname()
  const router = useRouter()
  const searchParams = useSearchParams()

  const MAX_YEAR_MONTH = useMemo(() => getCurrentYearMonth(), [])
  const [yearMonth, setYearMonth] = useState(MAX_YEAR_MONTH)
  const [weeks, setWeeks] = useState<ReportWeekSection[] | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [openGroupId, setOpenGroupId] = useState<string | null>(null)

  const activeType = searchParams.get("type")
  const activeDate = searchParams.get("date")

  useEffect(() => {
    let cancelled = false

    const load = () => {
      setIsLoading(true)

      getReportList(yearMonth.year, yearMonth.month)
        .then((data) => {
          if (cancelled) return
          const sections = mapWeeksToSections(data.weeks)
          setWeeks(sections)
          setOpenGroupId(sections[0]?.id ?? null)
        })
        .catch(() => {
          if (cancelled) return
          setWeeks([])
          setOpenGroupId(null)
        })
        .finally(() => {
          if (!cancelled) setIsLoading(false)
        })
    }

    load()

    return () => {
      cancelled = true
    }
  }, [yearMonth])

  if (pathname !== TIMELINE_PAGE_PATH && pathname !== BRIEFING_PAGE_PATH) {
    return null
  }

  return (
    <aside className="sticky top-18.75 hidden h-[calc(100vh-75px)] w-67.5 min-w-67.5 md:block">
      <div>
        {/* 상단 월 교체 영역 */}
        <div className="flex items-center justify-between px-5 py-3">
          <div className="flex items-baseline gap-1.5">
            <strong className="text-[22px] font-bold">
              {String(yearMonth.month).padStart(2, "0")}월
            </strong>
            <span className="text-[12px] font-medium text-neutral-400">
              {yearMonth.year}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <button
              type="button"
              aria-label="이전 달"
              disabled={compareYearMonth(yearMonth, MIN_YEAR_MONTH) <= 0}
              onClick={() => setYearMonth((current) => shiftMonth(current, -1))}
              className="cursor-pointer rounded-md p-1 text-neutral-400 transition-colors duration-200 hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronLeft size="16" />
            </button>
            <button
              type="button"
              aria-label="다음 달"
              disabled={compareYearMonth(yearMonth, MAX_YEAR_MONTH) >= 0}
              onClick={() => setYearMonth((current) => shiftMonth(current, 1))}
              className="cursor-pointer rounded-md p-1 text-neutral-400 transition-colors duration-200 hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronRight size="16" />
            </button>
          </div>
        </div>
        <Separator className="w-full" />
      </div>

      <div className="flex flex-col py-3">
        {isLoading && (
          <div className="flex flex-col gap-3 px-5 py-3">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-16 w-full rounded-xl" />
            <Skeleton className="h-16 w-full rounded-xl" />
          </div>
        )}

        {!isLoading && weeks && weeks.length === 0 && (
          <p className="px-5 py-6 text-center text-[12px] leading-relaxed text-neutral-400">
            아직 리포트가 생성되지 않았습니다.
          </p>
        )}

        {!isLoading &&
          weeks &&
          weeks.map((group) => {
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
                      const isActive =
                        activeType === item.type && activeDate === item.date

                      return (
                        <li key={item.id}>
                          <button
                            type="button"
                            onClick={() =>
                              router.push(
                                `${BRIEFING_PAGE_PATH}?type=${item.type}&date=${item.date}`
                              )
                            }
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
                                {item.dateLabel}
                              </strong>
                              <span className="opacity-80">
                                {item.unitLabel}
                              </span>
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="line-clamp-1 text-[13px] font-semibold">
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

export default function ReportSidebar() {
  return (
    <Suspense fallback={null}>
      <ReportSidebarContent />
    </Suspense>
  )
}
