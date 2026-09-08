import type { CalendarEvent } from '@/components/ui/full-calendar'

/* 뉴스 데이터 — TODO: API 연동 시 NEWS 배열만 교체 */

export type Category = 'macro' | 'earnings' | 'ipo' | 'dividend'

export type NewsItem = {
  id: string
  title: string
  summary: string
  category: Category
  region: string
  publishedAt: Date
  highlight?: 'focus' | 'special' // 날짜 그룹 배지
  url?: string
  /** 팝업 상세에만 노출 — 있는 값만 표시 */
  detail?: {
    forecast?: string // 예상치
    previous?: string // 이전치
    source?: string // 발표처
    sectors?: string[] // 관련 수혜 섹터
  }
}

export const CAT: Record<
  Category,
  {
    label: string
    dot: string
    text: string
    card: string
    /** 왼쪽 캘린더 색 점(variant 이름) */
    event: 'red' | 'green' | 'blue' | 'amber'
  }
> = {
  macro: { label: '매크로/금리', dot: 'bg-red-500', text: 'text-red-500', card: 'border-l-red-500 bg-red-500/5', event: 'red' }, // prettier-ignore
  earnings: { label: '기업 실적', dot: 'bg-emerald-500', text: 'text-emerald-600', card: 'border-l-emerald-500 bg-emerald-500/5', event: 'green' }, // prettier-ignore
  ipo: { label: '공모주/보호예수', dot: 'bg-blue-500', text: 'text-blue-600', card: 'border-l-blue-500 bg-blue-500/5', event: 'blue' }, // prettier-ignore
  dividend: { label: '배당/옵션만기', dot: 'bg-amber-500', text: 'text-amber-600', card: 'border-l-amber-500 bg-amber-500/5', event: 'amber' }, // prettier-ignore
}

export const CATS = Object.keys(CAT) as Category[]

export const NEWS: NewsItem[] = [
  { id: 'n1', title: '8월 NFIB 중소기업 경기 낙관지수', summary: '미국 고용의 50% 이상을 차지하는 중소기업 경기 체감지표입니다. 예상치(91.2)를 상회할 경우 연착륙(Soft Landing)에 힘이 실리며 리테일 및 소비재 종목이 탄력을 받을 수 있습니다.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-07T22:30:00'), highlight: 'focus', detail: { forecast: '91.2', previous: '90.3', source: '미국소상공인연맹', sectors: ['필수소비재', '소매유통(XRT)', '소형주(러셀 2000)'] } }, // prettier-ignore
  { id: 'n2', title: 'ECB 통화정책회의 사전 브리핑', summary: '라가르드 총재 연설 전 물가 코멘트 점검.', category: 'dividend', region: '유로존', publishedAt: new Date('2026-09-07T17:00:00')}, // prettier-ignore
  { id: 'n3', title: '미국 1년 기대인플레이션율 조사', summary: '뉴욕연은 소비자기대 서베이. 단기 물가 기대 흐름 확인.', category: 'macro', region: '뉴욕연은', publishedAt: new Date('2026-09-07T23:00:00')}, // prettier-ignore
  { id: 'n4', title: '국내 신규 상장 공모주 상장일', summary: '공모가 대비 시초가 변동성 주의.', category: 'ipo', region: '공모주', publishedAt: new Date('2026-09-08T09:00:00')}, // prettier-ignore
  { id: 'n5', title: '미국 8월 무역수지 발표', summary: '수출입 증감과 달러 흐름 연동 여부 점검.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-08T21:30:00')}, // prettier-ignore
  { id: 'n6', title: '아이폰 및 신규 3nm 인공지능 프로세서 공개', summary: '국내 반도체/디스플레이 밸류체인 수혜 점검.', category: 'ipo', region: '애플', publishedAt: new Date('2026-09-09T02:00:00'), highlight: 'special' }, // prettier-ignore
]

/** NEWS → 왼쪽 캘린더 이벤트(색 점 표시용, 제목은 표시 안 함) */
export const NEWS_EVENTS: CalendarEvent[] = NEWS.map((n) => ({
  id: n.id,
  start: n.publishedAt,
  end: n.publishedAt,
  title: n.title,
  color: CAT[n.category].event,
}))
