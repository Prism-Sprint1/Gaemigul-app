import type { TimelineContent } from "@/lib/types/TimelineType"

export const timelineContents: TimelineContent[] = [
  {
    id: "schedule-1",
    marketStats: [
      {
        groupLabel: "어제 마감",
        stats: [
          { label: "KOSPI", value: "2,675.90", rate: "+0.42%", isPositive: true },
          { label: "KOSDAQ", value: "862.31", rate: "-0.18%", isPositive: false },
          { label: "원/달러", value: "1,362.50", rate: "-0.35%", isPositive: false },
        ],
      },
      {
        groupLabel: "글로벌 현황",
        stats: [
          { label: "S&P500", value: "6,995.39", rate: "+4.61%", isPositive: true },
          { label: "나스닥", value: "22,141.20", rate: "-0.35%", isPositive: false },
          { label: "WTI", value: "94.31", rate: "+3.09%", isPositive: true },
        ],
      },
    ],
    llmSummary: {
      title: "유가 급등, 불안 확산",
      subtitle: "WTI 94.31달러 돌파, 인플레 우려 불붙다",
      points: [
        {
          id: "s1-p1",
          badgeLabel: "POINT 01",
          title: "유가 급등",
          description:
            "WTI가 94.31달러(+3.09%)로 상승했습니다 — 이란의 유조선 공격 소식이 유가 상승을 이끌며 인플레이션 우려가 증폭되고 있습니다.",
          accent: "red",
        },
        {
          id: "s1-p2",
          badgeLabel: "POINT 02",
          title: "금리 우려 확산",
          description:
            "유가 상승에 따라 금리 인상 우려가 커져 국내 성장주에 부정적인 영향을 미칠 가능성이 높습니다.",
          accent: "orange",
        },
        {
          id: "s1-p3",
          badgeLabel: "POINT 03",
          title: "안전자산 선호",
          description:
            "지정학적 리스크가 커지며 달러와 금 등 안전자산으로 자금이 이동하는 모습이 관측되고 있습니다.",
          accent: "green",
        },
      ],
    },
    beginnerSummary: {
      title: "오늘 왜 유가가 오르는 거예요?",
      subtitle: "유가가 오르면 물가와 금리, 안전자산까지 줄줄이 영향을 받아요",
      points: [
        {
          id: "s1-b1",
          title: "공급 불안이 유가를 밀어올려요",
          description:
            "중동에서 유조선이 공격당했다는 소식에 원유 공급이 줄어들 것이라는 걱정이 커지면서 기름값이 올랐어요.",
          tags: ["유가", "공급불안"],
        },
        {
          id: "s1-b2",
          title: "기름값이 오르면 물가도 뛰어요",
          description:
            "기름값은 거의 모든 물건의 생산·운송 비용에 영향을 줘서, 오르면 물가 상승(인플레이션) 우려로 이어져요.",
          tags: ["인플레이션", "물가"],
        },
        {
          id: "s1-b3",
          title: "물가 걱정은 금리 걱정으로 번져요",
          description:
            "물가가 오르면 금리를 더 올릴 수 있다는 걱정이 커져서, 오늘은 성장주보다 안전자산이 주목받고 있어요.",
          tags: ["금리", "안전자산"],
        },
      ],
    },
    news: [
      { id: "s1-n1", content: "[뉴욕채권] 국채가 이틀째 하락…유가 상승에 긴축 강세 되돌림", source: "NAVER" , url: "#" },
      { id: "s1-n2", content: "이란발 지정학 리스크에 국제유가 3%대 급등", source: "NAVER" , url: "#" },
      { id: "s1-n3", content: "간밤 뉴욕증시, 유가 급등에도 기술주 강세 지속", source: "NAVER" , url: "#" },
      { id: "s1-n4", content: "달러 인덱스 강세…원/달러 환율 1,360원대 등락", source: "NAVER" , url: "#" },
      { id: "s1-n5", content: "금값, 안전자산 선호에 온스당 2,400달러 돌파", source: "NAVER" , url: "#" },
      { id: "s1-n6", content: "OPEC+, 추가 감산 논의 가능성에 유가 상단 자극", source: "NAVER" , url: "#" },
    ],
  },
  {
    id: "schedule-2",
    llmSummary: {
      title: "프리마켓 특징주 부각",
      subtitle: "NXT 프리마켓, 에너지·방산주 강세",
      points: [
        {
          id: "s2-p1",
          badgeLabel: "POINT 01",
          title: "에너지株 강세",
          description: "정유·화학 관련 종목이 유가 급등 소식에 프리마켓에서 상승 흐름을 보이고 있습니다.",
          accent: "red",
        },
        {
          id: "s2-p2",
          badgeLabel: "POINT 02",
          title: "방산주 관심 집중",
          description: "지정학적 긴장 고조로 방산 관련주에 매수세가 유입되고 있습니다.",
          accent: "orange",
        },
        {
          id: "s2-p3",
          badgeLabel: "POINT 03",
          title: "성장주 약세",
          description: "금리 우려로 일부 성장주는 프리마켓에서 약보합 흐름을 나타내고 있습니다.",
          accent: "green",
        },
      ],
    },
    beginnerSummary: {
      title: "프리마켓이 뭔가요?",
      subtitle: "정규장 전 거래라 가격이 크게 흔들릴 수 있으니 참고만 해요",
      points: [
        {
          id: "s2-b1",
          title: "정규장 전에 미리 거래해요",
          description: "정규장이 열리기 전에 미리 거래할 수 있는 시장이 프리마켓이에요.",
          tags: ["프리마켓", "거래시간"],
        },
        {
          id: "s2-b2",
          title: "밤사이 뉴스가 먼저 반영돼요",
          description: "밤사이 나온 뉴스에 따라 특정 종목이 먼저 움직이는 걸 확인할 수 있어요.",
          tags: ["뉴스", "특징주"],
        },
        {
          id: "s2-b3",
          title: "거래량이 적어 변동성이 커요",
          description: "거래량이 적어 가격이 크게 흔들릴 수 있으니 주의가 필요해요.",
          tags: ["변동성", "주의"],
        },
      ],
    },
    news: [
      { id: "s2-n1", content: "프리마켓서 정유·화학주 동반 강세", source: "NAVER" , url: "#" },
      { id: "s2-n2", content: "방산 테마 프리마켓서 매수세 유입", source: "NAVER" , url: "#" },
      { id: "s2-n3", content: "간밤 이슈 정리…오늘 장초반 체크포인트는", source: "NAVER" , url: "#" },
      { id: "s2-n4", content: "외국인 프리마켓 순매수 상위 종목은", source: "NAVER" , url: "#" },
    ],
    featuredStocks: [
      { id: "s2-st1", name: "S-Oil", rate: "+4.8%", price: "78,900", badge: "상승 1위" },
      { id: "s2-st2", name: "한화에어로스페이스", rate: "+3.9%", price: "412,000", badge: "상승 2위" },
      { id: "s2-st3", name: "LG화학", rate: "+3.1%", price: "331,500", badge: "상승 3위" },
    ],
  },
  {
    id: "schedule-3",
    llmSummary: {
      title: "장초반 강세 업종 뚜렷",
      subtitle: "개장 직후 전자·반도체 업종 강세",
      points: [
        {
          id: "s3-p1",
          badgeLabel: "POINT 01",
          title: "외국인 순매수",
          description: "개장 직후 외국인 자금이 대형 반도체·전자 업종으로 유입되고 있습니다.",
          accent: "red",
        },
        {
          id: "s3-p2",
          badgeLabel: "POINT 02",
          title: "거래대금 집중",
          description: "코스피 거래대금 상위 종목이 전자제품·반도체장비 업종에 쏠려있습니다.",
          accent: "orange",
        },
        {
          id: "s3-p3",
          badgeLabel: "POINT 03",
          title: "코스닥 혼조",
          description: "코스닥은 개별 테마주 위주로 종목 장세가 이어지고 있습니다.",
          accent: "green",
        },
      ],
    },
    beginnerSummary: {
      title: "주도 섹터는 어떻게 정해지나요?",
      subtitle: "그날 가장 많은 돈이 몰리며 오른 업종을 주도 섹터라고 불러요",
      points: [
        {
          id: "s3-b1",
          title: "돈이 몰리는 곳이 주도 섹터예요",
          description: "그날 가장 많은 돈이 몰리면서 오른 업종을 '주도 섹터'라고 불러요.",
          tags: ["주도섹터", "수급"],
        },
        {
          id: "s3-b2",
          title: "오늘은 전자·반도체가 강세예요",
          description: "오늘은 전자제품과 반도체 관련 업종에 매수세가 집중되고 있어요.",
          tags: ["전자제품", "반도체"],
        },
        {
          id: "s3-b3",
          title: "주도 섹터로 시장 관심사를 읽어요",
          description: "주도 섹터를 보면 오늘 시장의 관심사가 어디에 있는지 알 수 있어요.",
          tags: ["시장관심", "테마"],
        },
      ],
    },
    news: [
      { id: "s3-n1", content: "코스피 개장 직후 반도체株 강세…외국인 순매수 지속", source: "NAVER" , url: "#" },
      { id: "s3-n2", content: "전자제품 업종, 장초반 거래대금 1위", source: "NAVER" , url: "#" },
      { id: "s3-n3", content: "코스닥, 개별 테마주 중심 종목 장세", source: "NAVER" , url: "#" },
      { id: "s3-n4", content: "장초반 수급 동향…기관은 관망세", source: "NAVER" , url: "#" },
    ],
    sectors: [
      {
        id: "s3-sec1",
        name: "전자제품",
        rate: "+3.43%",
        topStock: { name: "LG전자", badge: "상승·거래 1위", rate: "+3.4%" },
      },
      {
        id: "s3-sec2",
        name: "헨드셋",
        rate: "+3.43%",
        topStock: { name: "인탑스", badge: "상승·거래 1위", rate: "+3.4%" },
      },
      {
        id: "s3-sec3",
        name: "반도체와반도체장비",
        rate: "+3.43%",
        topStock: { name: "DB하이텍", badge: "상승 1위", rate: "+3.4%" },
      },
    ],
  },
  {
    id: "schedule-4",
    llmSummary: {
      title: "오전장 상승 폭 확대",
      subtitle: "코스피, 반도체 강세에 상승 폭 확대",
      points: [
        {
          id: "s4-p1",
          badgeLabel: "POINT 01",
          title: "지수 상승 지속",
          description: "코스피가 오전 중 상승 폭을 키우며 강세 흐름을 이어가고 있습니다.",
          accent: "red",
        },
        {
          id: "s4-p2",
          badgeLabel: "POINT 02",
          title: "2차전지 반등",
          description: "그간 부진했던 2차전지 관련주가 오전장 저가 매수세에 반등하고 있습니다.",
          accent: "orange",
        },
        {
          id: "s4-p3",
          badgeLabel: "POINT 03",
          title: "환율 안정",
          description: "원/달러 환율이 소폭 안정되며 외국인 수급에 우호적인 환경이 조성되고 있습니다.",
          accent: "green",
        },
      ],
    },
    beginnerSummary: {
      title: "오전장 흐름은 왜 중요한가요?",
      subtitle: "개장 직후 방향이 오전 내내 이어지는 경우가 많아요",
      points: [
        {
          id: "s4-b1",
          title: "개장 흐름이 오전 내내 이어져요",
          description:
            "개장 직후 방향이 오전 내내 이어지는 경우가 많아서, 오전장 흐름을 보면 하루 분위기를 짐작할 수 있어요.",
          tags: ["오전장", "추세"],
        },
        {
          id: "s4-b2",
          title: "상승세는 매수세의 신호예요",
          description: "오전 상승세가 이어지면 매수세가 힘을 받고 있다는 신호로 볼 수 있어요.",
          tags: ["매수세", "상승세"],
        },
        {
          id: "s4-b3",
          title: "환율 안정은 외국인에 우호적",
          description: "환율이 안정되면 외국인 자금이 국내 증시로 들어오기 더 편해져요.",
          tags: ["환율", "외국인수급"],
        },
      ],
    },
    news: [
      { id: "s4-n1", content: "코스피, 반도체 강세에 오전 상승 폭 확대", source: "NAVER" , url: "#" },
      { id: "s4-n2", content: "2차전지주, 저가 매수세에 반등 시도", source: "NAVER" , url: "#" },
      { id: "s4-n3", content: "원/달러 환율 소폭 안정…외국인 수급 개선", source: "NAVER" , url: "#" },
      { id: "s4-n4", content: "오전장 거래대금 상위 종목 점검", source: "NAVER" , url: "#" },
    ],
    sectors: [
      {
        id: "s4-sec1",
        name: "2차전지",
        rate: "+2.85%",
        topStock: { name: "LG에너지솔루션", badge: "상승·거래 1위", rate: "+2.9%" },
      },
      {
        id: "s4-sec2",
        name: "반도체와반도체장비",
        rate: "+2.61%",
        topStock: { name: "SK하이닉스", badge: "상승·거래 1위", rate: "+2.7%" },
      },
      {
        id: "s4-sec3",
        name: "자동차",
        rate: "+1.98%",
        topStock: { name: "현대차", badge: "상승 1위", rate: "+2.1%" },
      },
    ],
  },
  {
    id: "schedule-5",
    llmSummary: {
      title: "오후장 변동성 확대",
      subtitle: "차익 실현 매물에 상승 폭 둔화",
      points: [
        {
          id: "s5-p1",
          badgeLabel: "POINT 01",
          title: "차익 실현 매물",
          description: "오전 급등 업종을 중심으로 차익 실현 매물이 출회되며 상승 폭이 둔화됐습니다.",
          accent: "red",
        },
        {
          id: "s5-p2",
          badgeLabel: "POINT 02",
          title: "코스닥 강세 지속",
          description: "코스닥은 개별 테마주 중심으로 강세 흐름을 이어가고 있습니다.",
          accent: "orange",
        },
        {
          id: "s5-p3",
          badgeLabel: "POINT 03",
          title: "변동성 확대",
          description: "장 마감을 앞두고 프로그램 매매에 따른 변동성이 커지고 있습니다.",
          accent: "green",
        },
      ],
    },
    beginnerSummary: {
      title: "차익 실현이 뭐예요?",
      subtitle: "많이 오른 종목일수록 오후에 매도 물량이 나오기 쉬워요",
      points: [
        {
          id: "s5-b1",
          title: "오른 만큼 팔아 이익을 챙겨요",
          description: "주가가 오른 종목을 팔아서 이익을 확정 짓는 것을 '차익 실현'이라고 해요.",
          tags: ["차익실현", "매도"],
        },
        {
          id: "s5-b2",
          title: "많이 오를수록 매물도 늘어요",
          description: "오전에 많이 오른 업종일수록 오후에 차익 실현 매물이 나오기 쉬워요.",
          tags: ["업종순환", "매물"],
        },
        {
          id: "s5-b3",
          title: "마감이 가까울수록 변동성 확대",
          description: "장 마감이 가까워질수록 가격 변동이 커질 수 있어요.",
          tags: ["변동성", "장마감"],
        },
      ],
    },
    news: [
      { id: "s5-n1", content: "오전 급등 업종, 오후 차익 실현 매물 출회", source: "NAVER" , url: "#" },
      { id: "s5-n2", content: "코스닥, 테마주 중심 강세 지속", source: "NAVER" , url: "#" },
      { id: "s5-n3", content: "장 마감 앞두고 프로그램 매매 변동성 확대", source: "NAVER" , url: "#" },
      { id: "s5-n4", content: "오후장 수급 동향…기관 매도 전환", source: "NAVER" , url: "#" },
    ],
    sectors: [
      {
        id: "s5-sec1",
        name: "헬스케어",
        rate: "+2.12%",
        topStock: { name: "삼성바이오로직스", badge: "상승·거래 1위", rate: "+2.2%" },
      },
      {
        id: "s5-sec2",
        name: "전자제품",
        rate: "+1.75%",
        topStock: { name: "LG전자", badge: "상승·거래 1위", rate: "+1.8%" },
      },
      {
        id: "s5-sec3",
        name: "게임엔터",
        rate: "+1.44%",
        topStock: { name: "크래프톤", badge: "상승 1위", rate: "+1.6%" },
      },
    ],
  },
  {
    id: "schedule-6",
    marketStats: [
      {
        groupLabel: "장중 변화 (vs 07:30)",
        stats: [
          {
            label: "KOSPI",
            value: "2,689.40",
            rate: "+0.50%",
            isPositive: true,
            previousValue: "2,678.10",
          },
          {
            label: "KOSDAQ",
            value: "868.12",
            rate: "+0.67%",
            isPositive: true,
            previousValue: "863.00",
          },
          {
            label: "원/달러",
            value: "1,359.80",
            rate: "-0.20%",
            isPositive: false,
            previousValue: "1,362.50",
          },
        ],
      },
    ],
    llmSummary: {
      title: "반도체·2차전지 강세로 마감",
      subtitle: "코스피, 반도체 주도로 강보합 마감",
      points: [
        {
          id: "s6-p1",
          badgeLabel: "POINT 01",
          title: "지수 강보합 마감",
          description: "코스피가 반도체·2차전지 강세에 힘입어 강보합으로 장을 마쳤습니다.",
          accent: "red",
        },
        {
          id: "s6-p2",
          badgeLabel: "POINT 02",
          title: "외국인 순매수 전환",
          description: "외국인이 장 후반 순매수로 전환하며 지수 하단을 지지했습니다.",
          accent: "orange",
        },
        {
          id: "s6-p3",
          badgeLabel: "POINT 03",
          title: "환율 소폭 하락",
          description: "원/달러 환율이 오전 대비 소폭 하락하며 안정세를 보였습니다.",
          accent: "green",
        },
      ],
    },
    beginnerSummary: {
      title: "오늘 하루를 정리하면?",
      subtitle: "악재가 있어도 주도 업종이 강하면 지수는 오를 수 있어요",
      points: [
        {
          id: "s6-b1",
          title: "아침엔 유가 급등이 불안했어요",
          description: "아침엔 유가 급등 소식에 시장이 긴장했지만, 하루 종일 이어지진 않았어요.",
          tags: ["유가", "오전시황"],
        },
        {
          id: "s6-b2",
          title: "반도체·2차전지가 힘을 냈어요",
          description: "반도체와 2차전지 업종이 힘을 내면서 지수는 오히려 오르며 하루를 마쳤어요.",
          tags: ["반도체", "2차전지"],
        },
        {
          id: "s6-b3",
          title: "외국인 전환이 막판 반등 신호",
          description: "외국인 수급이 장 후반 순매수로 전환된 건 반등의 중요한 신호예요.",
          tags: ["외국인수급", "반등신호"],
        },
      ],
    },
    news: [
      { id: "s6-n1", content: "코스피, 반도체 주도로 강보합 마감", source: "NAVER" , url: "#" },
      { id: "s6-n2", content: "외국인, 장 후반 순매수 전환", source: "NAVER" , url: "#" },
      { id: "s6-n3", content: "원/달러 환율, 오전 대비 소폭 하락 마감", source: "NAVER" , url: "#" },
      { id: "s6-n4", content: "오늘의 마감 시황…내일 체크포인트는", source: "NAVER" , url: "#" },
    ],
    sectors: [
      {
        id: "s6-sec1",
        name: "반도체와반도체장비",
        rate: "+3.02%",
        topStock: { name: "SK하이닉스", badge: "상승·거래 1위", rate: "+3.1%" },
      },
      {
        id: "s6-sec2",
        name: "2차전지",
        rate: "+2.44%",
        topStock: { name: "LG에너지솔루션", badge: "상승·거래 1위", rate: "+2.5%" },
      },
      {
        id: "s6-sec3",
        name: "전자제품",
        rate: "+1.87%",
        topStock: { name: "LG전자", badge: "상승 1위", rate: "+1.9%" },
      },
    ],
  },
  {
    id: "schedule-7",
    llmSummary: {
      title: "시간외 단일가 특징주 부각",
      subtitle: "애프터마켓, 실적 발표 종목 변동성 확대",
      points: [
        {
          id: "s7-p1",
          badgeLabel: "POINT 01",
          title: "실적 서프라이즈",
          description: "시간외 단일가에서 어닝 서프라이즈를 기록한 종목이 급등하고 있습니다.",
          accent: "red",
        },
        {
          id: "s7-p2",
          badgeLabel: "POINT 02",
          title: "가이던스 부진",
          description: "일부 종목은 실망스러운 가이던스로 시간외에서 약세를 보이고 있습니다.",
          accent: "orange",
        },
        {
          id: "s7-p3",
          badgeLabel: "POINT 03",
          title: "내일 개장 주목",
          description: "시간외 흐름이 내일 정규장 개장가에 영향을 줄 수 있어 주목됩니다.",
          accent: "green",
        },
      ],
    },
    beginnerSummary: {
      title: "시간외 거래는 뭔가요?",
      subtitle: "실적 발표 직후엔 주가가 시간외에서 크게 움직일 수 있어요",
      points: [
        {
          id: "s7-b1",
          title: "정규장 뒤에도 잠깐 거래해요",
          description:
            "정규장이 끝난 뒤에도 정해진 가격으로 잠깐 더 거래할 수 있는 시간이 시간외 거래예요.",
          tags: ["시간외거래", "단일가"],
        },
        {
          id: "s7-b2",
          title: "실적 발표가 주가를 흔들어요",
          description: "그날 발표된 실적이나 뉴스에 따라 주가가 크게 움직일 수 있어요.",
          tags: ["실적발표", "변동성"],
        },
        {
          id: "s7-b3",
          title: "다음 날 개장가의 힌트가 돼요",
          description: "시간외 흐름은 다음 날 개장가에 힌트를 주기도 해요.",
          tags: ["개장가", "프리뷰"],
        },
      ],
    },
    news: [
      { id: "s7-n1", content: "시간외 단일가, 실적 발표 종목 급등락", source: "NAVER" , url: "#" },
      { id: "s7-n2", content: "어닝 서프라이즈 종목 시간외 상한가", source: "NAVER" , url: "#" },
      { id: "s7-n3", content: "가이던스 부진 종목, 시간외서 약세", source: "NAVER" , url: "#" },
      { id: "s7-n4", content: "내일 개장 전 체크해야 할 이슈는", source: "NAVER" , url: "#" },
    ],
    featuredStocks: [
      { id: "s7-st1", name: "한미반도체", rate: "+9.8%", price: "182,300", badge: "상승 1위" },
      { id: "s7-st2", name: "에코프로비엠", rate: "+6.2%", price: "231,000", badge: "상승 2위" },
      { id: "s7-st3", name: "카카오", rate: "+4.7%", price: "45,900", badge: "상승 3위" },
    ],
  },
  {
    id: "schedule-8",
    llmSummary: {
      title: "오늘 시장 총평",
      subtitle: "유가 충격 딛고 반도체가 지수 방어",
      points: [
        {
          id: "s8-p1",
          badgeLabel: "POINT 01",
          title: "업종 차별화 뚜렷",
          description: "유가 민감 업종은 약세, 반도체·2차전지는 강세를 보이며 업종별 온도차가 컸습니다.",
          accent: "red",
        },
        {
          id: "s8-p2",
          badgeLabel: "POINT 02",
          title: "외국인 수급 회복",
          description: "장 후반 외국인 순매수 전환이 지수 방어에 힘을 보탰습니다.",
          accent: "orange",
        },
        {
          id: "s8-p3",
          badgeLabel: "POINT 03",
          title: "내일 체크포인트",
          description: "내일은 유가 추가 변동성과 반도체 업종의 강세 지속 여부를 살펴봐야 합니다.",
          accent: "green",
        },
      ],
    },
    beginnerSummary: {
      title: "내일은 뭘 봐야 하나요?",
      subtitle: "유가 흐름과 오늘 주도 업종이 내일도 이어지는지 지켜봐요",
      points: [
        {
          id: "s8-b1",
          title: "유가가 계속 오르는지 확인해요",
          description:
            "유가 흐름은 인플레이션과 금리 우려로 이어질 수 있어서 계속 지켜볼 필요가 있어요.",
          tags: ["유가", "인플레이션"],
        },
        {
          id: "s8-b2",
          title: "오늘 주도 업종의 지속 여부",
          description: "오늘 시장을 이끈 반도체 업종의 강세가 내일도 이어지는지 확인해보세요.",
          tags: ["반도체", "주도업종"],
        },
        {
          id: "s8-b3",
          title: "외국인 수급 흐름도 체크해요",
          description: "외국인 수급이 계속 우호적으로 유지되는지도 함께 살펴보면 좋아요.",
          tags: ["외국인수급", "체크포인트"],
        },
      ],
    },
    news: [
      { id: "s8-n1", content: "[마감시황] 유가 충격 딛고 반도체가 지수 방어", source: "NAVER" , url: "#" },
      { id: "s8-n2", content: "오늘의 시장 총평…내일 체크포인트 정리", source: "NAVER" , url: "#" },
      { id: "s8-n3", content: "외국인 수급, 장 후반 순매수로 마무리", source: "NAVER" , url: "#" },
      { id: "s8-n4", content: "전문가들 \"유가 변동성 당분간 지속될 것\"", source: "NAVER" , url: "#" },
    ],
    featuredStocks: [
      { id: "s8-st1", name: "SK하이닉스", rate: "+5.4%", price: "215,000", badge: "상승 1위" },
      { id: "s8-st2", name: "LG에너지솔루션", rate: "+4.1%", price: "398,500", badge: "상승 2위" },
      { id: "s8-st3", name: "S-Oil", rate: "-2.3%", price: "75,200", badge: "하락 1위" },
    ],
  },
]
