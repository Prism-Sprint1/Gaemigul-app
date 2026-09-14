import { ArrowRight } from "lucide-react"
import { cn } from "cn"

import type { MarketStatGroup } from "@/lib/types/TimelineType"
import { formatValueDelta } from "./utils"

type MarketStatGridProps = {
  groups: MarketStatGroup[]
}

export default function MarketStatGrid({ groups }: MarketStatGridProps) {
  const totalStats = groups.reduce((sum, group) => sum + group.stats.length, 0)

  return (
    <div className="flex flex-col gap-2">
      <div
        className="grid gap-3"
        style={{ gridTemplateColumns: `repeat(${totalStats}, minmax(7rem, 1fr))` }}
      >
        {groups.map((group) => (
          <span
            key={group.groupLabel}
            className="text-xs font-medium text-neutral-400"
            style={{ gridColumn: `span ${group.stats.length}` }}
          >
            {group.groupLabel}
          </span>
        ))}
      </div>
      <div
        className="grid gap-3 overflow-x-auto"
        style={{ gridTemplateColumns: `repeat(${totalStats}, minmax(7rem, 1fr))` }}
      >
        {groups.flatMap((group) =>
          group.stats.map((stat) => (
            <div
              key={`${group.groupLabel}-${stat.label}`}
              className="rounded-lg border border-neutral-200 bg-white px-4 py-3"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-medium text-neutral-500">
                  {stat.label}
                </span>
                <span
                  className={cn(
                    "text-xs font-semibold",
                    stat.isPositive ? "text-increase" : "text-decrease"
                  )}
                >
                  {stat.rate}
                </span>
              </div>
              <strong className="mt-1 block text-lg font-bold">
                {stat.value}
              </strong>
              {stat.previousValue && (
                <div className="mt-1.5 flex items-center gap-2 border-t border-neutral-100 pt-1.5 text-[11px]">
                  <span className="flex items-center gap-1">
                    <span className="text-neutral-400">
                      {stat.previousLabel ?? "07:30"}
                    </span>
                    <span className="font-semibold text-neutral-700">
                      {stat.previousValue}
                    </span>
                  </span>
                  <ArrowRight size={10} className="shrink-0 text-neutral-300" />
                  <span
                    className={cn(
                      "font-semibold",
                      stat.isPositive ? "text-increase" : "text-decrease"
                    )}
                  >
                    {formatValueDelta(stat.value, stat.previousValue)}
                  </span>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
