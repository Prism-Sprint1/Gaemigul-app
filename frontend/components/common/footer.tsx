import Image from "next/image"

import Logo from "@/public/images/logo-footer.svg"

export default function Footer() {
  return (
    <footer className="flex h-max flex-col items-center justify-center gap-5 bg-neutral-800 px-6 py-8 text-center text-xs text-neutral-300">
      <p>
        본 서비스가 제공하는 정보는 투자 판단을 돕기 위한 참고 자료이며, 특정
        종목의 매수·매도를 권유하거나 투자를 조언하는 것이 아닙니다. 투자에 대한
        최종 결정과 책임은 투자자 본인에게 있습니다.
        <br /> <br />
        시세: 한국투자증권 · 뉴스: finlight, 네이버 뉴스 · 일정: FRED 지수 15분
        · 히트맵 10분 간격으로 자동 갱신됩니다.
      </p>
      <Image src={Logo} alt="개미굴 로고" width={80} className="mt-5" />
    </footer>
  )
}
