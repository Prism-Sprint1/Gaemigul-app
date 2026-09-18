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
      <div className="flex w-full">
        <main
          className={`${isMatch ? "w-full md:w-[calc(100%-270px)]" : "mx-auto w-full 2xl:max-w-300"}`}
        >
          {children}
        </main>
        <ReportSidebar />
      </div>
    </>
  )
}
