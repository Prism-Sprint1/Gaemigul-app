import { PageTitle } from "@/components/common"
import PheromoneTemperatureCard from "@/components/home/PheromoneTemperatureCard"
import TodayAntTermCard from "@/components/home/TodayAntTermCard"
import WhisperBriefingSection from "@/components/home/WhisperBriefingSection"
import AntColonySentimentCard from "@/components/home/dashboard/AntColonySentimentCard"
import CalendarScheduleCard from "@/components/home/dashboard/CalendarScheduleCard"
import MarketSessionCard from "@/components/home/dashboard/MarketSessionCard"
import TradingActivityCard from "@/components/home/dashboard/TradingActivityCard"
import UsdKrwTrendCard from "@/components/home/dashboard/UsdKrwTrendCard"

export default function Page() {
  return (
    <div className="flex w-full flex-col gap-6 px-6 py-10">
      <PageTitle
        title="애기 개미님, 오늘도 좋은 하루 되세요!"
        description="실시간 페로몬 온도부터 불개미 대장의 귓속말까지, 개미굴의 핵심 콘텐츠를 한눈에 확인하세요."
      />

      <div className="grid grid-cols-1 items-start gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <div className="flex flex-col gap-6">
          <div className="rounded-2xl border border-line-bg bg-white p-5 shadow-sm">
            <PheromoneTemperatureCard />
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <MarketSessionCard />
            <AntColonySentimentCard />
          </div>

          <UsdKrwTrendCard />
          <TradingActivityCard />
          <CalendarScheduleCard />
        </div>

        <div className="xl:sticky xl:top-18.75">
          <div className="overflow-hidden rounded-2xl border border-line-bg bg-white shadow-sm">
            <WhisperBriefingSection />
            <TodayAntTermCard />
          </div>
        </div>
      </div>
    </div>
  )
}
