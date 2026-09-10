import type { CalendarEvent } from "@/components/ui/full-calendar"

/* 뉴스 데이터 — TODO: API 연동 시 NEWS 배열만 교체 */

export type Category = "macro" | "earnings" | "ipo" | "dividend"

export type NewsItem = {
  id: string // 뉴스 항목을 구분하는 고유 식별자
  title: string // 뉴스 제목
  summary: string // 뉴스 목록과 상세 팝업에 표시할 요약 내용
  category: Category // 뉴스 분류 및 색상 스타일을 결정하는 카테고리
  region: string // 관련 국가, 지역 또는 기업명
  publishedAt: Date // 뉴스 발표 일시 및 캘린더에 표시할 날짜
  // highlight?: 'focus' | 'special' // 날짜 그룹 배지
  url?: string // 원문 기사로 이동할 때 사용하는 선택적 URL
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
    label: string // 화면에 표시할 카테고리 이름
    dot: string // 카테고리 표시 점의 Tailwind 배경색 클래스
    text: string // 카테고리 텍스트의 Tailwind 글자색 클래스
    card: string // 뉴스 카드의 왼쪽 테두리와 배경색 클래스
    /** 왼쪽 캘린더 색 점(variant 이름) */
    event: "red" | "green" | "blue" | "amber" // 캘린더 이벤트 점의 색상 variant
  }
> = {
  macro: { label: '매크로/금리', dot: 'bg-red-500', text: 'text-red-500', card: 'border-l-red-500 bg-red-500/[0.07]', event: 'red' }, // prettier-ignore
  earnings: { label: '기업 실적', dot: 'bg-emerald-500', text: 'text-emerald-600', card: 'border-l-emerald-500 bg-emerald-500/[0.07]', event: 'green' }, // prettier-ignore
  ipo: { label: '공모주/보호예수', dot: 'bg-blue-500', text: 'text-blue-600', card: 'border-l-blue-500 bg-blue-500/[0.07]', event: 'blue' }, // prettier-ignore
  dividend: { label: '배당/옵션만기', dot: 'bg-amber-500', text: 'text-amber-600', card: 'border-l-amber-500 bg-amber-500/[0.07]', event: 'amber' }, // prettier-ignore
}

export const CATS = Object.keys(CAT) as Category[]

/* 임의 샘플 데이터 — 2026-08-25 ~ 2026-10-31 (약 두 달치) */
export const NEWS: NewsItem[] = [
  // ── 2026년 8월 ──
  { id: 'n7', title: '미국 8월 CB 소비자신뢰지수', summary: '고용·소득 기대가 반영되는 소비 심리 지표. 위축 시 소비재 전반에 부담.', category: 'macro', region: '미국', publishedAt: new Date('2026-08-25T23:00:00'), detail: { forecast: '98.5', previous: '100.3', source: '콘퍼런스보드' } }, // prettier-ignore
  { id: 'n8', title: '엔비디아 2분기 실적 발표', summary: 'AI 가속기 수요와 데이터센터 매출 가이던스가 관전 포인트.', category: 'earnings', region: '엔비디아', publishedAt: new Date('2026-08-27T06:00:00'), detail: { forecast: 'EPS 1.24달러', previous: 'EPS 0.68달러', source: 'NVIDIA IR', sectors: ['반도체', 'HBM', 'AI 인프라'] } }, // prettier-ignore
  { id: 'n9', title: '미국 2분기 GDP 성장률 수정치', summary: '속보치 대비 상·하향 여부로 연착륙 시나리오 재평가.', category: 'macro', region: '미국', publishedAt: new Date('2026-08-28T21:30:00'), detail: { forecast: '2.4%', previous: '2.1%', source: '미국 상무부 BEA' } }, // prettier-ignore
  { id: 'n10', title: '미국 7월 PCE 물가지수', summary: '연준이 선호하는 물가 지표. 근원 PCE 흐름이 금리 경로를 좌우.', category: 'macro', region: '미국', publishedAt: new Date('2026-08-29T21:30:00'), detail: { forecast: '전년비 2.6%', previous: '2.5%', source: '미국 상무부 BEA', sectors: ['국채', '성장주'] } }, // prettier-ignore
  { id: 'n11', title: '중국 8월 제조업 PMI', summary: '경기 부양책 효과 확인. 50 상회 시 소재·산업재 반등 기대.', category: 'macro', region: '중국', publishedAt: new Date('2026-08-31T10:00:00'), detail: { forecast: '49.8', previous: '49.4', source: '중국 국가통계국' } }, // prettier-ignore

  // ── 2026년 9월 ──
  { id: 'n12', title: '한국 8월 수출입동향', summary: '반도체·자동차 수출 증감률이 코스피 이익 전망의 선행 지표.', category: 'macro', region: '한국', publishedAt: new Date('2026-09-01T09:00:00'), detail: { forecast: '수출 +7%', previous: '+5.9%', source: '산업통상자원부', sectors: ['반도체', '자동차', '2차전지'] } }, // prettier-ignore
  { id: 'n13', title: '미국 8월 ISM 제조업지수', summary: '신규주문·고용 세부 항목까지 확인. 위축 국면 지속 여부가 관건.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-02T23:00:00'), detail: { forecast: '48.6', previous: '48.0', source: 'ISM' } }, // prettier-ignore
  { id: 'n14', title: '연준 베이지북 공개', summary: '12개 지역 연은의 체감 경기 보고. FOMC 전 정성적 판단 근거.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-03T03:00:00') }, // prettier-ignore
  { id: 'n15', title: '삼성전자 파운드리 포럼', summary: '2nm 양산 로드맵·수주 현황 발표 예정. 소부장 밸류체인 주목.', category: 'earnings', region: '삼성전자', publishedAt: new Date('2026-09-04T10:00:00'), detail: { source: '삼성전자', sectors: ['파운드리', '반도체 장비', '소재'] } }, // prettier-ignore
  { id: 'n16', title: '미국 8월 고용보고서(비농업)', summary: '이달 최대 이벤트. 임금상승률과 실업률 조합이 9월 FOMC 결정에 직결.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-05T21:30:00'), detail: { forecast: '비농업 +15.5만', previous: '+11.4만', source: '미국 노동부 BLS', sectors: ['국채', '금융', '성장주'] } }, // prettier-ignore
  { id: 'n1', title: '8월 NFIB 중소기업 경기 낙관지수', summary: '미국 고용의 50% 이상을 차지하는 중소기업 경기 체감지표입니다. 예상치(91.2)를 상회할 경우 연착륙(Soft Landing)에 힘이 실리며 리테일 및 소비재 종목이 탄력을 받을 수 있습니다.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-07T22:30:00'), detail: { forecast: '91.2', previous: '90.3', source: '미국소상공인연맹', sectors: ['필수소비재', '소매유통(XRT)', '소형주(러셀 2000)'] } }, // prettier-ignore
  { id: 'n2', title: 'ECB 통화정책회의 사전 브리핑', summary: '라가르드 총재 연설 전 물가 코멘트 점검.', category: 'dividend', region: '유로존', publishedAt: new Date('2026-09-07T17:00:00')}, // prettier-ignore
  { id: 'n3', title: '미국 1년 기대인플레이션율 조사', summary: '뉴욕연은 소비자기대 서베이. 단기 물가 기대 흐름 확인.', category: 'macro', region: '뉴욕연은', publishedAt: new Date('2026-09-07T23:00:00')}, // prettier-ignore
  { id: 'n4', title: '국내 신규 상장 공모주 상장일', summary: '공모가 대비 시초가 변동성 주의.', category: 'ipo', region: '공모주', publishedAt: new Date('2026-09-08T09:00:00')}, // prettier-ignore
  { id: 'n5', title: '미국 8월 무역수지 발표', summary: '수출입 증감과 달러 흐름 연동 여부 점검.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-08T21:30:00')}, // prettier-ignore
  { id: 'n6', title: '아이폰 및 신규 3nm 인공지능 프로세서 공개', summary: '국내 반도체/디스플레이 밸류체인 수혜 점검.', category: 'ipo', region: '애플', publishedAt: new Date('2026-09-09T02:00:00') }, // prettier-ignore
  { id: 'n17', title: '미국 8월 생산자물가(PPI)', summary: 'CPI 하루 전 발표되는 물가 선행 지표. 근원 PPI가 서프라이즈 시 국채 변동성 확대.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-10T21:30:00'), detail: { forecast: '전년비 2.8%', previous: '2.6%', source: '미국 노동부 BLS' } }, // prettier-ignore
  { id: 'n18', title: '미국 8월 소비자물가(CPI)', summary: '9월 FOMC 직전 마지막 물가 확인. 근원 CPI 3% 안착 여부가 인하 폭 결정.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-11T21:30:00'), detail: { forecast: '전년비 2.9%', previous: '2.7%', source: '미국 노동부 BLS', sectors: ['국채', '리츠', '기술주'] } }, // prettier-ignore
  { id: 'n19', title: 'ECB 기준금리 결정', summary: '예금금리 동결 유력. 라가르드 회견에서 추가 인하 시점 힌트 주목.', category: 'dividend', region: '유로존', publishedAt: new Date('2026-09-11T21:15:00'), detail: { forecast: '동결(예금 2.00%)', previous: '2.00%', source: 'ECB' } }, // prettier-ignore
  { id: 'n20', title: '9월 선물·옵션 동시만기일(쿼드러플위칭)', summary: '분기 마지막 동시만기. 프로그램 매물·베이시스 청산으로 장중 변동성 확대.', category: 'dividend', region: '한국', publishedAt: new Date('2026-09-11T15:20:00') }, // prettier-ignore
  { id: 'n21', title: '미국 9월 미시간대 소비자심리지수 예비치', summary: '기대인플레이션 항목이 연준 위원 발언에 자주 인용됨.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-12T23:00:00'), detail: { forecast: '68.5', previous: '67.8', source: '미시간대' } }, // prettier-ignore
  { id: 'n22', title: '중국 8월 산업생산·소매판매', summary: '소비 회복 속도 확인. 부진 시 중국 소비 노출 기업에 부담.', category: 'macro', region: '중국', publishedAt: new Date('2026-09-15T11:00:00'), detail: { forecast: '소매판매 +3.5%', previous: '+2.7%', source: '중국 국가통계국' } }, // prettier-ignore
  { id: 'n23', title: '미국 8월 소매판매', summary: '컨트롤그룹(GDP 반영분) 흐름이 3분기 성장률 추정치를 좌우.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-16T21:30:00'), detail: { forecast: '전월비 +0.3%', previous: '+0.5%', source: '미국 상무부' } }, // prettier-ignore
  { id: 'n24', title: 'FOMC 기준금리 결정', summary: '25bp 인하 여부와 점도표(연내 추가 인하 횟수)가 핵심. 시장 컨센서스는 인하.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-17T03:00:00'), detail: { forecast: '25bp 인하', previous: '동결', source: '미국 연준(FOMC)', sectors: ['성장주', '리츠', '중소형주', '금'] } }, // prettier-ignore
  { id: 'n25', title: '파월 의장 기자회견', summary: '성명서 문구 변화와 함께 향후 인하 경로에 대한 톤이 자산시장 방향 결정.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-17T03:30:00') }, // prettier-ignore
  { id: 'n26', title: '일본은행(BOJ) 금융정책결정회의', summary: '추가 금리 인상 시점 관련 코멘트. 엔화·닛케이·수출주에 영향.', category: 'dividend', region: '일본', publishedAt: new Date('2026-09-19T08:00:00'), detail: { forecast: '동결', previous: '동결', source: 'BOJ' } }, // prettier-ignore
  { id: 'n27', title: 'OO바이오 공모주 청약 시작', summary: '기관 수요예측 경쟁률 상단 확정. 청약 증거금·환불일 일정 체크.', category: 'ipo', region: '공모주', publishedAt: new Date('2026-09-21T10:00:00') }, // prettier-ignore
  { id: 'n28', title: '9월 분기 배당락일', summary: '분기 배당 실시 종목의 배당락 반영. 고배당·금융주 수급 변동.', category: 'dividend', region: '한국', publishedAt: new Date('2026-09-22T09:00:00'), detail: { sectors: ['은행', '증권', '통신', '고배당'] } }, // prettier-ignore
  { id: 'n29', title: '삼성전자·SK하이닉스 메모리 가격 협상', summary: '4분기 DRAM·NAND 고정거래가격 방향성. AI 서버향 HBM 수요가 변수.', category: 'earnings', region: '한국', publishedAt: new Date('2026-09-24T10:00:00'), detail: { sectors: ['메모리 반도체', 'HBM', '반도체 소재'] } }, // prettier-ignore
  { id: 'n30', title: '미국 2분기 GDP 확정치', summary: '기업이익(세후) 항목까지 공개. 마진 추세 확인.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-25T21:30:00'), detail: { forecast: '2.4%', previous: '2.4%', source: '미국 상무부 BEA' } }, // prettier-ignore
  { id: 'n31', title: '미국 8월 PCE 물가지수', summary: '9월 FOMC 이후 첫 물가 확인. 인하 사이클 지속 명분 점검.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-26T21:30:00'), detail: { forecast: '전년비 2.5%', previous: '2.6%', source: '미국 상무부 BEA' } }, // prettier-ignore
  { id: 'n32', title: '한국 8월 산업활동동향', summary: '생산·소비·투자 3대 지표 동시 발표. 경기 저점 통과 여부 판단.', category: 'macro', region: '한국', publishedAt: new Date('2026-09-30T08:00:00'), detail: { source: '통계청' } }, // prettier-ignore
  { id: 'n33', title: '미국 9월 CB 소비자신뢰지수', summary: '고용 체감(현재 상황 지수)이 둔화되는지 확인.', category: 'macro', region: '미국', publishedAt: new Date('2026-09-30T23:00:00'), detail: { forecast: '99.0', previous: '98.5', source: '콘퍼런스보드' } }, // prettier-ignore

  // ── 2026년 10월 ──
  { id: 'n34', title: '미국 9월 ISM 제조업지수', summary: '분기 첫 경기 지표. 50 회복 시 경기민감주 순환매 재개 기대.', category: 'macro', region: '미국', publishedAt: new Date('2026-10-01T23:00:00'), detail: { forecast: '49.2', previous: '48.6', source: 'ISM' } }, // prettier-ignore
  { id: 'n35', title: '미국 9월 고용보고서(비농업)', summary: '9월 인하 이후 노동시장 냉각 속도 확인. 임금 상승률이 관건.', category: 'macro', region: '미국', publishedAt: new Date('2026-10-02T21:30:00'), detail: { forecast: '비농업 +12.0만', previous: '+15.5만', source: '미국 노동부 BLS', sectors: ['국채', '금융', '경기소비재'] } }, // prettier-ignore
  { id: 'n36', title: '미국 9월 ISM 서비스업지수', summary: '미국 경제의 70%를 차지하는 서비스업 체감. 물가(가격) 항목 병행 확인.', category: 'macro', region: '미국', publishedAt: new Date('2026-10-05T23:00:00'), detail: { forecast: '52.0', previous: '51.4', source: 'ISM' } }, // prettier-ignore
  { id: 'n37', title: '한국 9월 수출입동향(잠정)', summary: '3분기 수출 마감치. 반도체 단가·물량 기여도 분해.', category: 'macro', region: '한국', publishedAt: new Date('2026-10-07T09:00:00'), detail: { forecast: '수출 +8%', previous: '+7%', source: '산업통상자원부', sectors: ['반도체', '자동차', '조선'] } }, // prettier-ignore
  { id: 'n38', title: 'FOMC 의사록 공개(9월 회의)', summary: '점도표 뒤 위원별 견해차·양적긴축 관련 논의 확인.', category: 'macro', region: '미국', publishedAt: new Date('2026-10-08T03:00:00') }, // prettier-ignore
  { id: 'n39', title: '미국 9월 소비자물가(CPI)', summary: '4분기 첫 물가. 3% 아래 안착 시 추가 인하 기대가 강화.', category: 'macro', region: '미국', publishedAt: new Date('2026-10-10T21:30:00'), detail: { forecast: '전년비 2.8%', previous: '2.9%', source: '미국 노동부 BLS', sectors: ['국채', '기술주', '리츠'] } }, // prettier-ignore
  { id: 'n40', title: '삼성전자 3분기 잠정 실적', summary: '메모리 업황 반등 폭과 파운드리 적자 축소 여부가 관전 포인트.', category: 'earnings', region: '삼성전자', publishedAt: new Date('2026-10-11T08:00:00'), detail: { forecast: '영업이익 12조원', previous: '10.4조원', source: '삼성전자', sectors: ['메모리', 'HBM', '파운드리'] } }, // prettier-ignore
  { id: 'n41', title: '미 채권시장 휴장(콜럼버스 데이)', summary: '주식시장은 정상 개장하나 거래량 감소. 국채 금리 갭 주의.', category: 'dividend', region: '미국', publishedAt: new Date('2026-10-12T09:00:00') }, // prettier-ignore
  { id: 'n42', title: '미국 은행 3분기 실적 시작(JP모건·씨티)', summary: '순이자마진(NIM)·대손충당금 추이로 경기·신용 사이클 진단.', category: 'earnings', region: '미국', publishedAt: new Date('2026-10-14T20:00:00'), detail: { source: '각 사 IR', sectors: ['은행', '증권', '보험'] } }, // prettier-ignore
  { id: 'n43', title: '미국 9월 소매판매', summary: '연말 쇼핑시즌 진입 전 소비 모멘텀 점검.', category: 'macro', region: '미국', publishedAt: new Date('2026-10-16T21:30:00'), detail: { forecast: '전월비 +0.4%', previous: '+0.3%', source: '미국 상무부' } }, // prettier-ignore
  { id: 'n44', title: '중국 3분기 GDP', summary: '연간 성장 목표(약 5%) 달성 가능성 평가. 부양책 추가 여부와 연결.', category: 'macro', region: '중국', publishedAt: new Date('2026-10-19T11:00:00'), detail: { forecast: '전년비 4.7%', previous: '4.9%', source: '중국 국가통계국', sectors: ['소재', '기계', '중국 소비'] } }, // prettier-ignore
  { id: 'n45', title: '테슬라 3분기 실적', summary: '인도량·자동차 총마진(GPM)과 로보택시/에너지 부문 코멘트.', category: 'earnings', region: '테슬라', publishedAt: new Date('2026-10-22T06:00:00'), detail: { forecast: 'EPS 0.58달러', previous: 'EPS 0.52달러', source: 'Tesla IR', sectors: ['2차전지', '전기차 부품', '자율주행'] } }, // prettier-ignore
  { id: 'n46', title: '한국은행 10월 금융통화위원회', summary: '기준금리 결정과 수정 경제전망. 원화·건설·가계부채가 변수.', category: 'dividend', region: '한국', publishedAt: new Date('2026-10-23T10:00:00'), detail: { forecast: '동결(2.50%)', previous: '2.50%', source: '한국은행', sectors: ['은행', '건설', '리츠'] } }, // prettier-ignore
  { id: 'n47', title: 'OO테크 코스닥 신규 상장', summary: '수요예측 흥행 종목. 상장 첫날 유통물량·의무보유 확약 비율 확인.', category: 'ipo', region: '공모주', publishedAt: new Date('2026-10-27T09:00:00') }, // prettier-ignore
  { id: 'n48', title: '마이크로소프트·알파벳 3분기 실적', summary: '클라우드(Azure·GCP) 성장률과 AI 투자(CapEx) 가이던스가 빅테크 방향 결정.', category: 'earnings', region: '미국', publishedAt: new Date('2026-10-28T22:00:00'), detail: { source: '각 사 IR', sectors: ['클라우드', 'AI 반도체', '데이터센터'] } }, // prettier-ignore
  { id: 'n49', title: 'FOMC 기준금리 결정(10월)', summary: '연속 인하 여부와 12월 회의 대비 포워드 가이던스가 핵심.', category: 'macro', region: '미국', publishedAt: new Date('2026-10-29T03:00:00'), detail: { forecast: '25bp 인하', previous: '25bp 인하', source: '미국 연준(FOMC)', sectors: ['성장주', '중소형주', '리츠'] } }, // prettier-ignore
  { id: 'n50', title: '애플·아마존 3분기 실적', summary: '아이폰 신제품 초기 수요와 아마존 AWS·리테일 마진 동시 확인.', category: 'earnings', region: '미국', publishedAt: new Date('2026-10-29T06:00:00'), detail: { source: '각 사 IR', sectors: ['IT 하드웨어', '전자부품', '이커머스'] } }, // prettier-ignore
  { id: 'n51', title: '미국 3분기 GDP 속보치', summary: '소비·투자 기여도 분해로 4분기 경기 눈높이 조정.', category: 'macro', region: '미국', publishedAt: new Date('2026-10-30T21:30:00'), detail: { forecast: '2.2%', previous: '2.4%', source: '미국 상무부 BEA' } }, // prettier-ignore
  { id: 'n52', title: '미국 9월 PCE 물가지수', summary: '10월 FOMC 직후 물가 확인. 디스인플레이션 추세 지속 여부.', category: 'macro', region: '미국', publishedAt: new Date('2026-10-31T21:30:00'), detail: { forecast: '전년비 2.4%', previous: '2.5%', source: '미국 상무부 BEA' } }, // prettier-ignore
  { id: 'n53', title: '10월 결산법인 배당 기준일', summary: '10월 결산 종목의 배당받을 권리 확정일. 익일 배당락.', category: 'dividend', region: '한국', publishedAt: new Date('2026-10-31T09:00:00') }, // prettier-ignore
]

/** 국내 증시(KRX) 휴장일 — 달력에서 연보라색으로 표시 (2026년 기준) */
export const MARKET_HOLIDAYS: Date[] = [
  '2026-01-01', // 신정
  '2026-02-16', // 설날 연휴
  '2026-02-17', // 설날
  '2026-02-18', // 설날 연휴
  '2026-03-02', // 삼일절 대체공휴일
  '2026-05-01', // 근로자의 날(증시 휴장)
  '2026-05-05', // 어린이날
  '2026-05-25', // 부처님오신날 대체공휴일
  '2026-06-03', // 제9회 전국동시지방선거
  '2026-06-08', // 현충일 대체공휴일
  '2026-08-17', // 광복절 대체공휴일
  '2026-09-24', // 추석 연휴
  '2026-09-25', // 추석
  '2026-09-28', // 추석 대체공휴일
  '2026-10-05', // 개천절 대체공휴일
  '2026-10-09', // 한글날
  '2026-12-25', // 성탄절
  '2026-12-31', // 연말 휴장일
].map((d) => new Date(`${d}T00:00:00`))

/** NEWS → 왼쪽 캘린더 이벤트(색 점 표시용, 제목은 표시 안 함) */
export const NEWS_EVENTS: CalendarEvent[] = NEWS.map((n) => ({
  id: n.id,
  start: n.publishedAt,
  end: n.publishedAt,
  title: n.title,
  color: CAT[n.category].event,
}))
