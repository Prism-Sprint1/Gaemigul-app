"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { Bug, CalendarClock, Radio } from "lucide-react"

import { Button, Card, CardContent } from "@/components/ui"
import {
  calendarHighlight,
  hotSector,
} from "@/lib/constant/home"

interface WhisperCardProps {
  timestamp: string
  message: React.ReactNode
  linkHref: string
  linkLabel: string
}

function WhisperCard({ timestamp, message, linkHref, linkLabel }: WhisperCardProps) {
  return (
    <Card className="rounded-xl border-line-bg py-4 shadow-sm">
      <CardContent className="flex gap-3">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg border-2 border-point bg-point3/50">
          <Bug size={18} className="text-point" />
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-2.5">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-bold">불개미 대장</span>
            <span className="text-[11px] text-neutral-400">{timestamp}</span>
          </div>
          <p className="text-sm leading-relaxed text-neutral-700">{message}</p>
          <Button
            render={<Link href={linkHref} />}
            nativeButton={false}
            variant="secondary"
            className="w-fit bg-point3/60 text-point2 hover:bg-point3"
          >
            {linkLabel} →
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function useCurrentHour() {
  const [hour, setHour] = useState<number | null>(null)

  useEffect(() => {
    const update = () => setHour(new Date().getHours())
    update()
    const timer = setInterval(update, 60_000)
    return () => clearInterval(timer)
  }, [])

  return hour
}

export default function WhisperBriefingSection() {
  const hour = useCurrentHour()

  return (
    <section className="flex flex-col gap-4">
      <h2 className="flex items-center gap-1.5 text-base font-bold">
        <Radio size={16} className="text-point" />
        불개미 대장의 실시간 귓속말 브리핑
      </h2>

      <div className="flex flex-col gap-3">
        <WhisperCard
          timestamp="방금 전"
          message={
            <>
              애기 개미님, 지금 현재 {hour ?? "--"}시입니다. 실시간 페로몬
              신호가 계속 갱신되고 있으니 놓치지 말고 확인해 보세요.
            </>
          }
          linkHref="/timeline"
          linkLabel="실시간 페로몬 바로가기"
        />

        <WhisperCard
          timestamp="10분 전"
          message={
            <>
              애기 개미님, 오늘{" "}
              <strong className="font-semibold text-point">
                {hotSector.name}
              </strong>{" "}
              섹터가 아주 뜨거워요! 🔥 {hotSector.reason}
            </>
          }
          linkHref="/heatmap"
          linkLabel="단물 지도에서 확인하기"
        />

        <WhisperCard
          timestamp="30분 전"
          message={
            <>
              애기 개미님, 오늘 {calendarHighlight.time}에{" "}
              <strong className="font-semibold text-point">
                {calendarHighlight.title}
              </strong>
              가 있어요! 캘린더를 꼭 챙겨보세요{" "}
              <CalendarClock size={14} className="inline-block align-text-bottom" />
            </>
          }
          linkHref="/calendar"
          linkLabel="비축 캘린더 일정 확인하기"
        />
      </div>
    </section>
  )
}
