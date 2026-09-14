import { Separator } from "../ui"

type BriefingLedeProps = {
  lead: string
  points: string[]
}

export default function BriefingLede({ lead, points }: BriefingLedeProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="relative flex flex-col gap-2 overflow-hidden rounded-lg bg-white p-5 shadow-sm before:absolute before:top-0 before:left-0 before:h-full before:w-1 before:bg-point before:content-['']">
        <p className="text-xl font-bold text-neutral-950">{lead}</p>
        <Separator className="my-3 bg-[#E5E7EB]/50" />
        <p className="text-basic flex items-center gap-1.5 font-bold text-point">
          <span aria-hidden>📌</span>
          오늘의 핵심 요약 프리뷰
        </p>
        <ul className="flex flex-col gap-1.5">
          {points.map((point) => (
            <li
              key={point}
              className="flex gap-1.5 text-sm leading-relaxed text-neutral-600"
            >
              <span className="text-point">•</span>
              {point}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
