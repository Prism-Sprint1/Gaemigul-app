interface SubTitleType {
  title: string
  time: string
}

export default function SubTitle({ title, time }: SubTitleType) {
  return (
    <div className="text-l flex gap-8">
      <div className="flex items-end gap-2">
        <div className="relative inline-block text-2xl leading-none font-bold after:absolute after:bottom-0 after:left-0 after:-z-10 after:h-[45%] after:w-full after:bg-pink-100 after:content-['']">
          {title}
        </div>
        <div className="text-muted-foreground">
          <p className="text-xs whitespace-nowrap">{time}</p>
        </div>
      </div>
    </div>
  )
}
