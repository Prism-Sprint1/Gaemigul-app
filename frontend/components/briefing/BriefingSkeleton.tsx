import { Skeleton } from "@/components/ui"

/** 브리핑 콘텐츠를 불러오는 동안 보여주는 뼈대 UI. 실제 레이아웃 비율을 그대로 따른다. */
export default function BriefingSkeleton() {
  return (
    <div className="flex items-start gap-6">
      <section className="flex min-w-0 flex-1 flex-col gap-6 rounded-xl bg-ant-bg p-5">
        <div className="flex flex-col gap-5 border-b border-neutral-100 pb-5">
          <div className="flex items-center justify-between">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-5 w-32" />
          </div>
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-4 w-56" />
        </div>

        <Skeleton className="aspect-1200/400 w-full rounded-lg" />

        <div className="flex flex-col gap-3 rounded-lg bg-white p-5">
          <Skeleton className="h-6 w-2/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-1/2" />
        </div>

        <div className="flex flex-col gap-5">
          {[1, 2, 3].map((key) => (
            <div
              key={key}
              className="flex flex-col gap-4 rounded-lg bg-white p-5"
            >
              <div className="flex items-center gap-2">
                <Skeleton className="size-9 rounded-md" />
                <Skeleton className="h-5 w-48" />
              </div>
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-20 w-full rounded-lg" />
            </div>
          ))}
        </div>
      </section>

      <aside className="hidden w-56 shrink-0 lg:block">
        <div className="flex flex-col gap-3 rounded-xl bg-white p-4">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
        </div>
      </aside>
    </div>
  )
}
