import axios from "axios"

import type { ApiTimelineSlot } from "@/lib/types/TimelineType"

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://localhost:8000"
const TIMELINE_URL = `${API_BASE_URL.replace(/\/$/, "")}/timeline`

/** GET /timeline?date=YYYY-MM-DD — 하루치 슬롯 목록. date를 빼면 오늘. */
export async function getTimelineDay(date?: string): Promise<ApiTimelineSlot[]> {
  const response = await axios.get<ApiTimelineSlot[]>(TIMELINE_URL, {
    params: date ? { date } : undefined,
  })

  return response.data
}

/** GET /timeline/glossary — 용어 사전 {용어: 설명}. 본문 호버 툴팁에 쓴다. */
export async function getTimelineGlossary(): Promise<Record<string, string>> {
  const response = await axios.get<Record<string, string>>(
    `${TIMELINE_URL}/glossary`
  )

  return response.data
}
