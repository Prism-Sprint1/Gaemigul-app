import { Lightbulb } from "lucide-react"
import { Separator } from "../../ui"
import { TimelineTimer } from "../timeline"

import SidebarNav from "./SidebarNav"

export default function Sidebar() {
  return (
    <aside className="max-w-67.5">
      <SidebarNav />
      <Separator className="w-full" />
      <TimelineTimer />
      <div className="bg-point3/60 p-3 px-5">
        <p className="flex items-center gap-1 text-[14px] font-semibold text-point2">
          <Lightbulb size="16" />
          TIP 불개미 꿀팁!
        </p>
        <p className="mt-0.5 text-[12px] text-neutral-500">
          매크로 지표 발표 직후 5분은 뇌동매매를 멈추고 페로몬 신호의 방향성을
          확인하세요.
        </p>
      </div>
    </aside>
  )
}
