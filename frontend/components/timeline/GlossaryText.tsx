import { Fragment } from "react"

type GlossaryTextProps = {
  text: string
  /** GET /timeline/glossary 응답 {용어: 설명}. 없으면 원문 그대로 보여준다. */
  glossary: Record<string, string>
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
}

/** 본문 중 용어 사전에 있는 단어에만 연한 배경을 주고, 호버 시 설명을 띄운다. */
export default function GlossaryText({ text, glossary }: GlossaryTextProps) {
  const terms = Object.keys(glossary).sort((a, b) => b.length - a.length)

  if (!text || terms.length === 0) return <>{text}</>

  const pattern = new RegExp(`(${terms.map(escapeRegExp).join("|")})`, "g")
  const parts = text.split(pattern)
  // 같은 카드(하나의 GlossaryText) 안에서는 같은 단어를 두 번째부터 강조하지 않는다.
  const seen = new Set<string>()

  return (
    <>
      {parts.map((part, index) => {
        const description = glossary[part]

        if (!description || seen.has(part)) {
          return <Fragment key={index}>{part}</Fragment>
        }
        seen.add(part)

        return (
          <span
            key={index}
            className="group relative inline-block cursor-help rounded bg-point/10 px-0.5 text-point"
          >
            {part}
            <span className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-1.5 w-56 -translate-x-1/2 rounded-lg border border-neutral-200 bg-white p-2.5 text-[11px] leading-relaxed font-normal text-neutral-600 opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100">
              {description}
            </span>
          </span>
        )
      })}
    </>
  )
}
