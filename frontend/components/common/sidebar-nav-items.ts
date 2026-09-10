import { Calendar, Lollipop, Timeline, type LucideIcon } from "lucide-react"

const date = new Date()

const month = date.getMonth() + 1

export type SidebarNavItem = {
  href: string
  label: string
  icon: LucideIcon
  badge: string
  badgeClassName: string
  activeBadgeClassName: string
}

export const sidebarNavItems: SidebarNavItem[] = [
  {
    href: "/",
    label: "실시간 페로몬",
    icon: Timeline,
    badge: "LIVE",
    badgeClassName: "bg-white/20 text-point",
    activeBadgeClassName: "bg-white/20 text-white",
  },
  {
    href: "/calendar",
    label: "비축 캘린더",
    icon: Calendar,
    badge: `${month}월`,
    badgeClassName: "bg-white/20 text-black/80",
    activeBadgeClassName: "bg-white/20 text-white",
  },
  {
    href: "/hitmap",
    label: "단물 지도",
    icon: Lollipop,
    badge: "HOT",
    badgeClassName: "bg-point3 text-point2",
    activeBadgeClassName: "bg-point3 text-point2",
  },
]
