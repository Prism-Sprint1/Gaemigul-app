"use client"

import { useEffect, useId, useMemo, useRef, useState } from "react"
import { ChevronRight, Expand, Search } from "lucide-react"
import {
  formatChange,
  formatKoreanAmount,
  heatmapColor,
  layoutMarketCapTreemap,
  selectHeatmapSectors,
} from "@/lib/heatmap-layout"
import type { HeatmapSector, HeatmapStock } from "@/lib/types/HeatmapType"
import HeatmapLegend from "./HeatmapLegend"
import HeatmapStockDetail from "./HeatmapStockDetail"

export default function HeatmapTree({ sectors }: { sectors: HeatmapSector[] }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const detailId = useId()
  const [size, setSize] = useState({ width: 0, height: 0 })
  const [sectorCode, setSectorCode] = useState<string | null>(null)
  const [activeCode, setActiveCode] = useState<string | null>(null)
  const [search, setSearch] = useState("")
  const displayedSectors = useMemo(
    () => selectHeatmapSectors(sectors),
    [sectors]
  )
  const currentSector = displayedSectors.find(
    (sector) => sector.code === sectorCode
  )

  useEffect(() => {
    const element = containerRef.current
    if (!element) return
    const observer = new ResizeObserver(([entry]) => {
      setSize({
        width: entry.contentRect.width,
        height: entry.contentRect.height,
      })
    })
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  const sectorRects = useMemo(
    () =>
      layoutMarketCapTreemap(
        currentSector ? [currentSector] : displayedSectors,
        (sector) => sector.market_cap,
        size.width,
        size.height
      ),
    [currentSector, displayedSectors, size]
  )

  const allStocks = useMemo(
    () =>
      displayedSectors.flatMap((sector) =>
        sector.stocks.map((stock) => ({ sector, stock }))
      ),
    [displayedSectors]
  )
  const selected = allStocks.find(({ stock }) => stock.code === activeCode)
  const query = search.trim().toLocaleLowerCase()
  const matchedCodes = useMemo(() => {
    if (!query) return null
    const codes = new Set<string>()
    for (const { stock } of allStocks) {
      if (
        stock.name.toLocaleLowerCase().includes(query) ||
        stock.code.includes(query)
      )
        codes.add(stock.code)
    }
    return codes
  }, [allStocks, query])

  function selectSector(code: string | null) {
    setSectorCode(code)
    setActiveCode(null)
    setSearch("")
  }

  function stockTile(stock: HeatmapStock, width: number, height: number) {
    const showName = width >= 25 && height >= 21
    const showChange = width >= 38 && height >= 40
    const fontSize =
      width >= 125 && height >= 95
        ? 17
        : width >= 76 && height >= 65
          ? 12
          : width < 50
            ? 9
            : 10
    const selectedTile = activeCode === stock.code
    const dimmed = matchedCodes !== null && !matchedCodes.has(stock.code)
    return (
      <button
        type="button"
        tabIndex={showName ? 0 : -1}
        aria-label={`${stock.name}, ${formatChange(stock.change_rate)}, 시가총액 ${formatKoreanAmount(stock.market_cap)}`}
        title={`${stock.name} · ${formatChange(stock.change_rate)}\n현재가 ${stock.price.toLocaleString("ko-KR")}원\n시가총액 ${stock.market_cap.toLocaleString("ko-KR")}원\n거래량 ${stock.volume.toLocaleString("ko-KR")}주`}
        aria-describedby={selectedTile ? detailId : undefined}
        onMouseMove={() => setActiveCode(stock.code)}
        onFocus={() => setActiveCode(stock.code)}
        onClick={() => setActiveCode(stock.code)}
        className="absolute inset-px flex cursor-pointer flex-col items-center justify-center overflow-hidden px-0.5 text-center text-white transition-[filter,opacity] hover:z-10 hover:brightness-110 focus-visible:z-10 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-white"
        style={{
          backgroundColor: heatmapColor(stock.change_rate),
          boxShadow: selectedTile ? "inset 0 0 0 2px white" : undefined,
          opacity: dimmed ? 0.25 : 1,
          fontSize,
          lineHeight: 1.25,
        }}
      >
        {showName && (
          <span className="line-clamp-2 max-w-full font-semibold break-all">
            {stock.name}
          </span>
        )}
        {showChange && (
          <span className="mt-0.5 font-medium tabular-nums">
            {stock.change_rate === null ? "—" : formatChange(stock.change_rate)}
          </span>
        )}
      </button>
    )
  }

  return (
    <div className="min-w-0">
      <div className="mb-3 flex flex-wrap justify-between gap-2">
        <HeatmapStockDetail id={detailId} selected={selected} />
        <div className="flex flex-col justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative w-full sm:w-48">
              <Search className="pointer-events-none absolute top-2 left-2.5 size-3.5 text-neutral-400" />
              <label className="sr-only" htmlFor="heatmap-search">
                종목명 또는 종목코드 검색
              </label>
              <input
                id="heatmap-search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Escape") setSearch("")
                }}
                placeholder="표시된 기업 검색"
                autoComplete="off"
                className="h-8 w-full rounded-sm border border-neutral-200 bg-white pr-2 pl-8 text-xs shadow-sm outline-offset-2 placeholder:text-neutral-400 focus-visible:outline-point"
              />
            </div>
            <label className="sr-only" htmlFor="heatmap-sector">
              확대할 업종 선택
            </label>
            <select
              id="heatmap-sector"
              value={currentSector?.code ?? ""}
              onChange={(event) => selectSector(event.target.value || null)}
              className="h-8 max-w-44 rounded-md border border-neutral-200 bg-white px-2 text-xs text-neutral-600 outline-offset-2 focus-visible:outline-point"
            >
              <option value="">전체</option>
              {displayedSectors.map((sector) => (
                <option key={sector.code} value={sector.code}>
                  {sector.name}
                </option>
              ))}
            </select>
          </div>
          <HeatmapLegend />
        </div>
      </div>

      <p className="mb-2 text-[10px] leading-5 text-neutral-500">
        시가총액 상위 {displayedSectors.length}개 업종 · 업종별 대표 기업 5개 ·
        총 {allStocks.length}개 기업
        {displayedSectors.length < 15 &&
          " · 시세가 있는 기업 5개 이상인 업종만 표시합니다."}
        {currentSector && ` · 현재 ${currentSector.name} 확대 중`}
      </p>

      <div
        ref={containerRef}
        aria-label={
          currentSector
            ? `${currentSector.name} 업종 히트맵`
            : `주요 ${displayedSectors.length}개 업종 주식 히트맵`
        }
        className={`relative w-full overflow-hidden rounded-lg border border-slate-700 bg-slate-800 ${currentSector ? "h-[520px] sm:h-[720px]" : "h-[1200px] sm:h-[780px] 2xl:h-[820px]"}`}
      >
        {sectorRects.map(({ item: sector, x, y, width, height }) => {
          const compact = width < 58 || height < 44
          const headerHeight = compact ? height : 23
          const stocks = compact
            ? []
            : layoutMarketCapTreemap(
                sector.stocks,
                (stock) => stock.market_cap,
                Math.max(0, width - 4),
                Math.max(0, height - headerHeight - 4)
              )
          return (
            <div
              key={sector.code}
              className="absolute overflow-hidden border border-slate-800"
              style={{ left: x, top: y, width, height }}
            >
              <button
                type="button"
                onClick={() => selectSector(currentSector ? null : sector.code)}
                aria-label={`${sector.name}, ${sector.stocks.length}개 종목, ${currentSector ? "주요 업종 보기" : "확대 보기"}`}
                className="flex w-full cursor-pointer items-center justify-between gap-1 overflow-hidden bg-slate-700 px-1.5 text-left text-[10px] font-semibold text-white hover:bg-slate-600 focus-visible:relative focus-visible:z-10 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-white"
                style={{ height: headerHeight }}
              >
                <span className="truncate">{sector.name}</span>
                {width > 90 && (
                  <Expand className="size-2.5 shrink-0 opacity-60" />
                )}
              </button>
              {stocks.map(
                ({
                  item: stock,
                  x: stockX,
                  y: stockY,
                  width: stockWidth,
                  height: stockHeight,
                }) => (
                  <div
                    key={stock.code}
                    className="absolute"
                    style={{
                      left: stockX + 1,
                      top: stockY + headerHeight + 1,
                      width: stockWidth,
                      height: stockHeight,
                    }}
                  >
                    {stockTile(stock, stockWidth, stockHeight)}
                  </div>
                )
              )}
            </div>
          )
        })}
      </div>

      {currentSector && (
        <details className="mt-3 rounded-lg border border-neutral-200 bg-white text-xs">
          <summary className="cursor-pointer px-3 py-2.5 font-medium text-neutral-600">
            {currentSector.name} 대표 {currentSector.stocks.length}개 기업 목록
          </summary>
          <div className="max-h-56 overflow-auto border-t border-neutral-100 p-1">
            {[...currentSector.stocks]
              .sort((a, b) => b.market_cap - a.market_cap)
              .map((stock) => (
                <button
                  key={stock.code}
                  type="button"
                  onClick={() => setActiveCode(stock.code)}
                  className="flex w-full cursor-pointer items-center gap-2 rounded px-2 py-2 text-left hover:bg-neutral-50 focus-visible:bg-neutral-100"
                >
                  <span className="min-w-0 flex-1 truncate">
                    {stock.name}{" "}
                    <span className="text-[10px] text-neutral-400">
                      {stock.code}
                    </span>
                  </span>
                  <span
                    className="tabular-nums"
                    style={{
                      color:
                        stock.change_rate === null || stock.change_rate === 0
                          ? "#737373"
                          : stock.change_rate > 0
                            ? "#e52828"
                            : "#2563eb",
                    }}
                  >
                    {formatChange(stock.change_rate)}
                  </span>
                  <ChevronRight className="size-3 text-neutral-400" />
                </button>
              ))}
          </div>
        </details>
      )}
    </div>
  )
}
