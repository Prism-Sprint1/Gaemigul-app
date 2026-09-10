"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "cn"

import { sidebarNavItems } from "./sidebar-nav-items"
import { Badge } from "../ui"

export default function SidebarNav() {
  const pathname = usePathname()

  return (
    <nav className="p-3">
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
              href === "/" ? pathname === href : pathname.startsWith(href)

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
