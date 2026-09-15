import Image from "next/image"

import Logo from "@/public/images/logo-footer.svg"

interface FooterProps {
  title: string
  description: string
}

export default function Footer({ title, description }: FooterProps) {
  return (
    <footer className="flex min-h-42.5 flex-col items-center justify-center gap-5 bg-neutral-800 px-6 py-8 text-center text-white">
      <div className="flex flex-col gap-2 text-[10px] leading-relaxed text-neutral-300">
        <p>{title}</p>
        <p>{description}</p>
      </div>
      <Image src={Logo} alt="개미굴 로고" width={48} height={24} />
    </footer>
  )
}
