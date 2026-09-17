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
  showImagePlaceholder?: boolean
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
  todayBriefPoints: string[]
  article: BriefingArticle[]
  noviceSummary: {
    quote: string
    todoItems: BriefingTodoItem[]
  }
  glossary: BriefingGlossaryTerm[]
}
