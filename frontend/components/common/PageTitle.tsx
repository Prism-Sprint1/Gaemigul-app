import { Separator } from "@/components/ui/separator"

interface PageTitleType {
  title: string
  description: string
}

export default function PageTitle({ title, description }: PageTitleType) {
  return (
    <div className="text-l flex flex-col gap-3">
      <div className="flex flex-col gap-2">
        <div className="truncate text-lg leading-none font-bold sm:text-xl lg:text-2xl">
          {title}
        </div>
        <div className="text-muted-foreground">
          <p className="truncate text-[10px] sm:text-xs">{description}</p>
        </div>
      </div>
      <Separator />
    </div>
  )
}
