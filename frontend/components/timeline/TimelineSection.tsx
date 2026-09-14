import type { ScheduleItem, TimelineContent } from "@/lib/types/TimelineType"
import BeginnerSummarySection from "./BeginnerSummarySection"
import LLMSummarySection from "./LLMSummarySection"
import MarketStatGrid from "./MarketStatGrid"
import NewsList from "./NewsList"
import SectorGrid from "./SectorGrid"
import SurgingStockGrid from "./SurgingStockGrid"
import TimelineLockedSection from "./TimelineLockedSection"
import TimelineSectionHeader from "./TimelineSectionHeader"

// TODO: 백엔드 연동 후 제거 — 개발 편의를 위해 모든 시간대 섹션을 임시로 오픈해 둔다.
const DEV_FORCE_OPEN_ALL = true

type TimelineSectionProps = {
  item: ScheduleItem
  content: TimelineContent
}

export default function TimelineSection({ item, content }: TimelineSectionProps) {
  const isOpen =
    DEV_FORCE_OPEN_ALL ||
    item.status === "past" ||
    item.status === "current"

  return (
    <section id={item.id} className="flex scroll-mt-6 flex-col gap-5">
      <TimelineSectionHeader title={item.title} time={item.time} />

      {isOpen ? (
        <div className="flex flex-col gap-10 rounded-none border-b border-[#E5E7EB] bg-neutral-50 p-5">
          {content.marketStats && (
            <MarketStatGrid groups={content.marketStats} />
          )}
          <LLMSummarySection summary={content.llmSummary} />
          <BeginnerSummarySection summary={content.beginnerSummary} />
          <NewsList news={content.news} />
          {content.sectors && <SectorGrid sectors={content.sectors} />}
          {content.surgingStocks && (
            <SurgingStockGrid stocks={content.surgingStocks} />
          )}
        </div>
      ) : (
        <TimelineLockedSection time={item.time} />
      )}
    </section>
  )
}
