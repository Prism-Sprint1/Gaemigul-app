import PheromoneTemperatureCard from "@/components/home/PheromoneTemperatureCard"
import TodayAntTermCard from "@/components/home/TodayAntTermCard"
import WhisperBriefingSection from "@/components/home/WhisperBriefingSection"
import CalendarScheduleCard from "@/components/home/dashboard/CalendarScheduleCard"
import PheromoneSignalCard from "@/components/home/dashboard/PheromoneSignalCard"
import TradingActivityCard from "@/components/home/dashboard/TradingActivityCard"
import UsdKrwTrendCard from "@/components/home/dashboard/UsdKrwTrendCard"

export default function Page() {
  return (
    <div className="flex w-full flex-col gap-5 md:px-6 md:py-10">
      <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="flex flex-col gap-6">
          <PheromoneTemperatureCard />

          <div className="flex flex-col gap-6 md:flex-row md:items-stretch">
            <div className="flex md:flex-3">
              <UsdKrwTrendCard />
            </div>
            <div className="md:flex-1.5 flex">
              <PheromoneSignalCard />
            </div>
          </div>

          <TradingActivityCard />
          <CalendarScheduleCard />
        </div>

        <div className="xl:sticky xl:top-18.75">
          {/* 모바일에서는 대장 챗이 fixed로 떠 있어야 해서 overflow-hidden을 걸면 안 된다(특히
              iOS Safari는 overflow-hidden 조상 안의 fixed 요소를 뷰포트에 고정하지 못하는 버그가 있다). */}
          <div className="rounded-2xl border border-line-bg bg-white shadow-sm xl:overflow-hidden">
            <WhisperBriefingSection />
            <TodayAntTermCard />
          </div>
        </div>
      </div>
    </div>
  )
}
