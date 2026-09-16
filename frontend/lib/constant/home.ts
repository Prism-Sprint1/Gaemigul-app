// 백엔드 연동 전까지 사용하는 메인 페이지 더미 데이터.

export interface PheromoneScalePoint {
  value: number
  label: string
}

export interface PheromoneTemperatureDummy {
  value: number
  status: string
  statusEn: string
  description: string
  vixValue: number
  vixChange: number
  fiveDayAverage: number
  scale: PheromoneScalePoint[]
  maxScale: number
}

export const pheromoneTemperature: PheromoneTemperatureDummy = {
  value: 15.48,
  status: "안정",
  statusEn: "Calm",
  description: "현재 시장 변동성이 평소 수준이에요. 특별한 이상 신호는 없어요.",
  vixValue: 15.48,
  vixChange: -0.62,
  fiveDayAverage: 16.1,
  scale: [
    { value: 0, label: "극단적 저변동" },
    { value: 15, label: "안정" },
    { value: 25, label: "보통" },
    { value: 35, label: "고변동" },
    { value: 50, label: "극단적 충격" },
  ],
  maxScale: 60,
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
