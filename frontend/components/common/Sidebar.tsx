import { Separator } from "../ui"

import SidebarNav from "./SidebarNav"

export default function Sidebar() {
  return (
    <aside className="min-w-67.5">
      <SidebarNav />
      <Separator className="w-full" />
    </aside>
  )
}
