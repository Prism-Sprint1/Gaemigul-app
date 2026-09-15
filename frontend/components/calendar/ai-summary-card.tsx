"use client"

import { cn } from "@/lib/utils"
import { CAT, type Category } from "@/app/(main)/calendar/news-data"

/** 더미 데이터 — 실제 AI 요약 생성 로직은 아직 없음 */
const AI_WEEKLY_SUMMARY: { category: Category; title: string; desc: string }[] =
  [
    {
      category: "macro",
      title: "미국 GDP 성장률 수정치 발표",
      desc: "나라 경제가 얼마나 컸는지 다시 계산해 발표해요. 예상보다 높으면 증시엔 호재예요.",
    },
    {
      category: "rate",
      title: "한국 기준금리 동결 전망",
      desc: "이번엔 금리를 그대로 유지할 가능성이 커요. 대출·예금 이자는 큰 변화가 없을 거예요.",
    },
    {
      category: "macro",
      title: "미국 PCE 물가지수 발표",
      desc: "연준이 가장 참고하는 물가 지표예요. 수치가 낮게 나오면 금리 인하 기대가 커져요.",
    },
    {
      category: "dividend",
      title: "국내 배당주 배당락일",
      desc: "이 날 이후에 사면 이번 배당은 못 받아요. 배당을 노린다면 그 전에 미리 사두세요.",
    },
    {
      category: "earnings",
      title: "엔비디아 실적 발표",
      desc: "AI 반도체 수요가 여전한지 확인하는 빅이벤트예요. 국내 반도체 관련주에도 영향이 커요.",
    },
    {
      category: "optionExpiry",
      title: "미국 옵션 만기일",
      desc: "이 날은 주가가 평소보다 크게 출렁일 수 있어요. 급등락에 놀라지 않게 대비해두세요.",
    },
  ]

/** 더미 카드 — 클릭 없이 한눈에 보이는 이번 주 AI 요약 목록 */
export function AiSummaryCard() {
  return (
    <div className="rounded-xl border bg-primary/5 p-3 sm:p-4">
      <div className="mb-2 flex items-center justify-start gap-1.5 truncate text-left text-xs font-semibold whitespace-nowrap text-primary">
        <span className="shrink-0">✨</span>
        이번주 AI 요약
      </div>
      <ul className="flex flex-col gap-2.5">
        {AI_WEEKLY_SUMMARY.map((s, i) => (
          <li key={i} className="flex flex-col gap-0.5">
            <div className="flex items-center gap-1.5 text-[12px] font-semibold text-foreground">
              <span
                className={cn(
                  "size-1.5 shrink-0 rounded-full",
                  CAT[s.category].dot
                )}
              />
              {s.title}
            </div>
            <p className="pl-3 text-[11px] leading-snug break-keep text-muted-foreground">
              {s.desc}
            </p>
          </li>
        ))}
      </ul>
    </div>
  )
}
