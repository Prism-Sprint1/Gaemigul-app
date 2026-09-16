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

export interface TodayAntTerm {
  term: string
  hanja: string
  example: string
}

export const todayAntTerm: TodayAntTerm = {
  term: "PER (주가수익비율)",
  hanja: "Price Earning Ratio",
  example:
    "연간 1억을 버는 치킨집의 권리금이 10억이라면 PER은 10배! 투자금을 회수하는 데 걸리는 햇수예요.",
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

// ── 개미굴 심리지수 ──────────────────────────────────────────

export interface AntColonySentimentDummy {
  value: number
  description: string
}

export const antColonySentiment: AntColonySentimentDummy = {
  value: 68,
  description: "개미굴 전반적으로 적극적인 매수 심리가 우세해요.",
}

export interface SentimentLevel {
  label: string
  color: string
  /** 이 등급으로 판정되는 상한값(미포함). 마지막 구간은 Infinity. */
  max: number
}

export const sentimentLevels: SentimentLevel[] = [
  { label: "극단적 공포", color: "#4A90D9", max: 25 },
  { label: "공포", color: "#6FCF97", max: 45 },
  { label: "중립", color: "#9CA3AF", max: 55 },
  { label: "탐욕", color: "#F0A63E", max: 75 },
  { label: "극단적 탐욕", color: "#FF2A2A", max: Infinity },
]

export function getSentimentLevel(value: number): SentimentLevel {
  return (
    sentimentLevels.find((level) => value < level.max) ??
    sentimentLevels[sentimentLevels.length - 1]
  )
}

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

export interface UsdKrwTrendDummy {
  current: number
  change: number
  changeRate: number
  series: ExchangeRatePoint[]
}

export const usdKrwTrend: UsdKrwTrendDummy = {
  current: 1391.5,
  change: 4.2,
  changeRate: 0.3,
  series: [
    1387.3, 1388.1, 1386.9, 1389.4, 1390.2, 1388.8, 1389.9, 1390.6, 1392.1,
    1391.4, 1393.2, 1392.5, 1390.8, 1391.5,
  ].map((value, index) => ({ time: intradayTimeLabels[index], value })),
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

// ── 오늘의 비축 캘린더 일정 ─────────────────────────────────────

export interface CalendarScheduleItem {
  time: string
  title: string
  tag: string
}

export const todayCalendarSchedule: CalendarScheduleItem[] = [
  { time: "09:00", title: "국내 증시 개장", tag: "국장" },
  { time: "10:30", title: "8월 산업생산 발표", tag: "지표" },
  { time: "15:30", title: "국내 증시 마감 · 동시호가", tag: "국장" },
  { time: "21:30", title: "미국 소비자물가지수(CPI) 발표", tag: "미장" },
  { time: "23:00", title: "미국 국채 3년물 입찰", tag: "채권" },
]
