"use client"

import { useEffect, useRef, useState } from "react"

const INTERVAL_MS = 30 * 60 * 1000 // 30분

/** 다음 정시 기준 30분 경계(매시 00분, 30분)까지 남은 시간(ms) */
function getMsUntilNextBoundary(now = Date.now()) {
  return INTERVAL_MS - (now % INTERVAL_MS)
}

function formatRemaining(ms: number) {
  const totalSeconds = Math.max(0, Math.ceil(ms / 1000))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  const pad = (n: number) => n.toString().padStart(2, "0")
  return `${pad(minutes)}:${pad(seconds)}`
}

/**
 * 정시 기준 30분 간격에 맞춰
 * - 남은 시간을 "MM:SS" 문자열로 반환하고
 * - 매 경계 시점마다 onTick 콜백을 실행한다.
 */
export function useIndicatorSchedule(onTick?: () => void) {
  const [remaining, setRemaining] = useState<string>("--:--")
  const onTickRef = useRef(onTick)
  onTickRef.current = onTick

  useEffect(() => {
    let boundary = Date.now() + getMsUntilNextBoundary()

    const update = () => {
      const now = Date.now()
      if (now >= boundary) {
        onTickRef.current?.()
        boundary = now + getMsUntilNextBoundary(now)
      }
      setRemaining(formatRemaining(boundary - now))
    }

    update()
    const id = window.setInterval(update, 1000)
    return () => window.clearInterval(id)
  }, [])

  return { remaining }
}
