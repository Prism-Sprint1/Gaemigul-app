"use client"

import { CalendarMonthView, useCalendar } from "@/components/ui/full-calendar"
import { cn } from "@/lib/utils"
import { Dialog } from "@base-ui/react/dialog"
import {
  addMonths,
  endOfDay,
  endOfMonth,
  endOfWeek,
  format,
  isSameDay,
  isSameMonth,
  isWithinInterval,
  startOfDay,
  startOfMonth,
  startOfWeek,
  subMonths,
} from "date-fns"
import { ko } from "date-fns/locale/ko"
import { ChevronDown, ChevronLeft, ChevronRight, X } from "lucide-react"
import { useEffect, useMemo, useRef, useState } from "react"
import { CAT, CATS, NEWS, type Category, type NewsItem } from "./news-data"

export type Mode = "all" | "week" | "month" | "custom"

// '사용자' 탭은 좁은 화면(lg 미만)에서만 노출 — 넓은 화면은 왼쪽 큰 달력이 그 역할을 함
const TABS: [Mode, string][] = [
  ["all", "전체"],
  ["week", "주별"],
  ["month", "월별"],
  ["custom", "사용자"],
]

const navBtn =
  "cursor-pointer text-muted-foreground transition-colors hover:text-foreground"

export type DayGroup = {
  date: Date
  list: NewsItem[]
  badge: "focus" | "special" | null
}

/** 정렬된 같은 날 일정 배열 → 그룹 */
function buildDayGroup(list: NewsItem[]): DayGroup {
  return {
    date: list[0].publishedAt,
    list,
    badge: null,
  }
}

/** 일정 배열 → 시간순 정렬 후 날짜별 그룹 */
function groupByDay(items: NewsItem[]): DayGroup[] {
  const byDay = new Map<string, NewsItem[]>()
  for (const n of [...items].sort(
    (a, b) => a.publishedAt.getTime() - b.publishedAt.getTime()
  )) {
    const k = format(n.publishedAt, "yyyy-MM-dd")
    byDay.set(k, [...(byDay.get(k) ?? []), n])
  }
  return [...byDay.values()].map(buildDayGroup)
}

/** 특정 날짜의 전체 일정(필터 무시) → 그룹. 없으면 null */
export function dayGroupOf(d: Date): DayGroup | null {
  return groupByDay(NEWS.filter((n) => isSameDay(n.publishedAt, d)))[0] ?? null
}

/* ------------------------------------------------------------------ */

export function NewsPanel({
  onOpenItem,
}: {
  onOpenItem: (group: DayGroup, itemId: string) => void
}) {
  const { selectedDate, date, setSelectedDate, setDate, today } = useCalendar()
  const active = selectedDate ?? date // 선택된 날짜 (없으면 보고 있는 달 기준일)

  const [mode, setMode] = useState<Mode>("all")
  // 비어 있으면 전체 표시, 하나 이상 선택되면 해당 카테고리만 표시
  const [selected, setSelected] = useState<Set<Category>>(new Set())

  /** 날짜 이동 → 왼쪽 캘린더와 동기화 */
  const go = (d: Date) => {
    setSelectedDate(d)
    if (!isSameMonth(d, date)) setDate(d)
  }

  const groups = useMemo(() => {
    const range =
      mode === "week"
        ? {
            start: startOfWeek(active, { locale: ko }),
            end: endOfWeek(active, { locale: ko }),
          }
        : mode === "month"
          ? { start: startOfMonth(date), end: endOfMonth(date) }
          : mode === "custom"
            ? { start: startOfDay(active), end: endOfDay(active) }
            : null

    return groupByDay(
      NEWS.filter(
        (n) => selected.size === 0 || selected.has(n.category)
      ).filter((n) => !range || isWithinInterval(n.publishedAt, range))
    )
  }, [mode, active, date, selected])

  return (
    <section className="flex w-full shrink-0 flex-col border-t bg-card lg:w-90 lg:overflow-hidden lg:border-t-0 lg:border-l">
      {/* ── 고정 영역 ── */}
      <div className="flex flex-col gap-3 border-b p-4 pb-4 sm:p-5">
        {/* 조회 기간 탭 */}
        <div className="flex gap-1 rounded-lg bg-muted p-1 text-sm">
          {TABS.map(([k, label]) => (
            <button
              key={k}
              onClick={() => setMode(k)}
              className={cn(
                "flex-1 cursor-pointer rounded-md py-1 transition-colors",
                k === "custom" && "lg:hidden", // '사용자' 탭은 좁은 화면 전용
                mode === k
                  ? "bg-card font-semibold text-primary shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {label}
            </button>
          ))}
        </div>

        {/* 월 네비 — 왼쪽 캘린더와 동기화 */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setDate(subMonths(date, 1))}
            aria-label="이전 달"
            className={navBtn}
          >
            <ChevronLeft className="size-4" />
          </button>
          <span className="font-semibold tabular-nums">
            {format(date, "yyyy년 M월")}
          </span>
          <button
            onClick={() => setDate(addMonths(date, 1))}
            aria-label="다음 달"
            className={navBtn}
          >
            <ChevronRight className="size-4" />
          </button>
          <button
            onClick={() => go(today)}
            className="ml-auto cursor-pointer rounded-md border px-2 py-1 text-xs transition-colors hover:bg-muted"
          >
            오늘
          </button>
        </div>

        {/* 색깔별 카테고리 필터 */}
        <div className="flex flex-col gap-2">
          <span className="text-xs font-medium text-muted-foreground">
            색깔별 카테고리 필터
          </span>
          <div className="flex flex-wrap gap-1.5">
            {CATS.map((c) => (
              <button
                key={c}
                onClick={() => setSelected((s) => toggle(s, c))}
                aria-pressed={selected.has(c)}
                className={cn(
                  "flex cursor-pointer items-center gap-1.5 rounded-full border bg-muted/60 px-2 py-1 text-xs transition-all hover:bg-muted",
                  selected.has(c) &&
                    "border-primary/40 bg-primary/10 font-medium text-primary",
                  selected.size > 0 && !selected.has(c) && "opacity-40"
                )}
              >
                <span className={cn("size-2 rounded-full", CAT[c].dot)} />
                {CAT[c].label}
              </button>
            ))}
          </div>
          <p className="text-[11px] text-muted-foreground">
            색깔별 태그로 원하는 일정을 빠르게 필터링하세요.
          </p>
        </div>

        {/* '사용자' 탭(좁은 화면 전용): 왼쪽 큰 달력 대신 패널 안에서 날짜를 고른다 */}
        {mode === "custom" && (
          <div className="h-80 overflow-hidden rounded-lg border p-2 lg:hidden">
            <CalendarMonthView />
          </div>
        )}
      </div>

      {/* ── 리스트 (모바일: 페이지와 함께 스크롤 / lg: 패널 내부 스크롤) ── */}
      <div className="flex-1 space-y-5 p-4 sm:p-5 lg:min-h-0 lg:overflow-y-auto">
        {groups.length === 0 ? (
          <p className="grid place-items-center py-10 text-sm text-muted-foreground lg:h-full">
            표시할 뉴스가 없습니다
          </p>
        ) : (
          groups.map((g) => {
            // 빨간 뭉치 강조: 오늘 날짜 + 사용자가 클릭해 선택한 날
            const isActiveDay =
              isSameDay(g.date, today) ||
              (!!selectedDate && isSameDay(g.date, selectedDate))
            return (
              <div
                key={+g.date}
                className={cn(
                  "space-y-2 transition-colors",
                  isActiveDay
                    ? "rounded-xl border border-primary/25 bg-primary/5 p-3"
                    : "border-l-2 border-transparent pl-3"
                )}
              >
                <div className="flex items-center justify-between">
                  <span
                    className={cn(
                      "flex items-center gap-1.5 text-sm font-semibold",
                      isActiveDay && "text-primary"
                    )}
                  >
                    {isActiveDay && (
                      <span className="size-2 rounded-full bg-primary" />
                    )}
                    {format(g.date, "M월 d일 EEEE", { locale: ko })}
                  </span>
                  <span
                    className={cn(
                      "rounded px-1.5 py-0.5 text-[10px] font-bold",
                      isActiveDay
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    )}
                  >
                    {`${g.list.length}건`}
                  </span>
                </div>

                {g.list.map((n) => {
                  const c = CAT[n.category]
                  return (
                    <button
                      key={n.id}
                      type="button"
                      onClick={() => onOpenItem(g, n.id)}
                      className={cn(
                        "block w-full cursor-pointer rounded-lg border px-3 py-2 text-left transition-all hover:brightness-95 active:brightness-90",
                        isActiveDay ? "bg-card" : "bg-muted/70"
                      )}
                    >
                      <div className="flex items-start justify-between gap-2 text-xs">
                        <span className="flex items-center gap-1.5">
                          <span
                            className={cn("font-semibold tabular-nums", c.text)}
                          >
                            {format(n.publishedAt, "HH:mm")}
                          </span>
                          <span
                            className={cn("size-1.5 rounded-full", c.dot)}
                          />
                          <span className="text-muted-foreground">
                            {c.label}
                          </span>
                        </span>
                        <span className="shrink-0 text-[11px] text-muted-foreground">
                          {n.region}
                        </span>
                      </div>
                      <p className="mt-1 text-sm leading-snug font-semibold">
                        {n.title}
                      </p>
                      <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                        {n.summary}
                      </p>
                    </button>
                  )
                })}
              </div>
            )
          })
        )}
      </div>
    </section>
  )
}

/* ------------------------------------------------------------------ */

function toggle<T>(set: Set<T>, value: T) {
  const next = new Set(set)
  if (!next.delete(value)) next.add(value)
  return next
}

/** 일정 카드 / 캘린더 날짜 클릭 시 그날 일정 목록을 아코디언으로 보여주는 팝업 */
export function DayDetailDialog({
  popup,
  onClose,
}: {
  popup: { group: DayGroup; itemId: string } | null
  onClose: () => void
}) {
  return (
    <Dialog.Root open={!!popup} onOpenChange={(open) => !open && onClose()}>
      <Dialog.Portal>
        <Dialog.Backdrop className="fixed inset-0 z-50 bg-black/40" />
        <Dialog.Popup className="fixed top-1/2 left-1/2 z-50 flex max-h-[85vh] w-[calc(100vw-2rem)] max-w-90 -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-xl border bg-card shadow-lg">
          {popup && (
            <DayDetailBody group={popup.group} initialId={popup.itemId} />
          )}
        </Dialog.Popup>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

function DayDetailBody({
  group,
  initialId,
}: {
  group: DayGroup
  initialId: string
}) {
  const scrollRef = useRef<HTMLDivElement>(null)
  // 일정이 여러 개면 아코디언(각각 열고 닫기), 하나면 항상 펼침
  const multiple = group.list.length > 1
  const [openIds, setOpenIds] = useState<Set<string>>(() =>
    multiple ? new Set([initialId]) : new Set(group.list.map((n) => n.id))
  )

  const toggleOpen = (id: string) =>
    setOpenIds((s) => {
      const next = new Set(s)
      if (!next.delete(id)) next.add(id)
      return next
    })

  // 처음 클릭한 카드를 맨 위로
  useEffect(() => {
    scrollRef.current
      ?.querySelector<HTMLElement>(`[data-id="${initialId}"]`)
      ?.scrollIntoView({ block: "start" })
  }, [initialId])

  return (
    <>
      <div className="flex items-center justify-between border-b p-4">
        <Dialog.Title className="text-base font-bold">
          {format(group.date, "yyyy년 M월 d일 (EEE)", { locale: ko })}
        </Dialog.Title>
        <Dialog.Close
          aria-label="닫기"
          className="cursor-pointer text-muted-foreground transition-colors hover:text-foreground"
        >
          <X className="size-4" />
        </Dialog.Close>
      </div>

      <div
        ref={scrollRef}
        className="relative min-h-0 flex-1 space-y-2 overflow-y-auto p-4"
      >
        {group.list.map((n) => {
          const c = CAT[n.category]
          const isOpen = openIds.has(n.id)
          const facts = (
            [
              ["예상치", n.detail?.forecast],
              ["이전치", n.detail?.previous],
              ["발표처", n.detail?.source],
            ] as const
          ).filter(([, v]) => v)
          return (
            <div
              key={n.id}
              data-id={n.id}
              className={cn(
                "overflow-hidden rounded-lg border border-l-2",
                c.card
              )}
            >
              <button
                type="button"
                onClick={() => multiple && toggleOpen(n.id)}
                aria-expanded={isOpen}
                className={cn(
                  "flex w-full items-center gap-2 p-3 text-left transition-colors",
                  multiple && "cursor-pointer hover:bg-muted/40"
                )}
              >
                <span className="flex min-w-0 flex-1 items-center gap-1.5 text-xs">
                  <span
                    className={cn(
                      "shrink-0 rounded px-1.5 py-0.5 font-semibold text-white tabular-nums",
                      c.dot
                    )}
                  >
                    {format(n.publishedAt, "HH:mm")}
                  </span>
                  <span
                    className={cn(
                      "truncate font-semibold",
                      !isOpen && "text-muted-foreground"
                    )}
                  >
                    {n.title}
                  </span>
                </span>
                {multiple && (
                  <ChevronDown
                    aria-hidden
                    className={cn(
                      "size-4 shrink-0 text-muted-foreground transition-transform duration-300",
                      isOpen && "rotate-180"
                    )}
                  />
                )}
              </button>

              {/* 펼침 영역: grid 0fr → 1fr 로 부드럽게 */}
              <div
                className={cn(
                  "grid transition-[grid-template-rows] duration-300 ease-out",
                  isOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
                )}
              >
                <div className="overflow-hidden">
                  <div className="space-y-2 px-3 pb-3 text-xs">
                    <div className="flex items-center gap-1.5 text-muted-foreground">
                      <span>{c.label}</span>
                      <span>· {n.region}</span>
                    </div>

                    {facts.length > 0 && (
                      <dl className="flex flex-wrap gap-x-4 gap-y-1">
                        {facts.map(([k, v]) => (
                          <div key={k} className="flex gap-1">
                            <dt className="text-muted-foreground">{k}</dt>
                            <dd className="font-medium">{v}</dd>
                          </div>
                        ))}
                      </dl>
                    )}

                    <p className="rounded bg-background/60 p-2 leading-relaxed text-muted-foreground">
                      {n.summary}
                    </p>

                    {n.detail?.sectors && n.detail.sectors.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1">
                        <span className="text-muted-foreground">
                          관련 수혜 섹터
                        </span>
                        {n.detail.sectors.map((s) => (
                          <span
                            key={s}
                            className="rounded-full border px-1.5 py-0.5 text-[11px]"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="border-t p-3">
        <Dialog.Close className="w-full cursor-pointer rounded-md bg-primary py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90">
          확인
        </Dialog.Close>
      </div>
    </>
  )
}
