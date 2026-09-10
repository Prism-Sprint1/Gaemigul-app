import type { TimelineItem } from "@/lib/types/TimelineType"

export const timelineItems: TimelineItem[] = [
  {
    id: "schedule-1",
    time: "07:30",
    title: "글로벌 시황",
    description: "간밤 글로벌 증시 및 매크로 지표 요약",
  },
  {
    id: "schedule-2",
    time: "08:30",
    title: "NXT 프리마켓",
    description: "장 시작 전 주요 이슈 점검",
  },
  {
    id: "schedule-3",
    time: "09:30",
    title: "장초반 흐름",
    description: "개장 직후 테마 및 수급 동향 점검",
  },
  {
    id: "schedule-4",
    time: "12:00",
    title: "오전장 흐름",
    description: "오전장 주요 테마·섹터 및 수급 동향",
  },
  {
    id: "schedule-5",
    time: "14:00",
    title: "오후장 흐름",
    description: "오후장 수급 동향 및 변동성 브리핑",
  },
  {
    id: "schedule-6",
    time: "15:30",
    title: "장 마감",
    description: "정규장 마감 후 주도 테마 정리",
  },
  {
    id: "schedule-7",
    time: "17:30",
    title: "애프터마켓",
    description: "시간외 단일가 특징주 및 시장 이슈",
  },
  {
    id: "schedule-8",
    time: "20:00",
    title: "오늘 시장 분석",
    description: "섹터 총평 및 내일 체크포인트",
  },
]
