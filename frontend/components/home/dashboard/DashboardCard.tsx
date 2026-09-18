import { cn } from "@/lib/utils"

interface DashboardCardProps {
  icon: React.ReactNode
  title: React.ReactNode
  action?: React.ReactNode
  children: React.ReactNode
  className?: string
}

export default function DashboardCard({
  icon,
  title,
  action,
  children,
  className,
}: DashboardCardProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-4 rounded-lg border border-line-bg bg-white p-5 shadow-sm",
        className
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <h3 className="flex items-center gap-1.5 text-sm font-bold">
          {icon}
          {title}
        </h3>
        {action}
      </div>
      {children}
    </div>
  )
}
