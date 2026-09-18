# Next.js template

## 단물 지도 (히트맵)

`/heatmap`에서 KOSPI·KOSDAQ의 일간·주간·월간 히트맵을 확인합니다. 기존 메뉴 경로는 유지하고 내부 코드 이름은 `heatmap`을 사용합니다.

```powershell
npm install
npm run dev
```

`.env.local`의 `NEXT_PUBLIC_API_BASE_URL`에 백엔드 주소를 설정합니다(기본 `http://localhost:8000`). KIS 키는 프론트엔드에 설정하지 않습니다. 백엔드를 실행해야 실제 시세가 표시됩니다.

업종과 종목 면적은 시가총액의 0.35제곱을 정규화한 비중 60%와 균등 비중 40%를 합쳐 계산합니다. 시가총액 순서를 유지하면서 작은 업종·종목도 볼 수 있도록 크기 차이를 완화합니다. 업종 확대·종목 검색·키보드 선택으로 작은 종목도 확인할 수 있으며, 실제 시가총액은 상세 정보에 표시합니다. 빨강은 상승, 파랑은 하락이며 회색의 등락률 미제공과 보합은 상세 문구로 구분합니다.

표시 범위는 시세가 있는 기업 5개 이상인 업종 중 시가총액 상위 15개 업종입니다. 업종마다 시가총액 상위 기업 5개씩 총 75개를 표시하고, 데이터가 부족하면 실제 가능한 업종 수를 안내합니다. 검색·업종 확대에도 같은 표시 범위를 적용합니다. 업종 면적은 업종 전체 시가총액을 기준으로 유지합니다. 상단 1위는 선택한 시장·기간에서 전체 업종의 시가총액 가중 평균 등락률을 비교한 결과이며, 히트맵에 없는 업종도 1위가 될 수 있습니다. 모두 하락하면 등락률 1위(하락폭이 가장 작은 업종)로 안내합니다.

우측에는 1위 업종과 연결된 3개 업종의 연관 이유·등락률과 각 업종의 시가총액 상위 기업 2개를 표시합니다. 산업 연관 규칙이 부족해 시장 흐름으로 보완한 업종은 별도 표시합니다. 하단은 백엔드의 `GET /heatmap/news?market=...&period=...`를 통해 1위 업종의 최신 경제뉴스 최대 4개를 불러옵니다. Google 뉴스 RSS에서 제공되는 기사 제목·언론사·발행 시각·링크를 표시하고, 기사 부족이나 조회 오류를 샘플 기사로 대체하지 않습니다. 필터 변경 시 요청을 취소하며 다른 1위 업종의 응답은 표시하지 않습니다. 뉴스 갱신도 히트맵 조회에 연결되어 별도 수동 버튼으로 60초 제한을 우회하지 않습니다. 좁은 화면에서는 공통 메뉴를 가로 배치하고 히트맵 아래에 연관 업종·뉴스를 표시합니다. 이 반응형 보완은 히트맵 페이지에만 적용됩니다.

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

## 헤더 차트 회귀 테스트

설치 후 `npm run test:charts`로 실행합니다. 숨겨진 데스크톱/모바일 헤더에서 기존 반응형 차트가 0 × 0 크기 경고를 발생시키는 상황을 재현하고, 고정 80 × 40 크기의 지수 미니 차트는 숨김·표시 전환 후에도 경고 없이 렌더링되는지 검증합니다. 반복 티커의 SVG 그라데이션 ID도 중복되지 않는지 확인합니다.
