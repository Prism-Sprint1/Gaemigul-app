// 아티클 순서(0-based id)에 따라 순환 적용되는 강조 색상.
// 0번은 앱 공통 포인트 컬러를 그대로 쓰고, 이후 순서는 지정된 팔레트를 사용한다.
const BRIEFING_ACCENT_COLORS = ["var(--color-point)", "#2563EB", "#059669"]

export function getBriefingAccentColor(id: number) {
  return BRIEFING_ACCENT_COLORS[id % BRIEFING_ACCENT_COLORS.length]
}
