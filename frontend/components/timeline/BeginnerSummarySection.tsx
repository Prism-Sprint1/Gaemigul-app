import type { BeginnerSummary } from "@/lib/types/TimelineType"

type BeginnerSummarySectionProps = {
  summary: BeginnerSummary
}

export default function BeginnerSummarySection({
  summary,
}: BeginnerSummarySectionProps) {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-decrease/20 bg-decrease/5 p-5">
      <div className="flex items-center gap-1.5 text-base font-bold text-decrease">
        <span aria-hidden>🌱</span>
        주린이 해설 요약
      </div>
      <p className="text-sm font-semibold">{summary.title}</p>
      <p className="text-sm leading-relaxed text-neutral-600">
        {summary.description}
      </p>
      <ul className="mt-1 flex flex-col gap-1">
        {summary.bullets.map((bullet) => (
          <li key={bullet} className="flex gap-1.5 text-xs text-neutral-500">
            <span className="text-decrease">•</span>
            {bullet}
          </li>
        ))}
      </ul>
    </div>
  )
}
