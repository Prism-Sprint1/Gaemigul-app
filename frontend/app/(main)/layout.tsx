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
        <Sidebar />
        <main className="w-[calc(100%-540px)] px-6 py-4">{children}</main>
        <ReportSidebar />
      </div>
    </>
  )
}
