# Next.js template

## 단물 지도 (히트맵)

`/hitmap`에서 KOSPI·KOSDAQ의 일간·주간·월간 히트맵을 확인합니다. 기존 메뉴 경로는 유지하고 내부 코드 이름은 `heatmap`을 사용합니다.

```powershell
npm install
npm run dev
```

`.env.local`의 `NEXT_PUBLIC_API_BASE_URL`에 백엔드 주소를 설정합니다(기본 `http://localhost:8000`). KIS 키는 프론트엔드에 설정하지 않습니다. 백엔드를 실행해야 실제 시세가 표시됩니다.

업종과 종목 면적은 각각 시가총액의 제곱근을 사용해 큰 종목과 작은 종목의 크기 차이를 완화합니다. 업종 확대·종목 검색·키보드 선택으로 작은 종목도 확인할 수 있으며, 실제 시가총액은 상세 정보에 표시합니다. 빨강은 상승, 파랑은 하락이며 회색의 등락률 미제공과 보합은 상세 문구로 구분합니다.

표시 범위는 시가총액 상위 8개 업종입니다. 이 중 큰 업종 4개는 시가총액 상위 기업 5개씩, 나머지 4개 업종은 4개씩 표시해 최대 36개 기업으로 줄입니다. 검색·업종 확대에도 같은 표시 범위를 적용합니다. 업종 면적은 업종 전체 시가총액을 기준으로 유지하며, 백엔드 수집과 거래량 1위 집계는 전체 대상 종목을 기준으로 합니다.

우측 업종 추천 3칸과 하단 뉴스 4칸은 준비 중인 자리입니다. 실제 추천·뉴스 요청이나 샘플 투자정보를 생성하지 않습니다. 좁은 화면에서는 공통 메뉴를 가로 배치하고 히트맵 아래에 추천·뉴스를 표시합니다. 이 반응형 보완은 히트맵 페이지에만 적용됩니다.

`hooks/use-heatmap.ts`는 백엔드의 갱신 시각·초기 수집 상태에 맞춰 저장된 데이터를 조회합니다. UPDATE도 KIS 수집을 강제로 실행하지 않습니다. 수동 UPDATE와 오류 시 다시 불러오기는 요청 시작부터 60초에 한 번만 허용하며, 버튼에 남은 대기시간을 표시합니다. 이 제한은 같은 브라우저 탭에서 시장·기간 변경과 새로고침에도 유지되고, 요청이 실패해도 초기화되지 않습니다. 최초 조회와 필터 변경 조회, 자동 갱신은 별도로 동작합니다. 연결 오류·부분 수집·장외·지연 상태를 표시하고 필터 변경 시 이전 요청을 취소합니다.

검증: `npm run typecheck`, `npm run build`. 관련 파일은 `components/heatmap`, `lib/api/heatmap.ts`, `lib/types/HeatmapType.ts`, `lib/heatmap-layout.ts`입니다.

This is a Next.js template with shadcn/ui.

## Adding components

To add components to your app, run the following command:

```bash
npx shadcn@latest add button
```

This will place the ui components in the `components` directory.

## Using components

To use the components in your app, import them as follows:

```tsx
import { Button } from "@/components/ui/button";
```
