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
      <div className="flex" data-main-shell>
        <Sidebar />
        <main className="w-full px-12.5 py-10">{children}</main>

        <ReportSidebar />
      </div>
    </>
  )
}
