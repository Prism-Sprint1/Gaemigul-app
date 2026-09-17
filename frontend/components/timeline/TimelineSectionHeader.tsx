type TimelineSectionHeaderProps = {
  title: string
  time: string
}

export default function TimelineSectionHeader({
  title,
  time,
}: TimelineSectionHeaderProps) {
  return (
    <div className="flex items-baseline gap-2">
      <h2 className="relative inline-flex items-center text-[30px] font-bold after:absolute after:bottom-1.5 after:h-1.5 after:w-full after:bg-point/15 after:content-['']">
        {title}
      </h2>
      <span className="text-sm text-neutral-400">{time}</span>
    </div>
  )
}
