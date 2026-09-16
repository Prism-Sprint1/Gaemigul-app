import Link from "next/link"
import { BookOpen, ChevronRight } from "lucide-react"

import { Badge, Button, Card, CardContent } from "@/components/ui"
import { todayAntTerm } from "@/lib/constant/home"

export default function TodayAntTermCard() {
  return (
    <Card className="rounded-xl border-line-bg py-4 shadow-sm">
      <CardContent className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-point3/60 text-point2">
            <BookOpen size={18} />
          </div>
          <div className="flex min-w-0 flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="bg-point text-[11px] text-white">
                오늘의 한 입
              </Badge>
              <span className="text-sm font-bold">
                오늘의 개미 용어 한 입: {todayAntTerm.term}
              </span>
            </div>
            <p className="truncate text-xs text-neutral-500">
              &ldquo;{todayAntTerm.example}&rdquo;
            </p>
          </div>
        </div>

        <Button
          render={<Link href="/briefing" />}
          nativeButton={false}
          variant="secondary"
          className="shrink-0 bg-point3/60 text-point2 hover:bg-point3"
        >
          쉬운 예시 더보기
          <ChevronRight size={14} />
        </Button>
      </CardContent>
    </Card>
  )
}
