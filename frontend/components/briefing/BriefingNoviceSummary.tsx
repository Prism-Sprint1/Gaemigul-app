import type { BriefingContent } from "@/lib/types/BriefingType"
import { BriefingGlossary } from "@/components/briefing"
import { briefingContent } from "@/lib/constant/briefingContent"

import { Separator } from "../ui"

type BriefingNoviceSummaryProps = {
  summary: BriefingContent["noviceSummary"]
}

export default function BriefingNoviceSummary({
  summary,
}: BriefingNoviceSummaryProps) {
  return (
    <article
      id="article-04"
      className="flex scroll-mt-24 flex-col gap-4 rounded-lg bg-white p-5 shadow-sm"
    >
      <div className="flex items-center gap-2">
        <span className="text-baisc flex size-9 items-center justify-center rounded-md bg-point2 font-bold text-white">
          04
        </span>
        <h2 className="text-basic flex flex-col font-bold">
          <span className="text-xs font-semibold text-point2">
            ANTHILL NOVICE SUMMARY
          </span>
          초보 개미도 30초 안에 이해하는 한 줄 결론!
        </h2>
      </div>
      <Separator className="bg-line-bg/50" />

      <p className="text-sm leading-relaxed whitespace-pre-line text-neutral-600">
        {summary.quote}
      </p>

      <div className="flex flex-col gap-2">
        <p className="text-sm font-bold">
          ⚡ 지금 뭘 해야 하나요? 딱 이것만 외우세요!
        </p>
        <ol className="flex flex-col gap-3">
          {summary.todoItems.map((item, index) => (
            <li
              key={item.title}
              className="flex gap-3 rounded-lg border border-neutral-200 p-3 shadow-sm"
            >
              <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-point text-xs font-bold text-white">
                {index + 1}
              </span>
              <div className="flex flex-col gap-0.5">
                <p className="text-sm font-semibold">{item.title}</p>
                <p className="text-xs leading-relaxed text-neutral-500">
                  {item.description}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </div>

      <BriefingGlossary terms={briefingContent.glossary} />
    </article>
  )
}
