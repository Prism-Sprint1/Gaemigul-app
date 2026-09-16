export type BriefingStatTone = "increase" | "decrease" | "positive" | "neutral"

export type BriefingStatCard = {
  label: string
  value: string
  changeLabel?: string
  tone: BriefingStatTone
}

export type BriefingCorrelationPoint = {
  label: string
  fxRate: number
  netSell: number
  highlighted?: boolean
}

export type BriefingCorrelationChart = {
  title: string
  data: BriefingCorrelationPoint[]
  footnoteLeft: string
  footnoteRight: string
}

export type BriefingArticle = {
  id: string
  index: string
  eyebrow: string
  title: string
  body: string
  statCards?: BriefingStatCard[]
  correlationChart?: BriefingCorrelationChart
  /**
   * 이 섹션에 이미지 영역이 있는지를 나타낸다.
   * undefined면 이미지 영역 자체가 없고, null이면 이미지 영역은 있으나 아직 준비되지 않아 기본 이미지를 보여준다.
   */
  imageUrl?: string | null
  takeaways: string[]
}

export type BriefingTodoItem = {
  title: string
  description: string
}

export type BriefingGlossaryTerm = {
  term: string
  description: string
}

export type BriefingContent = {
  tag: string
  category: string
  title: string
  publishedAt: string
  analyst: string
  lead: string
  /** 없으면(undefined) 기본 이미지, 있으면 실제 URL을 보여준다. */
  mainImageUrl?: string | null
  todayBriefPoints: string[]
  article: BriefingArticle[]
  noviceSummary: {
    quote: string
    todoItems: BriefingTodoItem[]
  }
  glossary: BriefingGlossaryTerm[]
}
