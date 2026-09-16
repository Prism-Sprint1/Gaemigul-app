"use client"

import { useEffect, useState } from "react"
import { Globe } from "lucide-react"

import { cn } from "@/lib/utils"
import { getMarketSessionState, type ActiveMarket } from "@/lib/market-session"
import DashboardCard from "./DashboardCard"

function useNowMinutes() {
  const [minutes, setMinutes] = useState<number | null>(null)

  useEffect(() => {
    const update = () => {
      const now = new Date()
      setMinutes(now.getHours() * 60 + now.getMinutes())
    }
    update()
    const timer = setInterval(update, 30_000)
    return () => clearInterval(timer)
  }, [])

  return minutes
}

function SessionPill({
  label,
  active,
}: {
  label: string
  active: boolean
}) {
  return (
    <div
      className={cn(
        "flex flex-1 items-center justify-center rounded-lg py-2 text-sm font-semibold transition-colors duration-300",
        active
          ? "bg-point text-white shadow-sm"
          : "bg-transparent text-neutral-400"
      )}
    >
      {label}
    </div>
  )
}

export default function MarketSessionCard() {
  const minutes = useNowMinutes()
  const state = minutes !== null ? getMarketSessionState(minutes) : null
  const active: ActiveMarket = state?.active ?? "domestic"

  return (
    <DashboardCard icon={<Globe size={16} className="text-point" />} title="글로벌 장운영 현황">
      <div className="flex flex-col gap-3">
        <p className="flex items-center gap-1.5 text-xs font-medium text-neutral-500">
          <span className="relative flex size-1.5">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-point opacity-75" />
            <span className="relative inline-flex size-1.5 rounded-full bg-point" />
          </span>
          {state?.caption ?? "장운영 정보를 불러오는 중이에요."}
        </p>
        <div className="flex gap-1 rounded-xl bg-neutral-100 p-1">
          <SessionPill label="국장" active={active === "domestic"} />
          <SessionPill label="미장" active={active === "us"} />
        </div>
      </div>
    </DashboardCard>
  )
}
