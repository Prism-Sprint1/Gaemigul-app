import type { BriefingGlossaryTerm } from "@/lib/types/BriefingType"

type BriefingGlossaryProps = {
  terms: BriefingGlossaryTerm[]
}

export default function BriefingGlossary({ terms }: BriefingGlossaryProps) {
  return (
    <div className="flex flex-col gap-3 border-t border-neutral-100 pt-8">
      <p className="text-basic flex items-center gap-1 font-bold text-point2">
        <span aria-hidden>📘</span>
        주린이 1분 금융 용어 사전
      </p>
      <div className="grid gap-3 sm:grid-cols-3">
        {terms.map((term) => (
          <div
            key={term.term}
            className="flex flex-col gap-1 rounded-lg border border-neutral-200 p-4 shadow-sm"
          >
            <span className="text-sm font-semibold">{term.term}</span>
            <p className="text-xs leading-relaxed text-neutral-500">
              {term.description}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
