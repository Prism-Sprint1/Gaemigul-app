import type { ScheduleItem, TimelineContent } from "@/lib/types/TimelineType"
import BeginnerSummarySection from "./BeginnerSummarySection"
import FeaturedStockGrid from "./FeaturedStockGrid"
import LLMSummarySection from "./LLMSummarySection"
import MarketStatGrid from "./MarketStatGrid"
import NewsList from "./NewsList"
import SectorGrid from "./SectorGrid"
import TimelineLockedSection from "./TimelineLockedSection"
import TimelineSectionHeader from "./TimelineSectionHeader"

type TimelineSectionProps = {
  item: ScheduleItem
  content: TimelineContent
  /**
   * 오늘이 아닌 지난 날짜를 보고 있을 때 true로 전달한다.
   * 지난 날짜는 하루치 데이터가 이미 전부 확정된 상태이므로 시간대 잠금 없이 모두 공개한다.
   */
  forceOpen?: boolean
}

export default function TimelineSection({
  item,
  content,
  forceOpen = false,
}: TimelineSectionProps) {
  const isOpen =
    forceOpen || item.status === "past" || item.status === "current"

  return (
    <section id={item.id} className="flex scroll-mt-6 flex-col gap-5">
      <TimelineSectionHeader title={item.title} time={item.time} />

      {isOpen ? (
        <div className="flex flex-col gap-10 rounded-none border-b border-line-bg bg-neutral-50 p-5">
          {content.marketStats && (
            <MarketStatGrid groups={content.marketStats} />
          )}
          <LLMSummarySection summary={content.llmSummary} />
          <BeginnerSummarySection summary={content.beginnerSummary} />
          <NewsList news={content.news} />
          {content.sectors && <SectorGrid sectors={content.sectors} />}
          {content.featuredStocks && (
            <FeaturedStockGrid stocks={content.featuredStocks} />
          )}
        </div>
      ) : (
        <TimelineLockedSection time={item.time} />
      )}
    </section>
  )
}
