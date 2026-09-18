"use client"

import { useEffect, useRef, useState } from "react"
import { cn } from "cn"

import type { TimelineStatus } from "@/lib/types/TimelineType"

export type TimelineSectionsNavItem = {
  id: string
  title: string
  status: TimelineStatus
}

type TimelineSectionsNavProps = {
  items: TimelineSectionsNavItem[]
}

const statusStyle: Record<
  TimelineStatus,
  { dot: string; chip: string; label: string }
> = {
  past: {
    dot: "bg-neutral-400",
    chip: "border-neutral-200",
    label: "text-neutral-400",
  },
  current: {
    dot: "bg-point",
    chip: "border-point bg-point/10",
    label: "font-semibold text-point",
  },
  next: {
    dot: "bg-decrease",
    chip: "border-decrease/40 bg-decrease/5",
    label: "font-medium text-decrease",
  },
  upcoming: {
    dot: "bg-neutral-900",
    chip: "border-neutral-900/20",
    label: "text-neutral-900",
  },
}

const sectionIds = (items: TimelineSectionsNavItem[]) =>
  items.map((item) => item.id).join(",")

export default function TimelineSectionsNav({
  items,
}: TimelineSectionsNavProps) {
  const [viewedId, setViewedId] = useState<string | null>(null)
  const buttonRefs = useRef<Record<string, HTMLButtonElement | null>>({})

  useEffect(() => {
    const sections = items
      .map((item) => document.getElementById(item.id))
      .filter((el): el is HTMLElement => el !== null)

    if (sections.length === 0) return

    // 헤더 + 네비게이션이 고정되어 있으므로, 그 아래 얇은 띠에 걸린 섹션을
    // "지금 보고 있는 섹션"으로 취급한다.
    const headerHeight = parseFloat(
      getComputedStyle(document.documentElement).getPropertyValue(
        "--header-height"
      )
    )
    const topOffset = (Number.isFinite(headerHeight) ? headerHeight : 75) + 56

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((entry) => entry.isIntersecting)
        if (visible.length === 0) return

        const topMost = visible.reduce((closest, entry) =>
          entry.boundingClientRect.top < closest.boundingClientRect.top
            ? entry
            : closest
        )
        setViewedId(topMost.target.id)
      },
      { rootMargin: `-${topOffset}px 0px -70% 0px`, threshold: 0 }
    )

    sections.forEach((section) => observer.observe(section))
    return () => observer.disconnect()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sectionIds(items)])

  useEffect(() => {
    if (!viewedId) return

    buttonRefs.current[viewedId]?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
      inline: "start",
    })
  }, [viewedId])

  const scrollToSection = (id: string) => {
    setViewedId(id)
    document.getElementById(id)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    })
  }

  return (
    <nav
      className="sticky z-20 -mx-5 flex gap-2 overflow-x-auto border-b border-neutral-100 bg-background/90 px-5 py-3 backdrop-blur-sm md:mx-0 md:hidden md:rounded-2xl md:border md:border-neutral-100 md:px-3 md:shadow-sm"
      style={{ top: "var(--header-height, 75px)" }}
    >
      {items.map((item) => {
        const style = statusStyle[item.status]
        const isViewed = viewedId === item.id

        return (
          <button
            key={item.id}
            type="button"
            onClick={() => scrollToSection(item.id)}
            ref={(element) => {
              buttonRefs.current[item.id] = element
            }}
            className={cn(
              "flex shrink-0 items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-[12px] whitespace-nowrap transition-all duration-200",
              style.chip,
              style.label,
              isViewed &&
                "ring-1 ring-neutral-900 ring-offset-1 ring-offset-background"
            )}
          >
            <span className="relative flex size-2 items-center justify-center">
              {item.status === "current" && (
                <span className="absolute inline-flex size-full animate-ping rounded-full bg-point opacity-60" />
              )}
              <span
                className={cn("relative z-10 size-1.5 rounded-full", style.dot)}
              />
            </span>
            {item.title}
          </button>
        )
      })}
    </nav>
  )
}
