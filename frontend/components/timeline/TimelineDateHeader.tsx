"use client"

import { useState } from "react"
import { Popover } from "@base-ui/react/popover"
import {
  addDays,
  addMonths,
  endOfMonth,
  endOfWeek,
  format,
  isSameDay,
  isSameMonth,
  startOfDay,
  startOfMonth,
  startOfWeek,
  subMonths,
} from "date-fns"
import { ko } from "date-fns/locale/ko"
import { ChevronDown, ChevronLeft, ChevronRight } from "lucide-react"
import { cn } from "cn"

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"]

function getMonthGrid(month: Date) {
  const start = startOfWeek(startOfMonth(month), { weekStartsOn: 0 })
  const end = endOfWeek(endOfMonth(month), { weekStartsOn: 0 })

  const days: Date[] = []
  let cursor = start
  while (cursor <= end) {
    days.push(cursor)
    cursor = addDays(cursor, 1)
  }
  return days
}

type TimelineDateHeaderProps = {
  selectedDate: Date
  /** 실제로 데이터가 존재하는 날짜 목록 — 이 목록에 없는 날짜는 선택할 수 없다. */
  availableDates: Date[]
  onSelect: (date: Date) => void
}

export default function TimelineDateHeader({
  selectedDate,
  availableDates,
  onSelect,
}: TimelineDateHeaderProps) {
  const [open, setOpen] = useState(false)
  const [viewMonth, setViewMonth] = useState(startOfMonth(selectedDate))

  const days = getMonthGrid(viewMonth)
  const isAvailable = (date: Date) =>
    availableDates.some((available) => isSameDay(available, date))

  return (
    <Popover.Root
      open={open}
      onOpenChange={(next) => {
        setOpen(next)
        if (next) setViewMonth(startOfMonth(selectedDate))
      }}
    >
      <Popover.Trigger className="flex cursor-pointer items-center gap-1 border-b border-neutral-100 pb-3 text-left">
        <strong className="text-base font-bold">
          {format(selectedDate, "M월 d일", { locale: ko })}
        </strong>
        <ChevronDown
          size={18}
          className={cn(
            "text-neutral-400 transition-transform duration-200",
            open && "rotate-180"
          )}
        />
      </Popover.Trigger>

      <Popover.Portal>
        <Popover.Positioner sideOffset={8} align="start">
          <Popover.Popup className="w-70 rounded-xl border border-neutral-200 bg-white p-4 shadow-lg outline-none">
            <div className="flex items-center justify-between">
              <button
                type="button"
                aria-label="이전 달"
                onClick={() => setViewMonth((month) => subMonths(month, 1))}
                className="flex size-7 cursor-pointer items-center justify-center rounded-md text-neutral-400 transition-colors duration-200 hover:bg-neutral-100 hover:text-neutral-600"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="text-sm font-semibold">
                {format(viewMonth, "yyyy년 M월", { locale: ko })}
              </span>
              <button
                type="button"
                aria-label="다음 달"
                onClick={() => setViewMonth((month) => addMonths(month, 1))}
                className="flex size-7 cursor-pointer items-center justify-center rounded-md text-neutral-400 transition-colors duration-200 hover:bg-neutral-100 hover:text-neutral-600"
              >
                <ChevronRight size={16} />
              </button>
            </div>

            <div className="mt-3 grid grid-cols-7 gap-y-1 text-center text-[11px] text-neutral-400">
              {WEEKDAYS.map((day) => (
                <span key={day}>{day}</span>
              ))}
            </div>

            <div className="mt-1 grid grid-cols-7 gap-y-1 text-center text-xs">
              {days.map((day) => {
                const disabled = !isAvailable(day)
                const isSelected = isSameDay(day, selectedDate)
                const isToday = isSameDay(day, new Date())
                const inMonth = isSameMonth(day, viewMonth)

                return (
                  <button
                    key={day.toISOString()}
                    type="button"
                    disabled={disabled}
                    onClick={() => {
                      onSelect(startOfDay(day))
                      setOpen(false)
                    }}
                    className={cn(
                      "mx-auto flex size-8 items-center justify-center rounded-full transition-colors duration-200",
                      !inMonth && "text-neutral-300",
                      disabled
                        ? "cursor-not-allowed text-neutral-200"
                        : "cursor-pointer hover:bg-neutral-100",
                      isSelected && "bg-point font-semibold text-white hover:bg-point",
                      !isSelected && isToday && "font-semibold text-point"
                    )}
                  >
                    {format(day, "d")}
                  </button>
                )
              })}
            </div>

            <p className="mt-3 text-[11px] leading-relaxed text-neutral-400">
              데이터가 있는 날짜만 선택할 수 있어요.
            </p>
          </Popover.Popup>
        </Popover.Positioner>
      </Popover.Portal>
    </Popover.Root>
  )
}
