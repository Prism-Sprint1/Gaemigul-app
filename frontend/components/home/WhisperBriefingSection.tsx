"use client"

import Image from "next/image"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react"

import { Button, Separator, Skeleton } from "@/components/ui"
import { getTimelineDay } from "@/lib/api/timeline"
import { cn } from "@/lib/utils"
import type { ApiTimelineSlot } from "@/lib/types/TimelineType"
import { ArrowRight, MessageCircle, X } from "lucide-react"

type ChipTone = "neutral" | "info" | "accent"

const CHIP_TONE_CLASSES: Record<ChipTone, string> = {
  neutral: "bg-neutral-100 text-neutral-600 hover:bg-neutral-200",
  info: "bg-blue-50 text-blue-600 hover:bg-blue-100",
  accent: "bg-point3/60 text-point2 hover:bg-point3",
}

const TONE_ORDER: ChipTone[] = ["accent", "info", "neutral"]

interface WhisperMessage {
  id: string
  relativeLabel: string
  content: ReactNode
  linkHref: string
  linkLabel: string
  tone: ChipTone
  /** 이동 대상 타임라인 섹션의 앵커 id(슬롯 키). 같은 페이지에 있을 때 스크롤로만 이동시키는 데 쓴다. */
  anchorId: string
}

interface WhisperGroup {
  id: string
  dividerLabel: string
  messages: WhisperMessage[]
}

/** 슬롯 하나(제목·부제)를 채팅 말풍선 1~2개로 변환한다. 부제가 있으면 헤드라인 바로 다음 말풍선으로 이어붙인다. */
function slotToGroup(
  slot: ApiTimelineSlot,
  index: number
): WhisperGroup | null {
  if (!slot.briefing_headline) return null

  const tone = TONE_ORDER[index % TONE_ORDER.length]
  const linkHref = `/timeline#${slot.slot_key}`
  const messages: WhisperMessage[] = [
    {
      id: `${slot.slot_key}-headline`,
      relativeLabel: slot.time_slot,
      tone,
      linkHref,
      anchorId: slot.slot_key,
      linkLabel: `${slot.title} 자세히 보기`,
      content: <>{slot.briefing_headline}</>,
    },
  ]

  if (slot.briefing_subtitle) {
    messages.push({
      id: `${slot.slot_key}-subtitle`,
      relativeLabel: slot.time_slot,
      tone,
      linkHref,
      anchorId: slot.slot_key,
      linkLabel: `${slot.title} 자세히 보기`,
      content: <>{slot.briefing_subtitle}</>,
    })
  }

  return {
    id: slot.slot_key,
    dividerLabel: `오늘 ${slot.time_slot}`,
    messages,
  }
}

function useTodayTimeline() {
  const [slots, setSlots] = useState<ApiTimelineSlot[] | null>(null)
  const [loadError, setLoadError] = useState(false)

  const fetchTimeline = useCallback(async () => {
    try {
      const data = await getTimelineDay()
      setSlots(data)
      setLoadError(false)
    } catch (error) {
      console.error("[getTimelineDay] 실패", error)
      setLoadError(true)
    }
  }, [])

  useEffect(() => {
    fetchTimeline()
    const timer = setInterval(fetchTimeline, 60_000)
    return () => clearInterval(timer)
  }, [fetchTimeline])

  return { slots, loadError }
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

const TIMELINE_PAGE_PATH = "/timeline"

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
  const router = useRouter()
  const pathname = usePathname()

  const handleClick = (event: React.MouseEvent) => {
    // 이미 타임라인 페이지라면 새로 이동하지 않고 해당 섹션으로 바로 스크롤한다.
    if (pathname === TIMELINE_PAGE_PATH) {
      event.preventDefault()
      document.getElementById(message.anchorId)?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      })
      router.replace(message.linkHref, { scroll: false })
    }
  }

  return (
    <div
      className={`flex gap-2 ${visible ? "animate-chat-in" : "opacity-0"}`}
      style={visible ? { animationDelay: `${delayMs}ms` } : undefined}
    >
      <div className="w-9 shrink-0">
        {showHeader && (
          <div className="relative size-9 overflow-hidden rounded-full">
            <Image
              src="/images/profile.png"
              alt="불개미 대장"
              fill
              className="object-cover"
            />
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
          <div
            className={`flex max-w-[85%] min-w-0 flex-col gap-2.5 rounded-2xl bg-white p-3 shadow-sm ${showHeader ? "rounded-tl-xs" : "rounded-tl-lg"}`}
          >
            <p className="text-justify text-xs leading-relaxed font-medium text-neutral-700">
              {message.content}
            </p>
            <Separator className="opacity-50" />
            <Button
              render={<Link href={message.linkHref} />}
              nativeButton={false}
              variant="secondary"
              onClick={handleClick}
              className={`w-fit text-[11px] ${CHIP_TONE_CLASSES[message.tone]}`}
            >
              {message.linkLabel}
              <ArrowRight className="h-3! w-3!" />
            </Button>
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
  // 모바일 전용 상태. xl 이상(데스크톱)에서는 항상 인라인으로 펼쳐져 있어 쓰이지 않는다.
  const [isOpen, setIsOpen] = useState(false)
  const { slots, loadError } = useTodayTimeline()

  const groups: WhisperGroup[] =
    slots
      ?.map(slotToGroup)
      .filter((group): group is WhisperGroup => group !== null) ?? []

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
    <>
      {/* 모바일 전용 배경: 챗이 열려 있을 때 탭하면 닫힌다. 데스크톱에는 영향 없음. */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm xl:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      <div
        className={cn(
          "flex flex-col overflow-hidden",
          isOpen
            ? "fixed inset-x-4 bottom-24 z-50 h-[70vh] rounded-2xl border border-line-bg bg-white shadow-xl"
            : "hidden",
          "xl:static xl:z-auto xl:flex xl:h-auto xl:w-auto xl:rounded-none xl:border-none xl:bg-transparent xl:shadow-none"
        )}
      >
        <div className="flex items-center justify-between gap-3 border-b border-neutral-100 bg-white px-4 py-3.5">
          <div className="flex w-full items-center gap-2">
            <div className="relative size-9 shrink-0">
              <Image
                src="/images/profile.png"
                alt="불개미 대장"
                fill
                className="rounded-full object-cover"
              />
              <span className="absolute -right-px -bottom-0.5 size-3 rounded-full border-2 border-white bg-emerald-500" />
            </div>
            <div className="flex w-full flex-col">
              <div className="flex flex-wrap items-center justify-between">
                <span className="text-sm font-bold">불개미 대장</span>
                <span className="inline-flex items-center gap-1 rounded-full bg-point/10 px-2 py-0.5 text-[10px] font-medium text-point">
                  <span className="size-1.5 rounded-full bg-point" />
                  실시간 브리핑 중
                </span>
              </div>
              <span className="text-xs text-neutral-400">
                장중 핵심 시그널 귓속말 피드
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            className="flex size-7 shrink-0 items-center justify-center rounded-full text-neutral-400 hover:bg-neutral-100 xl:hidden"
            aria-label="대장 챗 닫기"
          >
            <X size={16} />
          </button>
        </div>

        <div
          ref={scrollRef}
          className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto bg-ant-bg px-4 py-5 xl:max-h-125 xl:flex-none"
        >
          {slots === null && !loadError ? (
            <div className="flex flex-col gap-4">
              <Skeleton className="mx-auto h-5 w-24 rounded-full" />
              <div className="flex gap-3">
                <Skeleton className="size-9 shrink-0 rounded-full" />
                <Skeleton className="h-16 w-2/3 rounded-2xl" />
              </div>
              <div className="flex gap-3">
                <div className="w-9 shrink-0" />
                <Skeleton className="h-12 w-1/2 rounded-2xl" />
              </div>
            </div>
          ) : loadError && groups.length === 0 ? (
            <p className="py-6 text-center text-xs text-neutral-400">
              브리핑을 불러오지 못했어요. 잠시 후 다시 시도해 주세요.
            </p>
          ) : groups.length === 0 ? (
            <p className="py-6 text-center text-xs text-neutral-400">
              아직 브리핑이 준비되지 않았어요. 07:30에 첫 소식을 전해드릴게요!
            </p>
          ) : (
            groups.map((group) => (
              <div key={group.id} className="flex flex-col gap-4">
                <TimeDivider label={group.dividerLabel} />
                {group.messages.map((message, index) => {
                  // 맨 마지막(가장 최근) 말풍선부터 fadeUp되도록 노출 순서를 뒤집는다.
                  const order = totalMessages - 1 - renderedCount
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
            ))
          )}
        </div>
      </div>

      {/* 모바일 전용 플로팅 버튼: 챗을 열고 닫는다. 데스크톱에서는 항상 인라인으로 보여서 필요 없다. */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={isOpen ? "대장 챗 닫기" : "대장 챗 열기"}
        className="fixed right-3 bottom-4 z-50 flex size-14 items-center justify-center rounded-full bg-point text-white shadow-lg transition-transform active:scale-95 xl:hidden"
      >
        {isOpen ? (
          <X size={24} />
        ) : (
          <>
            <MessageCircle size={24} />
            <span className="absolute top-0 right-0 size-3 rounded-full border-2 border-white bg-emerald-500" />
          </>
        )}
      </button>
    </>
  )
}
