import Link from "next/link"
import Image from "next/image"
import { Badge, Separator } from "@/components/ui"

import Logo from "@/public/images/logo.svg"

import Marquee from "../marquee/marquee"
import { Info } from "lucide-react"

export default function Header() {
  return (
    <header className="left-00 fixed top-0 flex w-full">
      <Link
        href={"/"}
        className="flex min-w-67.5 items-center justify-between pl-5"
      >
        <Image src={Logo} alt="개미굴 로고"></Image>
        <div className="flex items-center gap-2.5">
          <Badge className="bg-point text-[12px] font-semibold text-white">
            BETA
          </Badge>
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
    </header>
  )
}
