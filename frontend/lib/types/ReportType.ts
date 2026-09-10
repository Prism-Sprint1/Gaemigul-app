export type ReportBadgeLabel = "1 WEEK" | "DAY"

export type ReportItem = {
  id: string
  month: string
  date: string
  day: string
  title: string
  description: string
  badgeLabel: ReportBadgeLabel
  isHighlighted: boolean
}

export type ReportWeekGroup = {
  id: string
  rangeLabel: string
  items: ReportItem[]
}

export type ReportMonth = {
  id: string
  label: string
  subLabel: string
}
