import type { TimelineItem } from "@/lib/types/TimelineType"

// id는 백엔드 슬롯 키(slot_key, 콜론 없는 4자리)와 맞춘다.
// GET /timeline 응답의 각 슬롯을 이 목록과 매칭해 순서·제목·잠금 상태를 만든다.
export const timelineItems: TimelineItem[] = [
  {
    id: "0730",
    time: "07:30",
    title: "글로벌 시황",
    description: "간밤 글로벌 증시 및 매크로 지표 요약",
  },
  {
    id: "0830",
    time: "08:30",
    title: "NXT 프리마켓",
    description: "장 시작 전 주요 이슈 점검",
  },
  {
    id: "0930",
    time: "09:30",
    title: "장초반 흐름",
    description: "개장 직후 테마 및 수급 동향 점검",
  },
  {
    id: "1200",
    time: "12:00",
    title: "오전장 흐름",
    description: "오전장 주요 테마·섹터 및 수급 동향",
  },
  {
    id: "1400",
    time: "14:00",
    title: "오후장 흐름",
    description: "오후장 수급 동향 및 변동성 브리핑",
  },
  {
    id: "1530",
    time: "15:30",
    title: "장 마감",
    description: "정규장 마감 후 주도 테마 정리",
  },
  {
    id: "1730",
    time: "17:30",
    title: "애프터마켓",
    description: "시간외 단일가 특징주 및 시장 이슈",
  },
  {
    id: "2000",
    time: "20:00",
    title: "오늘 시장 분석",
    description: "섹터 총평 및 내일 체크포인트",
  },
]
