import "./globals.css"
import localFont from "next/font/local"
// import { ThemeProvider } from "@/components/theme-provider"
import { cn } from "@/lib/utils"

import { Header } from "@/components/common"
import { Sidebar } from "@/components/common"

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
        <Header />
        <div className="flex">
          <Sidebar />
          <main className="w-full px-12.5 py-10">{children}</main>
        </div>
        {/* <ThemeProvider></ThemeProvider> */}
      </body>
    </html>
  )
}
