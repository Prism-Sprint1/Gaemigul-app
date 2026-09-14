import { Header, Sidebar } from "@/components/common"
import ReportSidebar from "@/components/home/reportSidebar/ReportSidebar"

export default function MainLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <>
      <Header />
      <div className="flex">
        {/* 앱(모바일) 사이즈에서는 고정 사이드바를 노출하지 않음 */}
        <div className="hidden lg:block">
          <Sidebar />
        </div>
        <main className="w-full px-4 py-4 lg:px-12.5 lg:py-10">{children}</main>

        <ReportSidebar />
      </div>
    </>
  )
}
