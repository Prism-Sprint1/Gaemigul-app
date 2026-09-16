import { Activity } from "lucide-react"

import { antColonySentiment, getSentimentLevel } from "@/lib/constant/home"
import DashboardCard from "./DashboardCard"

const SCALE_LABELS = ["공포", "중립", "탐욕"]

export default function AntColonySentimentCard() {
  const { value, description } = antColonySentiment
  const level = getSentimentLevel(value)
  const pointerPercent = Math.min(100, Math.max(0, value))

  return (
    <DashboardCard
      icon={<Activity size={16} className="text-point" />}
      title="개미굴 심리지수"
    >
      <div className="flex flex-col gap-4">
        <p className="flex items-baseline gap-2">
          <span className="text-2xl font-bold" style={{ color: level.color }}>
            {value}
          </span>
          <span className="text-sm font-semibold text-neutral-400">
            ({level.label})
          </span>
        </p>

        <div className="flex flex-col gap-2">
          <div className="relative h-2 w-full rounded-full bg-linear-[90deg,#4A90D9_0%,#6FCF97_25%,#9CA3AF_50%,#F0A63E_75%,#FF2A2A_100%] opacity-80">
            <div
              className="absolute top-1/2 size-4 -translate-y-1/2 rounded-full border-2 bg-white shadow transition-[left,border-color] duration-500"
              style={{
                left: `calc(${pointerPercent}% - 8px)`,
                borderColor: level.color,
              }}
            />
          </div>
          <div className="flex justify-between text-[11px] text-neutral-400">
            {SCALE_LABELS.map((label) => (
              <span key={label}>{label}</span>
            ))}
          </div>
        </div>

        <p className="text-xs text-neutral-500">{description}</p>
      </div>
    </DashboardCard>
  )
}
