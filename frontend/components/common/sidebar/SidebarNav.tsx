"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "cn"

import { sidebarNavItems } from "@/lib/constant/sidebar"

import { Badge } from "../../ui"

// 브리핑 페이지는 실시간 페로몬(타임라인)의 하위 화면이라 같은 항목을 active 처리한다.
const TIMELINE_PATH = "/timeline"
const BRIEFING_PATH = "/briefing"

export default function SidebarNav() {
  const pathname = usePathname()

  return (
    <nav className="bg-white px-2.5 py-3">
      <ul className="flex flex-col gap-2.5">
        {sidebarNavItems.map(
          ({
            href,
            label,
            icon: Icon,
            badge,
            badgeClassName,
            activeBadgeClassName,
          }) => {
            const isActive =
              pathname === href ||
              pathname.startsWith(`${href}/`) ||
              (href === TIMELINE_PATH && pathname.startsWith(BRIEFING_PATH))

            return (
              <li key={href} className="flex items-center justify-between">
                <Link
                  href={href}
                  aria-current={isActive ? "page" : undefined}
                  className={cn(
                    "group flex w-full items-center justify-between rounded-lg px-3 py-2 transition-colors duration-200",
                    isActive ? "bg-point" : "hover:bg-point/10"
                  )}
                >
                  <span
                    className={cn(
                      "flex items-center gap-2 text-[14px] transition-colors duration-200",
                      isActive ? "text-white" : "group-hover:text-point"
                    )}
                  >
                    <Icon size="16" />
                    {label}
                  </span>
                  <Badge
                    className={cn(
                      isActive ? activeBadgeClassName : badgeClassName,
                      "transition-colors duration-200"
                    )}
                  >
                    {badge}
                  </Badge>
                </Link>
              </li>
            )
          }
        )}
      </ul>
    </nav>
  )
}
