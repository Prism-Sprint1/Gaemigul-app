'use client'

import { CalendarMonthView, useCalendar } from '@/components/ui/full-calendar'
import { cn } from '@/lib/utils'
import { Dialog } from '@base-ui/react/dialog'
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
} from 'date-fns'
import { ko } from 'date-fns/locale/ko'
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
  X,
} from 'lucide-react'
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { CAT, CATS, NEWS, type Category, type NewsItem } from './news-data'

export type Mode = 'all' | 'week' | 'month' | 'custom'

// '사용자' 탭은 좁은 화면(lg 미만)에서만 노출 — 넓은 화면은 왼쪽 큰 달력이 그 역할을 함
const TABS: [Mode, string][] = [
  ['all', '전체'],
  ['week', '주별'],
  ['month', '월별'],
  ['custom', '사용자'],
]

export type DayGroup = {
  date: Date
  list: NewsItem[]
  badge: 'focus' | 'special' | null
}

/** 정렬된 같은 날 일정 배열 → 그룹(배지 계산) */
function buildDayGroup(list: NewsItem[]): DayGroup {
  return {
    date: list[0].publishedAt,
    list,
    badge: list.some((n) => n.highlight === 'focus')
      ? 'focus'
      : list.some((n) => n.highlight === 'special')
        ? 'special'
        : null,
  }
}

/** 특정 날짜의 전체 일정(필터 무시) → 그룹. 없으면 null */
export function dayGroupOf(d: Date): DayGroup | null {
  const list = NEWS.filter((n) => isSameDay(n.publishedAt, d)).sort(
    (a, b) => a.publishedAt.getTime() - b.publishedAt.getTime()
  )
  return list.length ? buildDayGroup(list) : null
}

/* ------------------------------------------------------------------ */

export function NewsPanel({
  onOpenItem,
}: {
  onOpenItem: (group: DayGroup, itemId: string) => void
}) {
  const { selectedDate, date, setSelectedDate, setDate, today } = useCalendar()
  const active = selectedDate ?? date // 선택된 날짜 (없으면 보고 있는 달 기준일)

  const [mode, setMode] = useState<Mode>('all')
  // 비어 있으면 전체 표시, 하나 이상 선택되면 해당 카테고리만 표시
  const [selected, setSelected] = useState<Set<Category>>(new Set())

  /** 날짜 이동 → 왼쪽 캘린더와 동기화 */
  const go = (d: Date) => {
    setSelectedDate(d)
    if (!isSameMonth(d, date)) setDate(d)
  }

  const groups = useMemo(() => {
    const range =
      mode === 'week'
        ? { start: startOfWeek(active, { locale: ko }), end: endOfWeek(active, { locale: ko }) }
        : mode === 'month'
          ? { start: startOfMonth(date), end: endOfMonth(date) }
          : mode === 'custom'
            ? { start: startOfDay(active), end: endOfDay(active) }
            : null

    const items = NEWS.filter((n) => selected.size === 0 || selected.has(n.category))
      .filter((n) => !range || isWithinInterval(n.publishedAt, range))
      .sort((a, b) => a.publishedAt.getTime() - b.publishedAt.getTime())

    const byDay = new Map<string, NewsItem[]>()
    for (const n of items) {
      const k = format(n.publishedAt, 'yyyy-MM-dd')
      byDay.set(k, [...(byDay.get(k) ?? []), n])
    }

    return [...byDay.values()].map(buildDayGroup)
  }, [mode, active, date, selected])

  return (
    <section className="flex w-full shrink-0 flex-col border-t bg-card lg:w-90 lg:overflow-hidden lg:border-l lg:border-t-0">
      {/* ── 고정 영역 ── */}
      <div className="flex flex-col gap-3 border-b p-4 pb-4 sm:p-5">
        <div className="flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-lg font-bold">
            <span className="grid size-6 place-items-center rounded-md bg-red-500 text-white">
              <CalendarDays className="size-4" />
            </span>
            캘린더
          </h2>
          <button className="text-muted-foreground hover:text-foreground" aria-label="설정">
            <SlidersHorizontal className="size-4" />
          </button>
        </div>

        {/* 조회 기간 탭 */}
        <div className="flex gap-1 rounded-lg bg-muted p-1 text-sm">
          {TABS.map(([k, label]) => (
            <button
              key={k}
              onClick={() => setMode(k)}
              className={cn(
                'flex-1 rounded-md py-1 transition-colors',
                k === 'custom' && 'lg:hidden', // '사용자' 탭은 좁은 화면 전용
                mode === k
                  ? 'bg-background font-semibold text-foreground shadow-sm'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {label}
            </button>
          ))}
        </div>

        {/* 월 네비 — 왼쪽 캘린더와 동기화 */}
        <div className="flex items-center gap-2">
          <IconButton label="이전 달" onClick={() => setDate(subMonths(date, 1))}>
            <ChevronLeft className="size-4" />
          </IconButton>
          <span className="font-semibold tabular-nums">{format(date, 'yyyy년 M월')}</span>
          <IconButton label="다음 달" onClick={() => setDate(addMonths(date, 1))}>
            <ChevronRight className="size-4" />
          </IconButton>
          <button
            onClick={() => go(today)}
            className="ml-auto rounded-md border px-2 py-1 text-xs hover:bg-muted"
          >
            오늘
          </button>
        </div>

        {/* 색깔별 카테고리 필터 */}
        <div className="flex flex-col gap-2">
          <span className="text-xs font-medium text-muted-foreground">색깔별 카테고리 필터</span>
          <div className="flex flex-wrap gap-1.5">
            {CATS.map((c) => (
              <button
                key={c}
                onClick={() => setSelected((s) => toggle(s, c))}
                aria-pressed={selected.has(c)}
                className={cn(
                  'flex items-center gap-1.5 rounded-full border px-2 py-1 text-xs transition-all',
                  selected.has(c) && 'border-foreground/30 bg-muted font-medium',
                  selected.size > 0 && !selected.has(c) && 'opacity-40'
                )}
              >
                <span className={cn('size-2 rounded-full', CAT[c].dot)} />
                {CAT[c].label}
              </button>
            ))}
          </div>
          <p className="text-[11px] text-muted-foreground">
            태그를 누르면 해당 색깔의 일정만 표시됩니다. (여러 개 선택 가능, 다시 누르면 해제)
          </p>
        </div>

        {/* '사용자' 탭(좁은 화면 전용): 왼쪽 큰 달력 대신 패널 안에서 날짜를 고른다 */}
        {mode === 'custom' && (
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
          groups.map((g) => (
            <div key={+g.date} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1.5 text-sm font-semibold">
                  {g.badge && (
                    <span
                      className={cn(
                        'size-2 rounded-full',
                        g.badge === 'focus' ? 'bg-red-500' : 'bg-blue-500'
                      )}
                    />
                  )}
                  {format(g.date, 'M월 d일 EEEE', { locale: ko })}
                </span>
                <span
                  className={cn(
                    'rounded px-1.5 py-0.5 text-[10px] font-bold',
                    g.badge === 'focus'
                      ? 'bg-red-500 text-white'
                      : g.badge === 'special'
                        ? 'bg-blue-500 text-white'
                        : 'bg-muted text-muted-foreground'
                  )}
                >
                  {g.badge === 'focus'
                    ? 'FOCUS'
                    : g.badge === 'special'
                      ? 'SPECIAL'
                      : `${g.list.length}건`}
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
                      'block w-full rounded-lg border border-l-2 px-3 py-2 text-left transition-colors hover:brightness-95',
                      c.card
                    )}
                  >
                    <div className="flex items-start justify-between gap-2 text-xs">
                      <span className="flex items-center gap-1.5">
                        <span className={cn('font-semibold tabular-nums', c.text)}>
                          {format(n.publishedAt, 'HH:mm')}
                        </span>
                        <span className={cn('size-1.5 rounded-full', c.dot)} />
                        <span className="text-muted-foreground">{c.label}</span>
                        {n.importance === 3 && <span className={c.text}>★★★</span>}
                      </span>
                      <span className="shrink-0 text-[11px] text-muted-foreground">
                        {n.region}
                      </span>
                    </div>
                    <p className="mt-1 text-sm font-semibold leading-snug">{n.title}</p>
                    <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                      {n.summary}
                    </p>
                  </button>
                )
              })}
            </div>
          ))
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

function IconButton({
  label,
  onClick,
  children,
}: {
  label: string
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      onClick={onClick}
      aria-label={label}
      className="text-muted-foreground hover:text-foreground"
    >
      {children}
    </button>
  )
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
        <Dialog.Popup className="fixed left-1/2 top-1/2 z-50 flex max-h-[85vh] w-[calc(100vw-2rem)] max-w-90 -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-xl border bg-card shadow-lg">
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
  const ticking = useRef(false)
  const [expandedId, setExpandedId] = useState(initialId)

  // 처음 클릭한 카드를 맨 위로
  useEffect(() => {
    scrollRef.current
      ?.querySelector<HTMLElement>(`[data-id="${initialId}"]`)
      ?.scrollIntoView({ block: 'start' })
  }, [initialId])

  // 스크롤하면 맨 위에 걸린 카드가 펼쳐짐
  const onScroll = () => {
    if (ticking.current) return
    ticking.current = true
    requestAnimationFrame(() => {
      ticking.current = false
      const el = scrollRef.current
      if (!el) return
      const cards = [...el.querySelectorAll<HTMLElement>('[data-id]')]
      let top = cards[0]
      for (const card of cards) {
        if (card.offsetTop <= el.scrollTop + 24) top = card
      }
      if (top?.dataset.id && top.dataset.id !== expandedId) {
        setExpandedId(top.dataset.id)
      }
    })
  }

  return (
    <>
      <div className="flex items-center justify-between border-b p-4">
        <Dialog.Title className="text-base font-bold">
          {format(group.date, 'yyyy년 M월 d일 (EEE)', { locale: ko })}
        </Dialog.Title>
        <Dialog.Close
          aria-label="닫기"
          className="text-muted-foreground hover:text-foreground"
        >
          <X className="size-4" />
        </Dialog.Close>
      </div>

      <div
        ref={scrollRef}
        onScroll={onScroll}
        className="relative min-h-0 flex-1 space-y-2 overflow-y-auto p-4"
      >
        {group.list.map((n) => {
          const c = CAT[n.category]
          const isOpen = n.id === expandedId
          return (
            <div
              key={n.id}
              data-id={n.id}
              className={cn(
                'overflow-hidden rounded-lg border border-l-2',
                c.card
              )}
            >
              <button
                type="button"
                onClick={() => setExpandedId(n.id)}
                className="flex w-full items-center justify-between gap-2 p-3 text-left"
              >
                <span className="flex min-w-0 items-center gap-1.5 text-xs">
                  <span
                    className={cn(
                      'shrink-0 rounded px-1.5 py-0.5 font-semibold tabular-nums text-white',
                      c.dot
                    )}
                  >
                    {format(n.publishedAt, 'HH:mm')}
                  </span>
                  <span
                    className={cn(
                      'truncate font-semibold',
                      !isOpen && 'text-muted-foreground'
                    )}
                  >
                    {n.title}
                  </span>
                </span>
                <span className={cn('shrink-0 text-xs', c.text)}>
                  {'★'.repeat(n.importance)}
                  <span className="text-muted-foreground/40">
                    {'★'.repeat(3 - n.importance)}
                  </span>
                </span>
              </button>

              {/* 펼침 영역: grid 0fr → 1fr 로 부드럽게 */}
              <div
                className={cn(
                  'grid transition-[grid-template-rows] duration-300 ease-out',
                  isOpen ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
                )}
              >
                <div className="overflow-hidden">
                  <div className="space-y-2 px-3 pb-3 text-xs">
                    <div className="flex items-center gap-1.5 text-muted-foreground">
                      <span>{c.label}</span>
                      <span>· {n.region}</span>
                    </div>

                    {n.detail &&
                      (n.detail.forecast ||
                        n.detail.previous ||
                        n.detail.source) && (
                        <dl className="flex flex-wrap gap-x-4 gap-y-1">
                          {n.detail.forecast && (
                            <div className="flex gap-1">
                              <dt className="text-muted-foreground">예상치</dt>
                              <dd className="font-medium">{n.detail.forecast}</dd>
                            </div>
                          )}
                          {n.detail.previous && (
                            <div className="flex gap-1">
                              <dt className="text-muted-foreground">이전치</dt>
                              <dd className="font-medium">{n.detail.previous}</dd>
                            </div>
                          )}
                          {n.detail.source && (
                            <div className="flex gap-1">
                              <dt className="text-muted-foreground">발표처</dt>
                              <dd className="font-medium">{n.detail.source}</dd>
                            </div>
                          )}
                        </dl>
                      )}

                    <p className="rounded bg-background/60 p-2 leading-relaxed text-muted-foreground">
                      {n.summary}
                    </p>

                    {n.detail?.sectors && n.detail.sectors.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1">
                        <span className="text-muted-foreground">관련 수혜 섹터</span>
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
        <Dialog.Close className="w-full rounded-md bg-primary py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
          확인
        </Dialog.Close>
      </div>
    </>
  )
}
