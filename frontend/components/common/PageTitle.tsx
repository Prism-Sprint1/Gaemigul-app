import type { ReactNode } from "react"
import { Separator } from "@/components/ui/separator"

interface PageTitleProps {
  children: ReactNode
}

export default function PageTitle({ children }: PageTitleProps) {
  return (
    <div className="text-l flex flex-col gap-8 p-8">
      <div className="flex flex-col gap-2">{children}</div>
      <Separator />
    </div>
  )
}

PageTitle.title = function PageTitletile({ children }: PageTitleProps) {
  return <div className="text-2xl leading-none font-bold">{children}</div>
}

PageTitle.Description = function PageTitleDescription({
  children,
}: PageTitleProps) {
  return (
    <div className="text-muted-foreground">
      <p className="text-xs whitespace-nowrap">{children}</p>
    </div>
  )
}
