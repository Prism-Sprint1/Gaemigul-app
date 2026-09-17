// 백엔드 연동 전까지 사용하는 메인 페이지 더미 데이터.

export interface PheromoneScalePoint {
  value: number
  label: string
}

export const pheromoneScale: PheromoneScalePoint[] = [
  { value: 0, label: "극단적 저변동" },
  { value: 15, label: "안정" },
  { value: 25, label: "보통" },
  { value: 35, label: "고변동" },
  { value: 50, label: "극단적 충격" },
]

export const pheromoneMaxScale = 60

export interface PheromoneLevel {
  status: string
  statusEn: string
  description: string
  color: string
  /** 이 등급으로 판정되는 VIX 상한값(미포함). 마지막 구간은 Infinity. */
  max: number
}

/** VIX 값에 따른 등급·문구·색상 매핑. main.py 스케줄러가 30분마다 갱신하는 /market/vix 값을 기준으로 판정한다. */
export const pheromoneLevels: PheromoneLevel[] = [
  {
    status: "안정",
    statusEn: "Calm",
    description: "현재 시장 변동성이 낮고 안정적인 흐름을 유지하고 있어요.",
    color: "#4A90D9",
    max: 25,
  },
  {
    status: "보통",
    statusEn: "Normal",
    description: "현재 시장 변동성이 평소 수준이에요. 특별한 이상 신호는 없어요.",
    color: "#6FCF97",
    max: 35,
  },
  {
    status: "고변동",
    statusEn: "Volatile",
    description:
      "최근 시장 변동성이 커지고 있어요. 가격 움직임을 조금 더 주의 깊게 살펴보세요.",
    color: "#F0A63E",
    max: 50,
  },
  {
    status: "극단적 충격",
    statusEn: "Panic",
    description:
      "시장 변동성이 매우 큰 상태예요. 단기적으로 가격이 급격히 움직일 수 있어요.",
    color: "#FF2A2A",
    max: Infinity,
  },
]

export function getPheromoneLevel(vixValue: number): PheromoneLevel {
  return (
    pheromoneLevels.find((level) => vixValue < level.max) ??
    pheromoneLevels[pheromoneLevels.length - 1]
  )
}

export interface HotSectorDummy {
  name: string
  reason: string
}

export const hotSector: HotSectorDummy = {
  name: "반도체·AI 인프라",
  reason:
    "HBM과 서버 전력 부품 수요가 함께 늘면서 관련 부품주까지 낙수효과가 번지고 있어요.",
}

export interface CalendarHighlightDummy {
  time: string
  title: string
}

export const calendarHighlight: CalendarHighlightDummy = {
  time: "21:30",
  title: "미국 소비자물가지수(CPI) 발표",
}

// ── 글로벌 장운영 현황 ──────────────────────────────────────────

export interface MarketSessionSchedule {
  /** 국장 개장 */
  domesticOpen: string
  /** 국장 동시호가 시작 */
  domesticAuctionStart: string
  /** 국장 마감 */
  domesticClose: string
  /** 미국 프리마켓 시작 */
  usPreMarketStart: string
  /** 미국 정규장 시작(한국시간) */
  usRegularStart: string
  /** 미국 정규장 마감(한국시간, 익일) */
  usRegularEnd: string
}

/** 시:분(HH:mm) 문자열 기준 장 스케줄. 실데이터 연동 전까지 이 스케줄로 자동 전환 문구를 계산한다. */
export const marketSessionSchedule: MarketSessionSchedule = {
  domesticOpen: "09:00",
  domesticAuctionStart: "15:20",
  domesticClose: "15:30",
  usPreMarketStart: "17:00",
  usRegularStart: "22:30",
  usRegularEnd: "05:00",
}

// ── 페로몬 신호 강도 ──────────────────────────────────────────

export interface PheromoneSignalDummy {
  value: number
}

export const pheromoneSignalStrength: PheromoneSignalDummy = {
  value: 68,
}

export interface PheromoneSignalLevel {
  /** 와이파이 신호 막대 중 채워지는 개수(1~5) */
  bars: number
  label: string
  description: string
  /** 이 등급으로 판정되는 상한값(미포함). 마지막 구간은 Infinity. */
  max: number
}

/** 값(0~100) → 채워지는 막대 개수·라벨·설명 문구 매핑 */
export const pheromoneSignalLevels: PheromoneSignalLevel[] = [
  {
    bars: 1,
    label: "신호 약함",
    description: "지금 개미들 사이에 신호가 약하게 퍼지고 있어요",
    max: 20,
  },
  {
    bars: 2,
    label: "신호 감지됨",
    description: "지금 개미들 사이에 신호가 감지되고 있어요",
    max: 40,
  },
  {
    bars: 3,
    label: "신호 보통",
    description: "지금 개미들 사이에 신호가 보통 수준으로 퍼지고 있어요",
    max: 60,
  },
  {
    bars: 4,
    label: "신호 강함",
    description: "지금 개미들 사이에 신호가 강하게 퍼지고 있어요",
    max: 80,
  },
  {
    bars: 5,
    label: "신호 매우 강함",
    description: "지금 개미들 사이에 신호가 매우 강하게 퍼지고 있어요",
    max: Infinity,
  },
]

export function getPheromoneSignalLevel(value: number): PheromoneSignalLevel {
  return (
    pheromoneSignalLevels.find((level) => value < level.max) ??
    pheromoneSignalLevels[pheromoneSignalLevels.length - 1]
  )
}

/** 채워진 막대 개수(1~5)에 대응하는 브랜드 레드 톤 — 신호가 강할수록 진해진다. */
export const pheromoneSignalBarColors = [
  "#FFD4D4",
  "#FFA8A8",
  "#FF7A7A",
  "#FF4A4A",
  "#FF2A2A",
]

// ── 시간대별 공통 축(09:00 ~ 15:30, 30분 간격) ────────────────────

export const intradayTimeLabels = [
  "09:00",
  "09:30",
  "10:00",
  "10:30",
  "11:00",
  "11:30",
  "12:00",
  "12:30",
  "13:00",
  "13:30",
  "14:00",
  "14:30",
  "15:00",
  "15:30",
] as const

// ── 원/달러 환율 추이 ──────────────────────────────────────────

export interface ExchangeRatePoint {
  time: string
  value: number
}

export type UsdKrwRange = "day" | "week5" | "month"

export const usdKrwRangeLabels: Record<UsdKrwRange, string> = {
  day: "하루",
  week5: "5일",
  month: "월별",
}

export interface UsdKrwTrendDummy {
  current: number
  change: number
  changeRate: number
  seriesByRange: Record<UsdKrwRange, ExchangeRatePoint[]>
}

export const usdKrwTrend: UsdKrwTrendDummy = {
  current: 1391.5,
  change: 4.2,
  changeRate: 0.3,
  seriesByRange: {
    day: [
      1387.3, 1388.1, 1386.9, 1389.4, 1390.2, 1388.8, 1389.9, 1390.6, 1392.1,
      1391.4, 1393.2, 1392.5, 1390.8, 1391.5,
    ].map((value, index) => ({ time: intradayTimeLabels[index], value })),
    week5: [
      ["9/12", 1382.4],
      ["9/15", 1385.7],
      ["9/16", 1388.9],
      ["9/17", 1390.1],
      ["9/18", 1391.5],
    ].map(([time, value]) => ({ time: time as string, value: value as number })),
    month: [
      ["4월", 1362.8],
      ["5월", 1371.2],
      ["6월", 1358.6],
      ["7월", 1369.4],
      ["8월", 1378.9],
      ["9월", 1391.5],
    ].map(([time, value]) => ({ time: time as string, value: value as number })),
  },
}

// ── 시간대별 거래대금 분포 (단위: 억 원) ───────────────────────────

export interface TradingValuePoint {
  time: string
  value: number
}

export const tradingValueDistribution: TradingValuePoint[] = [
  820, 650, 540, 480, 430, 410, 380, 400, 420, 460, 520, 610, 780, 990,
].map((value, index) => ({ time: intradayTimeLabels[index], value }))

// ── 투자자별 매매동향 (단위: 억 원, +매수 / -매도) ─────────────────

export interface InvestorFlowItem {
  investor: string
  value: number
}

export const investorFlow: InvestorFlowItem[] = [
  { investor: "개인", value: 1240 },
  { investor: "외국인", value: -860 },
  { investor: "기관", value: -320 },
]

