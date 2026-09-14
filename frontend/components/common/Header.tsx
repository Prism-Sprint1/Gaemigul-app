import Link from "next/link"
import Image from "next/image"
import { Badge, Separator } from "@/components/ui"

import Logo from "@/public/images/logo.svg"

import Marquee from "../marquee/marquee"
import HeaderTimer from "./HeaderTimer"
import { Info } from "lucide-react"

export default function Header() {
  return (
    <header className="top-0 flex w-full items-center">
      {/* 앱(모바일)에서는 BETA 뱃지·티커·타이머를 숨기고 로고만 왼쪽 정렬로 노출 */}
      <Link
        href={"/"}
        className="flex items-center gap-2.5 py-3 pl-4 lg:min-w-67.5 lg:justify-between lg:py-0 lg:pl-5"
      >
        <Image src={Logo} alt="개미굴 로고"></Image>
        <div className="hidden items-center gap-2.5 lg:flex">
          <Badge className="bg-point text-[12px] font-semibold text-white">
            BETA
          </Badge>
          <Separator orientation="vertical" />
        </div>
      </Link>

      <div className="hidden lg:flex lg:flex-1">
        <Marquee></Marquee>
      </div>

      <div className="hidden lg:flex lg:min-w-67.5 lg:flex-col lg:justify-center lg:gap-0.5 lg:px-3">
        <HeaderTimer />
        <p className="flex items-center gap-1 text-[10px] text-neutral-500">
          <Info size="14" />
          지수 데이터는 정시 기준 30분마다 갱신됩니다.
        </p>
      </div>
    </header>
  )
}
