import { Lock } from "lucide-react"

type TimelineLockedSectionProps = {
  time: string
}

export default function TimelineLockedSection({
  time,
}: TimelineLockedSectionProps) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-dashed border-neutral-200 bg-neutral-50 px-5 py-8 text-neutral-400">
      <Lock size={16} />
      <p className="text-sm">{time} 이후에 공개되는 콘텐츠예요.</p>
    </div>
  )
}
