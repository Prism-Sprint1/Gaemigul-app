import { Separator } from "@/components/ui/separator"

export default function timeline() {
  return (
    <div className="text-l flex flex-col gap-8 p-8">
      <div className="flex flex-col gap-2">
        <div className="text-2xl leading-none font-bold">
          개미들을 위한 실시간 시장 신호
        </div>
        <div className="text-muted-foreground">
          <p className="text-xs whitespace-nowrap">
            시장의 급박한 변화와 핵심 뉴스 요약을 페로몬 흔적처럼 빠르게
            따라갑니다.
          </p>
        </div>
      </div>
      <Separator />
    </div>
  )
}
