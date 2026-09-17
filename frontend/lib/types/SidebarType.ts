import type { LucideIcon } from "lucide-react"

export type SidebarNavItem = {
  href: string
  label: string
  icon: LucideIcon
  badge: string
  badgeClassName: string
  activeBadgeClassName: string
}
