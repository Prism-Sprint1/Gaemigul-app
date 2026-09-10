import { Separator } from "@/components/ui/separator"

interface PageTitleType {
  title: string
  description: string
}

export default function PageTitle({ title, description }: PageTitleType) {
  return (
    <div className="text-l flex flex-col gap-8">
      <div className="flex flex-col gap-2">
        <div className="text-2xl leading-none font-bold">{title}</div>
        <div className="text-muted-foreground">
          <p className="text-xs whitespace-nowrap">{description}</p>
        </div>
      </div>
      <Separator />
    </div>
  )
}
