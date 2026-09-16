"use client"

import { Suspense, useEffect, useMemo, useState } from "react"
import { useSearchParams } from "next/navigation"

import {
  BriefingArticle,
  BriefingArticleHeader,
  BriefingImage,
  BriefingLede,
  BriefingNoviceSummary,
  BriefingSkeleton,
  ReportSectionsNav,
} from "@/components/briefing"
import { PageTitle } from "@/components/common"
import { getReport, getReportList, type ReportKind } from "@/lib/api/report"
import {
  isReportReady,
  mapReportToBriefingContent,
} from "@/lib/briefing-mapper"
import type { BriefingContent } from "@/lib/types/BriefingType"

type ReportTarget = { type: ReportKind; date: string }

function getCurrentYearMonth() {
  const now = new Date()
  return { year: now.getFullYear(), month: now.getMonth() + 1 }
}

/** 쿼리로 지정된 보고서가 없을 때, 이번 달 목록에서 가장 최근 보고서를 기본값으로 고른다. */
async function resolveDefaultTarget(): Promise<ReportTarget | null> {
  const { year, month } = getCurrentYearMonth()
  const list = await getReportList(year, month)
  const latestWeek = list.weeks[0]
  if (!latestWeek) return null

  if (latestWeek.weekly) {
    return { type: "weekly", date: latestWeek.weekly.end_date }
  }

  const latestDaily = latestWeek.dailies.at(-1)
  return latestDaily ? { type: "daily", date: latestDaily.end_date } : null
}

function BriefingPageContent() {
  const searchParams = useSearchParams()
  const queryType = searchParams.get("type")
  const queryDate = searchParams.get("date")

  const [content, setContent] = useState<BriefingContent | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isEmpty, setIsEmpty] = useState(false)

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setIsLoading(true)
      setIsEmpty(false)

      const target: ReportTarget | null =
        queryType === "daily" || queryType === "weekly"
          ? { type: queryType, date: queryDate ?? "" }
          : await resolveDefaultTarget()

      if (!target || !target.date) {
        if (!cancelled) {
          setContent(null)
          setIsEmpty(true)
        }
        return
      }

      const report = await getReport(target.type, target.date)
      if (cancelled) return

      if (!isReportReady(report)) {
        setContent(null)
        setIsEmpty(true)
        return
      }

      setContent(mapReportToBriefingContent(report))
      setIsEmpty(false)
    }

    load()
      .catch(() => {
        if (cancelled) return
        setContent(null)
        setIsEmpty(true)
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [queryType, queryDate])

  const reportSectionItems = useMemo(
    () =>
      content?.article.map((article) => ({
        id: article.id,
        label: `${article.index} ${article.eyebrow}`,
      })) ?? [],
    [content]
  )

  return (
    <div className="flex">
      <div className="flex w-full flex-col gap-6 px-6 py-4">
        <PageTitle
          title="개미들을 위한 실시간 시장 신호"
          description="시장의 급박한 변화와 핵심 뉴스 요약을 페로몬 흔적처럼 빠르게 따라갑니다."
        />

        {isLoading && <BriefingSkeleton />}

        {!isLoading && isEmpty && (
          <div className="flex min-h-100 w-full items-center justify-center rounded-xl bg-ant-bg p-5">
            <p className="text-sm text-neutral-400">
              아직 리포트가 생성되지 않았습니다.
            </p>
          </div>
        )}

        {!isLoading && !isEmpty && content && (
          <div className="flex items-start gap-6">
            <section className="flex min-w-0 flex-1 flex-col gap-6 rounded-xl bg-ant-bg p-5">
              <BriefingArticleHeader content={content} />

              <BriefingImage url={content.mainImageUrl} alt={content.title} />

              <BriefingLede
                lead={content.lead}
                points={content.todayBriefPoints}
              />

              <div className="flex gap-5">
                <div className="flex flex-col gap-5">
                  {content.article.map((article, id) => (
                    <BriefingArticle
                      key={article.id}
                      id={id}
                      article={article}
                    />
                  ))}

                  <BriefingNoviceSummary
                    summary={content.noviceSummary}
                    glossary={content.glossary}
                  />
                </div>
                <ReportSectionsNav
                  items={reportSectionItems}
                  footerItem={{
                    id: "article-04",
                    label: "초보 개미 30초 한 줄 결론",
                  }}
                />
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  )
}

export default function BriefingPage() {
  return (
    <Suspense fallback={<BriefingSkeleton />}>
      <BriefingPageContent />
    </Suspense>
  )
}
