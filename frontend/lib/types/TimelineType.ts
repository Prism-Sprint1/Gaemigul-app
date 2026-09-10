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
