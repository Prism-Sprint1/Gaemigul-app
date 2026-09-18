import { MousePointer2 } from "lucide-react"
import { formatChange, formatKoreanAmount } from "@/lib/heatmap-layout"
import type { HeatmapSector, HeatmapStock } from "@/lib/types/HeatmapType"

export default function HeatmapStockDetail({
  id,
  selected,
}: {
  id: string
  selected: { sector: HeatmapSector; stock: HeatmapStock } | undefined
}) {
  const rate = selected?.stock.change_rate
  return (
    <div
      id={id}
      className="flex min-h-32 items-center rounded-xl border border-heatmap-border bg-heatmap-panel px-4 py-3 sm:min-h-24"
      aria-live="polite"
      aria-atomic="true"
    >
      {selected ? (
        <div className="grid w-full grid-cols-2 gap-x-4 gap-y-3 text-xs sm:grid-cols-[1.3fr_1fr_1fr_1fr]">
          <div className="min-w-0">
            <p className="truncate text-[11px] text-slate-500">
              {selected.sector.name} · {selected.stock.code}
            </p>
            <p
              className="mt-1 truncate text-sm font-bold text-slate-900"
              title={selected.stock.name}
            >
              {selected.stock.name}
            </p>
            <p
              className={`mt-0.5 text-xs font-semibold tabular-nums ${rate == null || rate === 0 ? "text-slate-500" : rate > 0 ? "text-red-700" : "text-blue-700"}`}
            >
              {formatChange(rate ?? null)}
            </p>
          </div>
          <Detail
            label="현재가"
            value={`${selected.stock.price.toLocaleString("ko-KR")}원`}
          />
          <Detail
            label="시가총액"
            value={formatKoreanAmount(selected.stock.market_cap)}
          />
          <Detail
            label="선택 기간 거래량"
            value={formatKoreanAmount(selected.stock.volume, "주")}
          />
        </div>
      ) : (
        <div className="flex items-center gap-3">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-white text-slate-400">
            <MousePointer2 className="size-4" aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-medium text-slate-700">
              관심 있는 기업을 선택해 보세요
            </p>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              현재가·시가총액·거래량을 여기서 확인할 수 있어요.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <p className="text-[11px] text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold break-keep text-slate-800 tabular-nums">
        {value}
      </p>
    </div>
  )
}
