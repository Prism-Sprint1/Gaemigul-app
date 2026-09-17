"use client"

import { Header, Footer, Sidebar } from "@/components/common"
import ReportSidebar from "@/components/home/reportSidebar/ReportSidebar"
import { usePathname } from "next/navigation"

export default function MainLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const pathname = usePathname()
  const activeTargets = ["/briefing", "/timeline"]
  const isMatch = activeTargets.some((target) => pathname.includes(target))

  return (
    <>
      <Header />
      <div className="flex w-full">
        <Sidebar />
        <main className={`${isMatch ? "w-[calc(100%-540px)]" : "w-full"}`}>
          {children}
        </main>
        <ReportSidebar />
      </div>
      <Footer />
    </>
  )
}
