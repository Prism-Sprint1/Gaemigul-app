import Link from "next/link"

import { sidebarNavItems } from "./sidebar-nav-items"

export default function SidebarNav() {
  return (
    <nav className="p-3">
      <ul className="flex flex-col gap-2.5">
        {sidebarNavItems.map(({ href, label, icon: Icon }) => (
          <li key={href} className="flex items-center justify-between">
            <Link href={href} className="w-full rounded-2xl px-3 py-2">
              <span className="flex items-center gap-2 text-[14px]">
                <Icon size="16" />
                {label}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  )
}
