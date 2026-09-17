const LEGEND_COLORS = ["#2563eb", "#395fa9", "#4b5563", "#ab4447", "#ff2a2a"]

export default function HeatmapLegend() {
  return (
    <div
      className="mb-3 flex w-full flex-col gap-1"
      aria-label="등락률 색상 범례"
    >
      <div className="flex justify-between text-[10px] text-neutral-500">
        <span>-5% 이하</span>
        <span>0%</span>
        <span>+5% 이상</span>
      </div>
      <div
        className="flex h-1.5 w-full overflow-hidden rounded-sm"
        aria-hidden="true"
      >
        {LEGEND_COLORS.map((color) => (
          <span
            key={color}
            className="flex-1"
            style={{ backgroundColor: color }}
          />
        ))}
      </div>
    </div>
  )
}

export function HeatmapLegendFootnote() {
  return (
    <p className="mt-2 text-[10px] leading-5 text-neutral-400">
      기업은 각 업종의 시가총액 상위 5개이며, 상승률 1위는 표시 범위와 관계없이
      전체 대상 업종을 비교합니다. 업종 등락률은 선택한 기간의 종목 등락률을
      시가총액으로 가중 평균한 값입니다. 면적은 시가총액 순서를 유지하면서 40%를
      균등 배분해 크기 차이를 완화했습니다. 실제 시가총액은 종목 상세에서
      확인하세요. 회색은 보합 또는 등락률 미제공입니다.
    </p>
  )
}
