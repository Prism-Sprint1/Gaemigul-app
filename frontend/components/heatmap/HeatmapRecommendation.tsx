import { Lightbulb } from "lucide-react"
import { Badge } from "@/components/ui"

interface AssociationTag {
  text: string
  highlight: string
}

interface AssociationChain {
  emoji: string
  label: string
  quote: string
  tags: AssociationTag[]
}

const ASSOCIATION_CHAINS: AssociationChain[] = [
  {
    emoji: "🏠",
    label: "[살 곳] 철강·후판",
    quote: "배 뼈대 필수 공급",
    tags: [
      { text: "철광석 해상운송 ", highlight: "포스코홀딩스" },
      { text: "특수 용접 피팅 ", highlight: "태광" },
    ],
  },
  {
    emoji: "🍲",
    label: "[먹을거리] 친환경 엔진",
    quote: "LNG 이중연료 심장",
    tags: [
      { text: "단조 피스톤 부품 ", highlight: "HD현대마린엔진" },
      { text: "고압 변압기 ", highlight: "HD현대일렉트릭" },
    ],
  },
  {
    emoji: "👕",
    label: "[입을거리] 극저온 보냉재",
    quote: "영하 163도 특수 패딩",
    tags: [
      { text: "초저온 글라스 ", highlight: "동성화인텍" },
      { text: "누출방지 밸브 ", highlight: "한국카본" },
    ],
  },
]

export default function HeatmapRecommendation({
  topSectorName,
}: {
  topSectorName: string | undefined
}) {
  return (
    <aside
      aria-labelledby="heatmap-recommendation-title"
      className="h-[calc(100%-28px)] flex-2 rounded-xl border border-neutral-200 bg-white p-4 shadow-xs"
    >
      <h2
        id="heatmap-recommendation-title"
        className="text-sm leading-5 font-bold"
      >
        지금 몰리고 있는 섹터 의식주!
      </h2>
      <p className="mt-1.5 text-[10px] leading-5 text-neutral-400">
        애기 개미들을 위한 꼬리에 꼬리를 무는 연쇄 연상법
      </p>

      <div className="my-4 h-px bg-neutral-100" />

      <div className="rounded-full bg-point px-4 py-2.5 text-center text-sm font-bold text-white shadow-sm">
        {topSectorName ?? "집계 중"}
      </div>
      <div className="mx-auto h-3 w-px border-l-2 border-dashed border-point/40" />

      <div className="flex flex-col gap-2.5">
        {ASSOCIATION_CHAINS.map((chain) => (
          <div
            key={chain.label}
            className="rounded-lg border border-neutral-100 bg-neutral-50/80 p-3"
          >
            <p className="text-xs font-bold text-neutral-800">
              {chain.emoji} {chain.label}
            </p>
            <p className="mt-1 text-[10px] text-neutral-500">
              &ldquo;{chain.quote}&rdquo;
            </p>
            <div className="mt-2.5 flex items-start gap-2">
              <span className="mt-1 shrink-0 text-[10px] text-neutral-400">
                → 연쇄 낙수
              </span>
              <div className="flex min-w-0 flex-1 flex-col items-end gap-1">
                {chain.tags.map((tag) => (
                  <Badge
                    key={tag.highlight}
                    variant="outline"
                    className="max-w-full justify-end truncate rounded-full border-neutral-200 bg-white px-2.5 py-1 text-[10px] font-normal text-neutral-600"
                  >
                    {tag.text}
                    <span className="font-semibold text-point">
                      {tag.highlight}
                    </span>
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-3 rounded-lg border border-amber-100 bg-amber-50/60 p-3">
        <p className="flex items-center gap-1 text-[11px] font-semibold text-amber-700">
          <Lightbulb className="size-3.5" /> 개미 연상 TIP
        </p>
        <p className="mt-1 text-[12px] leading-5 text-neutral-500">
          배를 만들면 <span className="font-medium">철판(집)</span>을 깔고{" "}
          <span className="font-medium">엔진(밥)</span>을 먹인 뒤{" "}
          <span className="font-medium">보랭재(옷)</span>를 입힌다!
        </p>
      </div>
    </aside>
  )
}
