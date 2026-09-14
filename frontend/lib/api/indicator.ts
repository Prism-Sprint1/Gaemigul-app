import axios from "axios"

const INDICATORS_URL = "http://127.0.0.1:8000/timeline/indicators"

export interface MarketIndicatorItem {
  code: string
  name: string
  price: number
  change_rate: number
}

export interface IndicatorBarResponse {
  updated_at: string
  items: MarketIndicatorItem[]
}

export async function getTimelineIndicators(): Promise<IndicatorBarResponse> {
  const response = await axios.get<IndicatorBarResponse>(INDICATORS_URL, {
    responseType: "json",
  })

  return response.data
}
