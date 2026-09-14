"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

import { Separator } from "@/components/ui/separator"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"

const TIMELINE_PATH = "/timeline"
const BRIEFING_PATH = "/briefing"

interface PageTitleType {
  title: string
  description: string
}

export default function PageTitle({ title, description }: PageTitleType) {
  const pathname = usePathname()
  const showMarketTabs =
    pathname.startsWith(TIMELINE_PATH) || pathname.startsWith(BRIEFING_PATH)
  const activeTab = pathname.startsWith(BRIEFING_PATH) ? "briefing" : "timeline"

  return (
    <div className="text-l flex flex-col gap-8">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-2">
          <div className="text-2xl leading-none font-bold">{title}</div>
          <div className="text-muted-foreground">
            <p className="text-xs whitespace-nowrap">{description}</p>
          </div>
        </div>

        {showMarketTabs && (
          <Tabs value={activeTab} className="shrink-0">
            <TabsList className="h-auto rounded-full bg-neutral-100 p-1">
              <TabsTrigger
                value="timeline"
                render={<Link href={TIMELINE_PATH} />}
                className="rounded-full px-4 py-1.5 text-neutral-500 data-active:bg-point data-active:text-white data-active:shadow-none"
              >
                시황
              </TabsTrigger>
              <TabsTrigger
                value="briefing"
                render={<Link href={BRIEFING_PATH} />}
                className="rounded-full px-4 py-1.5 text-neutral-500 data-active:bg-point data-active:text-white data-active:shadow-none"
              >
                브리핑
              </TabsTrigger>
            </TabsList>
          </Tabs>
        )}
      </div>
      <Separator />
    </div>
  )
}
