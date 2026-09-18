import { heatmapColor } from "@/lib/heatmap-layout"

const RATES = [-5, -2.5, 0, 2.5, 5]

export default function HeatmapLegend() {
  return (
    <div
      className="w-36 shrink-0"
      aria-label="등락률: 파랑은 하락, 회색은 보합 또는 미제공, 빨강은 상승"
    >
      <div className="mb-1 flex justify-between text-[9px] font-medium text-slate-500 tabular-nums">
        <span>−5% 이하</span>
        <span>0%</span>
        <span>+5% 이상</span>
      </div>
      <div className="flex h-1 overflow-hidden rounded-sm" aria-hidden="true">
        {RATES.map((rate) => (
          <span
            key={rate}
            className="flex-1"
            style={{ backgroundColor: heatmapColor(rate) }}
          />
        ))}
      </div>
    </div>
  )
}

export function HeatmapLegendFootnote() {
  return (
    <details className="group mt-4 border-t border-heatmap-border/60 pt-3 text-xs text-slate-500">
      <summary className="w-fit cursor-pointer rounded py-1 font-medium outline-offset-4 focus-visible:outline-slate-700">
        데이터와 표시 기준
      </summary>
      <ul className="mt-2 space-y-1.5 pl-4 leading-6">
        <li>
          기업 5개 이상인 업종 중 시가총액 상위 15개와 업종별 상위 5개 기업을
          표시합니다.
        </li>
        <li>
          상승률 1위는 표시 범위와 관계없이 전체 대상 업종을 비교합니다. 업종
          등락률은 종목 등락률의 시가총액 가중 평균입니다.
        </li>
        <li>
          작은 업종도 읽을 수 있도록 면적 차이를 완화했습니다. 시가총액 순서는
          유지되며 실제 금액은 종목 상세에서 확인할 수 있습니다.
        </li>
        <li>
          빨강은 상승, 파랑은 하락입니다. 회색은 보합 또는 등락률 미제공이며,
          미제공 값은 —로 표시합니다.
        </li>
      </ul>
    </details>
  )
}
