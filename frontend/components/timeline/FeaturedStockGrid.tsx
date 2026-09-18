import { cn } from "cn"

import { Badge } from "@/components/ui"
import type { FeaturedStock } from "@/lib/types/TimelineType"
import { isPositiveRate } from "./utils"

type FeaturedStockGridProps = {
  stocks: FeaturedStock[]
}

export default function FeaturedStockGrid({ stocks }: FeaturedStockGridProps) {
  return (
    <div className="flex flex-col gap-3">
      <h3 className="text-base font-bold">특징주</h3>
      <div className="grid gap-3 sm:grid-cols-3">
        {stocks.map((stock) => {
          const positive = isPositiveRate(stock.rate)

          return (
            <div
              key={stock.id}
              className="flex flex-col gap-3 rounded-lg border border-neutral-200 bg-white p-4"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold">{stock.name}</span>
                <Badge className="bg-neutral-100 text-[10px] text-neutral-500">
                  {stock.badge}
                </Badge>
              </div>
              <div className="flex items-end justify-between">
                <strong className="text-lg font-bold">{stock.price}</strong>
                <span
                  className={cn(
                    "text-sm font-semibold",
                    positive ? "text-increase" : "text-decrease"
                  )}
                >
                  {stock.rate}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
