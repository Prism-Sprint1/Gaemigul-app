import "./globals.css"
import localFont from "next/font/local"
// import { ThemeProvider } from "@/components/theme-provider"
import { cn } from "@/lib/utils"

import {
  Footer,
  Header,
  Sidebar,
  MobileSidebarProvider,
} from "@/components/common"

const pretendard = localFont({
  src: "../public/fonts/pretendard/PretendardVariable.woff2",
  display: "swap",
  weight: "100 900",
  variable: "--font-pretendard",
})

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="ko"
      suppressHydrationWarning
      className={cn("antialiased", pretendard.variable, "font-sans")}
    >
      <body>
        <MobileSidebarProvider>
          <Header />
          <div className="flex">
            <Sidebar />
            <main className="w-full px-12.5 py-10">{children}</main>
          </div>
        </MobileSidebarProvider>
        <Footer
          title="본 서비스가 제공하는 정보는 투자 판단을 돕기 위한 참고 자료이며, 특정 종목의 매수·매도를 권유하거나 투자를 조언하는 것이 아닙니다. 투자에 대한 최종 결정과 책임은 투자자 본인에게 있습니다."
          description="시세: 한국투자증권 · 뉴스: finlight, 네이버 뉴스 · 일정: FRED 지수 15분 · 히트맵 10분 간격으로 자동 갱신됩니다."
        />
        {/* <ThemeProvider></ThemeProvider> */}
      </body>
    </html>
  )
}
