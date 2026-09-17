import type { HeatmapSector } from "@/lib/types/HeatmapType"

/** 화면만 축약한다. 업종 전체 시가총액과 백엔드 거래량 집계는 그대로 둔다. */
export function selectHeatmapSectors(
  sectors: HeatmapSector[]
): HeatmapSector[] {
  return sectors
    .filter(
      (sector) => Number.isFinite(sector.market_cap) && sector.market_cap > 0
    )
    .map((sector) => ({
      ...sector,
      stocks: sector.stocks
        .filter(
          (stock) => Number.isFinite(stock.market_cap) && stock.market_cap > 0
        )
        .sort(
          (a, b) => b.market_cap - a.market_cap || a.code.localeCompare(b.code)
        ),
    }))
    .filter((sector) => sector.stocks.length > 0)
    .sort((a, b) => b.market_cap - a.market_cap || a.code.localeCompare(b.code))
    .slice(0, 8)
    .map((sector, index) => ({
      ...sector,
      stocks: sector.stocks.slice(0, index < 4 ? 5 : 4),
    }))
}

export interface HeatmapRect<T> {
  item: T
  x: number
  y: number
  width: number
  height: number
}

/**
 * Squarified treemap: keep adjacent rectangles readable while preserving the
 * supplied weights. Callers pass sqrt(market cap) to soften size differences.
 * No artificial minimum area is added, so the layout always fits its bounds.
 */
export function layoutTreemap<T>(
  items: T[],
  getWeight: (item: T) => number,
  width: number,
  height: number
): HeatmapRect<T>[] {
  const weighted = items
    .map((item) => ({ item, weight: getWeight(item) }))
    .filter(({ weight }) => Number.isFinite(weight) && weight > 0)
    .sort((a, b) => b.weight - a.weight)
  const total = weighted.reduce((sum, entry) => sum + entry.weight, 0)
  if (!total || width <= 0 || height <= 0) return []

  const remaining = weighted.map(({ item, weight }) => ({
    item,
    area: (weight / total) * width * height,
  }))
  const result: HeatmapRect<T>[] = []
  let x = 0
  let y = 0
  let availableWidth = width
  let availableHeight = height
  let index = 0

  function worst(areas: number[], side: number) {
    const sum = areas.reduce((value, area) => value + area, 0)
    const squared = sum * sum
    const sideSquared = side * side
    return Math.max(
      (sideSquared * Math.max(...areas)) / squared,
      squared / (sideSquared * Math.min(...areas))
    )
  }

  while (index < remaining.length) {
    const side = Math.min(availableWidth, availableHeight)
    const row = [remaining[index++]]
    while (
      index < remaining.length &&
      worst([...row.map((entry) => entry.area), remaining[index].area], side) <=
        worst(
          row.map((entry) => entry.area),
          side
        )
    ) {
      row.push(remaining[index++])
    }

    const area = row.reduce((sum, entry) => sum + entry.area, 0)
    const vertical = availableWidth >= availableHeight
    const thickness = area / (vertical ? availableHeight : availableWidth)
    let offset = 0
    row.forEach((entry, rowIndex) => {
      const length =
        rowIndex === row.length - 1
          ? (vertical ? availableHeight : availableWidth) - offset
          : entry.area / thickness
      result.push({
        item: entry.item,
        x: x + (vertical ? 0 : offset),
        y: y + (vertical ? offset : 0),
        width: vertical ? thickness : length,
        height: vertical ? length : thickness,
      })
      offset += length
    })

    if (vertical) {
      x += thickness
      availableWidth = Math.max(0, width - x)
    } else {
      y += thickness
      availableHeight = Math.max(0, height - y)
    }
  }
  return result
}

export function formatChange(rate: number | null) {
  if (rate === null || !Number.isFinite(rate)) return "등락률 미제공"
  return `${rate > 0 ? "+" : ""}${rate.toFixed(2)}%`
}

export function heatmapColor(rate: number | null) {
  if (rate === null || !Number.isFinite(rate)) return "#606875"
  if (rate === 0) return "#4b5563"
  const strength = Math.min(Math.abs(rate) / 5, 1)
  const base = [74, 78, 89]
  const target = rate > 0 ? [255, 42, 42] : [37, 99, 235]
  const color = base.map((value, i) =>
    Math.round(value + (target[i] - value) * (0.28 + strength * 0.72))
  )
  return `rgb(${color.join(", ")})`
}

export function formatKoreanAmount(value: number, unit = "원") {
  if (!Number.isFinite(value)) return "—"
  if (value >= 1_000_000_000_000)
    return `${(value / 1_000_000_000_000).toLocaleString("ko-KR", { maximumFractionDigits: 2 })}조 ${unit}`
  if (value >= 100_000_000)
    return `${(value / 100_000_000).toLocaleString("ko-KR", { maximumFractionDigits: 1 })}억 ${unit}`
  if (value >= 10_000)
    return `${(value / 10_000).toLocaleString("ko-KR", { maximumFractionDigits: 1 })}만 ${unit}`
  return `${value.toLocaleString("ko-KR")} ${unit}`
}
