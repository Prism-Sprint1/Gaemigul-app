import { Separator } from "@/components/ui"
import type { BeginnerSummary } from "@/lib/types/TimelineType"

type BeginnerSummarySectionProps = {
  summary: BeginnerSummary
}

export default function BeginnerSummarySection({
  summary,
}: BeginnerSummarySectionProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-1.5 text-lg font-bold text-decrease">
        <span aria-hidden>🌱</span>
        주린이를 위한 해설
      </div>
      <p className="text-sm font-semibold text-neutral-700">{summary.title}</p>
      <p className="text-xs text-neutral-500">{summary.subtitle}</p>
      <div className="grid gap-3 sm:grid-cols-3">
        {summary.points.map((point, index) => (
          <div
            key={point.id}
            className="relative flex flex-col gap-2 overflow-hidden rounded-lg border border-neutral-200 bg-white p-4 before:absolute before:inset-x-0 before:top-0 before:h-1 before:bg-decrease before:content-['']"
          >
            <div className="flex items-center gap-2">
              <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-decrease/10 text-[10px] font-bold text-decrease">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="text-sm font-semibold">{point.title}</span>
            </div>
            <p className="text-xs leading-relaxed text-neutral-500">
              {point.description}
            </p>
            <Separator />
            <div className="flex flex-wrap gap-1.5">
              {point.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-neutral-200 bg-neutral-50 px-2 py-0.5 text-[10px] text-neutral-500"
                >
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
