import { Separator } from "../ui"

import SidebarNav from "./SidebarNav"
import TimelineTimer from "./TimelineTimer"

export default function Sidebar() {
  return (
    <aside className="min-w-67.5">
      <SidebarNav />
      <Separator className="w-full" />
      <TimelineTimer />
    </aside>
  )
}
