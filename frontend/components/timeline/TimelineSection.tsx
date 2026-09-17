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
  /** 백엔드에 해당 슬롯이 아직 없으면 null — 이때는 잠금 화면을 보여준다. */
  content: TimelineContent | null
  glossary: Record<string, string>
}

export default function TimelineSection({
  item,
  content,
  glossary,
}: TimelineSectionProps) {
  const isOpen = content !== null
  const isPending = item.status === "next" || item.status === "upcoming"

  return (
    <section
      id={item.id}
      className="flex w-full scroll-mt-[calc(var(--header-height,75px)+64px)] flex-col gap-5"
    >
      <TimelineSectionHeader title={item.title} time={item.time} />

      {isOpen && content ? (
        <div className="flex w-full flex-col gap-10 rounded-none border-b border-line-bg bg-neutral-50 px-3 py-5">
          {content.marketStats && (
            <MarketStatGrid groups={content.marketStats} />
          )}
          <LLMSummarySection summary={content.llmSummary} glossary={glossary} />
          <BeginnerSummarySection
            summary={content.beginnerSummary}
            glossary={glossary}
          />
          <NewsList news={content.news} />
          {content.sectors && <SectorGrid sectors={content.sectors} />}
          {content.featuredStocks && (
            <FeaturedStockGrid stocks={content.featuredStocks} />
          )}
        </div>
      ) : (
        <TimelineLockedSection time={item.time} pending={isPending} />
      )}
    </section>
  )
}
