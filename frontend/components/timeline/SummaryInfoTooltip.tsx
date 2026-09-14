"use client"

import { Info } from "lucide-react"

export default function SummaryInfoTooltip() {
  return (
    <div className="group relative shrink-0">
      <button
        type="button"
        aria-label="AI 요약 안내"
        className="flex size-6 cursor-pointer items-center justify-center rounded-full text-neutral-300 transition-colors duration-200 hover:text-neutral-400"
      >
        <Info size={16} />
      </button>
      <div className="pointer-events-none absolute top-full right-0 z-10 mt-2 w-114 rounded-lg border border-neutral-200 bg-white p-3 text-[12px] leading-relaxed text-neutral-500 opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100">
        <p className="mb-1 font-semibold text-neutral-700">🐜 개미봇 알림</p>
        <p>
          AI 개미가 빠르게 훑어온 요약 정보입니다. <br />
          시장 탐색용으로 가볍게 참고해 주시고, 최종 투자 결정과 책임은 투자자
          본인에게 있습니다.
        </p>
      </div>
    </div>
  )
}
