"use client"

import { Lightbulb, X } from "lucide-react"
import { cn } from "@/lib/utils"

import { Separator } from "../../ui"
import { TimelineTimer } from "../timeline"

import SidebarNav from "./SidebarNav"
import { useMobileSidebar } from "./MobileSidebarContext"

export default function Sidebar() {
  const { isOpen, close } = useMobileSidebar()

  return (
    <>
      {/* 모바일: 사이드바 열렸을 때 뒷배경 딤 처리 */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          onClick={close}
          aria-hidden="true"
        />
      )}
      <aside
        className={cn(
          "bg-background max-w-67.5",
          "fixed inset-y-0 right-0 z-50 w-67.5 translate-x-full transition-transform duration-300 ease-in-out",
          "md:static md:z-auto md:w-auto md:translate-x-0 md:transition-none",
          isOpen && "translate-x-0"
        )}
      >
        <div className="flex items-center justify-end px-3 py-2 md:hidden">
          <button
            type="button"
            onClick={close}
            aria-label="메뉴 닫기"
            className="p-1 text-foreground"
          >
            <X size={20} />
          </button>
        </div>
        <SidebarNav />
        <Separator className="w-full" />
        <TimelineTimer />
        <div className="hidden bg-point3/60 p-3 px-5 md:block">
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
    </>
  )
}
