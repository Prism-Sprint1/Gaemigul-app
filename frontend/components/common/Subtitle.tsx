import type { ReactNode } from "react"

interface subtitleProps {
  children: ReactNode
}

export default function subtitle({ children }: subtitleProps) {
  return (
    <div className="text-l flex gap-8 p-8">
      <div className="flex gap-2">{children}</div>
    </div>
  )
}

subtitle.subtitle = function subtitle({ children }: subtitleProps) {
  return <div className="text-2xl leading-none font-bold">{children}</div>
}

subtitle.Time = function subtitleTime({ children }: subtitleProps) {
  return (
    <div className="text-muted-foreground">
      <p className="text-xs whitespace-nowrap">{children}</p>
    </div>
  )
}
