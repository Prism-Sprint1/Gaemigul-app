import axios from "axios"

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://localhost:8000"
const VIX_URL = `${API_BASE_URL.replace(/\/$/, "")}/market/vix`

export interface VixResponse {
  value: number
  change_value: number
  market_date: string | null
  updated_at: string
}

/** GET /market/vix — 캐시된 VIX 공포지수. 캐시가 없으면 503. */
export async function getVix(): Promise<VixResponse> {
  const response = await axios.get<VixResponse>(VIX_URL)
  return response.data
}
