import { PageTitle } from "@/components/common"
import PheromoneTemperatureCard from "@/components/home/PheromoneTemperatureCard"
import TodayAntTermCard from "@/components/home/TodayAntTermCard"
import WhisperBriefingSection from "@/components/home/WhisperBriefingSection"

export default function Page() {
  return (
    <div className="flex w-full flex-col gap-6 px-6 py-10">
      <PageTitle
        title="애기 개미님, 오늘도 좋은 하루 되세요!"
        description="실시간 페로몬 온도부터 불개미 대장의 귓속말까지, 개미굴의 핵심 콘텐츠를 한눈에 확인하세요."
      />

      <PheromoneTemperatureCard />
      <WhisperBriefingSection />
      <TodayAntTermCard />
    </div>
  )
}
