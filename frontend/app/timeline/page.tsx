import { timelineItems, PageTitle, Subtitle } from "@/components/common"

export default function timeline() {
  return (
    <div className="flex flex-col gap-6 p-6">
      <PageTitle>
        <PageTitle.title>개미들을 위한 실시간 시장 신호</PageTitle.title>
        <PageTitle.Description>
          시장의 급박한 변화의 핵심 뉴스 요약을 페로몬 흔적처럼 빠르게
          따라갑니다.
        </PageTitle.Description>
      </PageTitle>
      <Subtitle>
        <Subtitle.Subtitle>글로벌 시황 요약</Subtitle.Subtitle>
        <SubTitle.Time>07:30</SubTitle.Time>
      </Subtitle>
      {timelineItems.map((item) => (
        <section
          key={item.id}
          id={item.id}
          className="scroll-mt-6 rounded-lg border p-4"
        >
          <p className="text-sm text-neutral-500">{item.time}</p>
          <h2 className="text-lg font-semibold">{item.title}</h2>
          <p className="text-sm text-neutral-500">{item.description}</p>
        </section>
      ))}
    </div>
  )
}
