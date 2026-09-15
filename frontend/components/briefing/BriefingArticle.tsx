import type { CSSProperties } from "react"

import type { BriefingArticle as BriefingArticleType } from "@/lib/types/BriefingType"
import { getBriefingAccentColor } from "./accentColors"
import BriefingCorrelationChart from "./BriefingCorrelationChart"
import BriefingStatCards from "./BriefingStatCards"
import BriefingTakeaway from "./BriefingTakeaway"

import { Separator } from "../ui"

type BriefingArticleProps = {
  /** 0-based 순서. 강조 색상을 순환 선택하는 데 사용한다. */
  id: number
  article: BriefingArticleType
}

export default function BriefingArticle({ id, article }: BriefingArticleProps) {
  const accentColor = getBriefingAccentColor(id)
  const accentStyle = { "--briefing-accent": accentColor } as CSSProperties

  return (
    <article
      id={article.id}
      style={accentStyle}
      className="flex scroll-mt-24 flex-col gap-4 rounded-lg bg-white p-5 shadow-sm"
    >
      <div className="flex items-center gap-2">
        <span className="text-baisc flex size-9 items-center justify-center rounded-md bg-(--briefing-accent) font-bold text-white">
          {article.index}
        </span>
        <h2 className="text-basic flex flex-col font-bold">
          <span className="text-xs font-semibold text-(--briefing-accent)">
            {article.eyebrow}
          </span>
          {article.title}
        </h2>
      </div>
      <Separator className="bg-line-bg/50" />
      <p className="text-sm leading-relaxed text-neutral-600">{article.body}</p>

      {article.showImagePlaceholder && (
        // 실제 이미지 연동 전까지 임시 그레이 박스로 대체
        <div
          className="aspect-1200/400 w-full rounded-lg bg-neutral-200"
          aria-hidden
        />
      )}

      {article.statCards && <BriefingStatCards cards={article.statCards} />}
      {article.correlationChart && (
        <BriefingCorrelationChart chart={article.correlationChart} />
      )}

      <BriefingTakeaway
        index={article.index}
        items={article.takeaways}
        color={accentColor}
      />
    </article>
  )
}
