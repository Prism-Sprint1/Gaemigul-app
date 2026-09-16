import { Clock, Lock } from "lucide-react"

type TimelineLockedSectionProps = {
  time: string
  /** true면 아직 시각이 오지 않은 예정 슬롯, false면 시각은 지났지만 데이터가 없는 경우다. */
  pending: boolean
}

export default function TimelineLockedSection({
  time,
  pending,
}: TimelineLockedSectionProps) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-dashed border-neutral-200 bg-neutral-50 px-5 py-8 text-neutral-400">
      {pending ? <Lock size={16} /> : <Clock size={16} />}
      <p className="text-sm">
        {pending
          ? `${time} 이후에 공개되는 콘텐츠예요.`
          : "이 시간대 데이터를 아직 불러오지 못했어요."}
      </p>
    </div>
  )
}
