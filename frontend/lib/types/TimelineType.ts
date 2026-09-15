export type TimelineStatus = "past" | "current" | "next" | "upcoming"

export type TimelineItem = {
  id: string
  time: string
  title: string
  description: string
}

export type ScheduleItem = TimelineItem & {
  status: TimelineStatus
  badgeLabel: string
}

export type MarketStat = {
  label: string
  value: string
  rate: string
  isPositive: boolean
  /** 비교 기준(예: 07:30) 값 — 있으면 카드 안에 작고 연하게 함께 표시한다. */
  previousValue?: string
  previousLabel?: string
}

export type MarketStatGroup = {
  groupLabel: string
  stats: MarketStat[]
}

export type SummaryAccent = "red" | "orange" | "green"

export type LLMSummaryPoint = {
  id: string
  badgeLabel: string
  title: string
  description: string
  accent: SummaryAccent
}

export type LLMSummary = {
  title: string
  subtitle: string
  points: LLMSummaryPoint[]
}

export type BeginnerSummaryPoint = {
  id: string
  title: string
  description: string
  /** 카드 하단에 보여줄 태그. 카드마다 2개씩 넣는다. */
  tags: string[]
}

export type BeginnerSummary = {
  title: string
  subtitle: string
  points: BeginnerSummaryPoint[]
}

export type NewsItem = {
  id: string
  content: string
  source: string
  /** 원문 뉴스 링크. 아직 실제 URL이 연결되지 않은 목데이터는 "#"으로 둔다. */
  url: string
}

export type SectorStock = {
  name: string
  badge: string
  rate: string
}

export type SectorItem = {
  id: string
  name: string
  rate: string
  /** 섹터 대표 종목 1개만 보여준다. */
  topStock: SectorStock
}

/** 급등/급락 여부와 무관하게 시장에서 주목받는 특징 종목. */
export type FeaturedStock = {
  id: string
  name: string
  rate: string
  price: string
  badge: string
}

export type TimelineContent = {
  id: string
  marketStats?: MarketStatGroup[]
  llmSummary: LLMSummary
  beginnerSummary: BeginnerSummary
  news: NewsItem[]
  sectors?: SectorItem[]
  featuredStocks?: FeaturedStock[]
}
