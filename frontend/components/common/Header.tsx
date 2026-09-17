"use client"

import Link from "next/link"
import Image from "next/image"
import { useEffect, useRef } from "react"
import { Badge, Separator } from "@/components/ui"

import Logo from "@/public/images/logo.svg"

import Marquee from "../marquee/marquee"
import { Info, Menu } from "lucide-react"

import { useMobileSidebar } from "./sidebar"

export default function Header() {
  const { toggle } = useMobileSidebar()
  const headerRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const node = headerRef.current
    if (!node) return

    const updateHeaderHeight = () => {
      document.documentElement.style.setProperty(
        "--header-height",
        `${node.offsetHeight}px`
      )
    }

    updateHeaderHeight()
    const observer = new ResizeObserver(updateHeaderHeight)
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  return (
    <header ref={headerRef} className="sticky top-0 z-30 w-full bg-background">
      {/* 데스크톱 헤더 (기존 그대로) */}
      <div className="hidden w-full md:flex">
        <Link
          href={"/"}
          className="flex min-w-67.5 items-center justify-between pl-5"
        >
          <Image src={Logo} alt="개미굴 로고"></Image>
          <div className="flex items-center gap-2.5">
            <Separator orientation="vertical" />
          </div>
        </Link>
        <Marquee></Marquee>
        <div className="flex min-w-67.5 flex-col justify-center gap-0.5 px-3">
          <strong className="flex items-center gap-1 text-[18px] text-point">
            <Badge className="bg-point text-[12px] text-white">TIMER</Badge>
            25:24
          </strong>
          <p className="flex items-center gap-1 text-[10px] text-neutral-500">
            <Info size="14" />
            지수 데이터는 정시 기준 30분마다 갱신됩니다.
          </p>
        </div>
      </div>

      {/* 모바일 헤더: 좌측 로고 / 우측 TIMER + 햄버거 메뉴, 같은 높이로 정렬 */}
      <div className="flex w-full items-center justify-between px-4 pt-4 pb-3 md:hidden">
        <Link href={"/"} className="flex items-center">
          <Image src={Logo} alt="개미굴 로고" className="h-9 w-auto" />
        </Link>
        <div className="flex items-center gap-3">
          <strong className="flex items-center gap-1 text-[16px] text-point">
            <Badge className="bg-point text-[12px] text-white">TIMER</Badge>
            25:24
          </strong>
          <button
            type="button"
            onClick={toggle}
            aria-label="메뉴 열기"
            className="p-1 text-neutral-500"
          >
            <Menu size={24} />
          </button>
        </div>
      </div>

      {/* 모바일: 헤더 아래 지수 데이터 티커 */}
      <div className="w-full md:hidden">
        <Marquee></Marquee>
      </div>
    </header>
  )
}
