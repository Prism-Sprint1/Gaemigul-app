import { Info } from "lucide-react"
import { formatChange, formatKoreanAmount } from "@/lib/heatmap-layout"
import type { HeatmapSector, HeatmapStock } from "@/lib/types/HeatmapType"

function changeColor(rate: number | null) {
  if (rate === null || rate === 0) return "#737373"
  return rate > 0 ? "#e52828" : "#2563eb"
}

export default function HeatmapStockDetail({
  id,
  selected,
}: {
  id: string
  selected: { sector: HeatmapSector; stock: HeatmapStock } | undefined
}) {
  return (
    <div
      id={id}
      className="mb-3 min-h-16.25 w-full flex-1 rounded-sm border border-neutral-200 bg-white px-3 py-3 shadow-sm"
      aria-live="polite"
    >
      {selected ? (
        <div className="grid grid-cols-2 gap-x-5 gap-y-2 text-xs sm:grid-cols-[1.3fr_1fr_1fr_1fr]">
          <div>
            <p className="text-xs text-neutral-400">
              {selected.sector.name} · {selected.stock.code}
            </p>
            <strong className="flex items-center gap-1.5 text-sm">
              <p className="mt-1 truncate font-bold">{selected.stock.name}</p>
              <p
                className="mt-0.5 font-semibold tabular-nums"
                style={{ color: changeColor(selected.stock.change_rate) }}
              >
                {formatChange(selected.stock.change_rate)}
              </p>
            </strong>
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
        <div className="flex gap-2 text-xs leading-relaxed text-neutral-400">
          <Info className="relative top-1 size-3 shrink-0" />
          <p>
            종목을 가리키거나 선택하면 상세 정보를 볼 수 있어요.
            <br />
            작은 종목은 업종 확대 또는 검색으로 확인하세요.
          </p>
        </div>
      )}
    </div>
  )
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-neutral-400">{label}</p>
      <p className="mt-1 text-sm font-semibold tabular-nums">{value}</p>
    </div>
  )
}
