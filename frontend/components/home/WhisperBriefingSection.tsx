"use client"

import Link from "next/link"
import { useEffect, useRef, useState, type ReactNode } from "react"
import { format, subMinutes } from "date-fns"
import { Bug } from "lucide-react"

import { Button } from "@/components/ui"
import { calendarHighlight, hotSector } from "@/lib/constant/home"

type ChipTone = "neutral" | "info" | "accent"

const CHIP_TONE_CLASSES: Record<ChipTone, string> = {
  neutral: "bg-neutral-100 text-neutral-600 hover:bg-neutral-200",
  info: "bg-blue-50 text-blue-600 hover:bg-blue-100",
  accent: "bg-point3/60 text-point2 hover:bg-point3",
}

interface WhisperMessage {
  id: string
  relativeLabel: string
  content: ReactNode
  linkHref: string
  linkLabel: string
  tone: ChipTone
}

interface WhisperGroup {
  id: string
  dividerLabel: string
  messages: WhisperMessage[]
}

/** 오늘 날짜의 특정 시:분으로 고정된 Date. 캘린더/장운영처럼 매일 같은 시각에 뜨는 알림에 쓴다. */
function todayAt(hours: number, minutes: number): Date {
  const date = new Date()
  date.setHours(hours, minutes, 0, 0)
  return date
}

function useNow() {
  const [now, setNow] = useState<Date | null>(null)

  useEffect(() => {
    setNow(new Date())
    const timer = setInterval(() => setNow(new Date()), 30_000)
    return () => clearInterval(timer)
  }, [])

  return now
}

const WHISPER_REVEAL_INTERVAL_MS = 450

function useSequentialReveal(count: number) {
  const [visibleCount, setVisibleCount] = useState(0)

  useEffect(() => {
    setVisibleCount(0)
    const timers = Array.from({ length: count }, (_, index) =>
      window.setTimeout(
        () => setVisibleCount((prev) => Math.max(prev, index + 1)),
        index * WHISPER_REVEAL_INTERVAL_MS
      )
    )
    return () => timers.forEach((timer) => window.clearTimeout(timer))
  }, [count])

  return visibleCount
}

function TimeDivider({ label }: { label: string }) {
  return (
    <div className="flex justify-center">
      <span className="rounded-full bg-neutral-200/70 px-3 py-1 text-[11px] font-medium text-neutral-500">
        {label}
      </span>
    </div>
  )
}

function MessageBubble({
  message,
  showHeader,
  visible,
  delayMs,
}: {
  message: WhisperMessage
  showHeader: boolean
  visible: boolean
  delayMs: number
}) {
  return (
    <div
      className={`flex gap-3 ${visible ? "animate-chat-in" : "opacity-0"}`}
      style={visible ? { animationDelay: `${delayMs}ms` } : undefined}
    >
      <div className="w-9 shrink-0">
        {showHeader && (
          <div className="flex size-9 items-center justify-center rounded-lg border-2 border-point bg-point3/50">
            <Bug size={18} className="text-point" />
          </div>
        )}
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        {showHeader && (
          <span className="text-xs font-bold text-neutral-700">
            불개미 대장
          </span>
        )}
        <div className="flex items-end gap-2">
          <div className="flex min-w-0 max-w-[85%] flex-col gap-2.5 rounded-2xl rounded-tl-sm bg-white p-4 shadow-sm">
            <p className="text-xs leading-relaxed text-neutral-700">
              {message.content}
            </p>
            <div className="border-t border-neutral-100 pt-2.5">
              <Button
                render={<Link href={message.linkHref} />}
                nativeButton={false}
                variant="secondary"
                className={`w-fit text-xs ${CHIP_TONE_CLASSES[message.tone]}`}
              >
                {message.linkLabel} →
              </Button>
            </div>
          </div>
          <span className="shrink-0 text-[11px] text-neutral-400">
            {message.relativeLabel}
          </span>
        </div>
      </div>
    </div>
  )
}

export default function WhisperBriefingSection() {
  const now = useNow()

  const relativeDividerLabel = (minutesAgo: number) =>
    now ? `오늘 ${format(subMinutes(now, minutesAgo), "HH:mm")}` : "오늘 --:--"

  const groups: WhisperGroup[] = [
    {
      id: "calendar",
      dividerLabel: `오늘 ${format(todayAt(7, 30), "HH:mm")}`,
      messages: [
        {
          id: "calendar",
          relativeLabel: "07:30",
          tone: "info",
          linkHref: "/calendar",
          linkLabel: "비축 캘린더 일정 확인하기",
          content: (
            <>
              애기 개미님, 오늘 {calendarHighlight.time}에{" "}
              <strong className="font-semibold text-blue-600">
                {calendarHighlight.title}
              </strong>
              가 있어요! 캘린더를 꼭 챙겨보세요 📅
            </>
          ),
        },
      ],
    },
    {
      id: "market-open",
      dividerLabel: `오늘 ${format(todayAt(9, 0), "HH:mm")}`,
      messages: [
        {
          id: "market-open",
          relativeLabel: "09:00",
          tone: "accent",
          linkHref: "/timeline",
          linkLabel: "실시간 페로몬 바로가기",
          content: (
            <>
              애기 개미님, 국장이 열려 있어요! 오늘 하루도 화이팅이에요 🐜
            </>
          ),
        },
      ],
    },
    {
      id: "sector-and-live",
      dividerLabel: relativeDividerLabel(10),
      messages: [
        {
          id: "sector",
          relativeLabel: "10분 전",
          tone: "accent",
          linkHref: "/heatmap",
          linkLabel: "단물 지도에서 확인하기",
          content: (
            <>
              애기 개미님, 오늘{" "}
              <strong className="font-semibold text-point">
                {hotSector.name}
              </strong>{" "}
              섹터가 아주 뜨거워요! 🔥 {hotSector.reason}
            </>
          ),
        },
        {
          id: "live",
          relativeLabel: "방금 전",
          tone: "neutral",
          linkHref: "/timeline",
          linkLabel: "실시간 페로몬 바로가기",
          content: (
            <>
              애기 개미님, 실시간 페로몬 신호가 계속 갱신되고 있으니 놓치지
              말고 확인해 보세요.
            </>
          ),
        },
      ],
    },
  ]

  const totalMessages = groups.reduce(
    (sum, group) => sum + group.messages.length,
    0
  )
  const visibleCount = useSequentialReveal(totalMessages)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = scrollRef.current
    if (!container) return
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" })
  }, [visibleCount])

  let renderedCount = 0

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between gap-3 border-b border-neutral-100 bg-white px-4 py-3.5">
        <div className="flex items-center gap-3">
          <div className="relative flex size-11 shrink-0 items-center justify-center rounded-xl bg-point3/50">
            <Bug size={22} className="text-point" />
            <span className="absolute -right-0.5 -bottom-0.5 size-2.5 rounded-full border-2 border-white bg-emerald-500" />
          </div>
          <div className="flex flex-col gap-0.5">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-sm font-bold">불개미 대장</span>
              <span className="inline-flex items-center gap-1 rounded-full bg-point/10 px-2 py-0.5 text-[11px] font-medium text-point">
                <span className="size-1.5 rounded-full bg-point" />
                실시간 브리핑 중
              </span>
            </div>
            <span className="text-xs text-neutral-400">
              장중 핵심 시그널 귓속말 피드
            </span>
          </div>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex max-h-125 flex-col gap-4 overflow-y-auto bg-ant-bg px-4 py-5"
      >
        {groups.map((group) => (
          <div key={group.id} className="flex flex-col gap-4">
            <TimeDivider label={group.dividerLabel} />
            {group.messages.map((message, index) => {
              const order = renderedCount
              renderedCount += 1
              return (
                <MessageBubble
                  key={message.id}
                  message={message}
                  showHeader={index === 0}
                  visible={visibleCount > order}
                  delayMs={0}
                />
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}
