import { Calendar, Lollipop, Timeline, type LucideIcon } from "lucide-react"

export type SidebarNavItem = {
  href: string
  label: string
  icon: LucideIcon
}

export const sidebarNavItems: SidebarNavItem[] = [
  {
    href: "/",
    label: "실시간 페로몬",
    icon: Timeline,
  },
  {
    href: "/calendar",
    label: "비축 캘린더",
    icon: Calendar,
  },
  {
    href: "/hitmap",
    label: "단물 지도",
    icon: Lollipop,
  },
]
