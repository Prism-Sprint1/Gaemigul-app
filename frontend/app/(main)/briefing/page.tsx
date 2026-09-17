import {
  BriefingArticle,
  BriefingArticleHeader,
  BriefingLede,
  BriefingNoviceSummary,
  ReportSectionsNav,
} from "@/components/briefing"
import { PageTitle } from "@/components/common"
import { briefingContent } from "@/lib/constant/briefingContent"

export default function BriefingPage() {
  const reportSectionItems = briefingContent.article.map((article) => ({
    id: article.id,
    label: `${article.index} ${article.eyebrow}`,
  }))

  return (
    <div className="flex">
      <div className="flex w-full flex-col gap-6 px-6 py-4">
        <PageTitle
          title="개미들을 위한 실시간 시장 신호"
          description="시장의 급박한 변화와 핵심 뉴스 요약을 페로몬 흔적처럼 빠르게 따라갑니다."
        />

        <div className="flex items-start gap-6">
          <section className="flex min-w-0 flex-1 flex-col gap-6 rounded-xl bg-ant-bg p-5">
            <BriefingArticleHeader content={briefingContent} />

            {/* 실제 이미지 연동 전까지 임시 그레이 박스로 대체 */}
            <div
              className="aspect-1200/400 w-full rounded-lg bg-neutral-200"
              aria-hidden
            />

            <BriefingLede
              lead={briefingContent.lead}
              points={briefingContent.todayBriefPoints}
            />

            <div className="flex gap-5">
              <div className="flex flex-col gap-5">
                {briefingContent.article.map((article, id) => (
                  <BriefingArticle key={article.id} id={id} article={article} />
                ))}

                <BriefingNoviceSummary
                  summary={briefingContent.noviceSummary}
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
      </div>
      {/* <RepoㄴrtSidebar /> */}
    </div>
  )
}
