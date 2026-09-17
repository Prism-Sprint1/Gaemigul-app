import type {
  ReportItem,
  ReportMonth,
  ReportWeekGroup,
} from "@/lib/types/ReportType"

export const reportMonths: ReportMonth[] = [
  { id: "2026-07", label: "07월", subLabel: "JULY" },
  { id: "2026-08", label: "08월", subLabel: "AUGUST" },
  { id: "2026-09", label: "09월", subLabel: "SEPTEMBER" },
  { id: "2026-10", label: "10월", subLabel: "OCTOBER" },
]

const WEEK_ITEM_TEMPLATE: Omit<ReportItem, "id">[] = [
  {
    month: "9월",
    date: "27",
    day: "금",
    title: "[선물옵션 동시만기일]",
    description:
      "라가르드 총재 연설 및 유로존 기준금리 25bp 인하 여부라가르드 총재 연설 및 유로존 기준금리 인하 기준...",
    badgeLabel: "1 WEEK",
    isHighlighted: true,
  },
  {
    month: "9월",
    date: "27",
    day: "금",
    title: "[선물옵션 동시만기일]",
    description:
      "라가르드 총재 연설 및 유로존 기준금리 25bp 인하 여부라가르드 총재 연설 및 유로존 기준금리 인하 기준...",
    badgeLabel: "DAY",
    isHighlighted: false,
  },
  {
    month: "9월",
    date: "27",
    day: "금",
    title: "[선물옵션 동시만기일]",
    description:
      "라가르드 총재 연설 및 유로존 기준금리 25bp 인하 여부라가르드 총재 연설 및 유로존 기준금리 인하 기준...",
    badgeLabel: "DAY",
    isHighlighted: false,
  },
  {
    month: "9월",
    date: "27",
    day: "금",
    title: "[선물옵션 동시만기일]",
    description:
      "라가르드 총재 연설 및 유로존 기준금리 25bp 인하 여부라가르드 총재 연설 및 유로존 기준금리 인하 기준...",
    badgeLabel: "DAY",
    isHighlighted: false,
  },
  {
    month: "9월",
    date: "27",
    day: "금",
    title: "[선물옵션 동시만기일]",
    description:
      "라가르드 총재 연설 및 유로존 기준금리 25bp 인하 여부라가르드 총재 연설 및 유로존 기준금리 인하 기준...",
    badgeLabel: "DAY",
    isHighlighted: false,
  },
  {
    month: "9월",
    date: "27",
    day: "금",
    title: "[선물옵션 동시만기일]",
    description:
      "라가르드 총재 연설 및 유로존 기준금리 25bp 인하 여부라가르드 총재 연설 및 유로존 기준금리 인하 기준...",
    badgeLabel: "DAY",
    isHighlighted: false,
  },
]

function createWeekItems(weekId: string): ReportItem[] {
  return WEEK_ITEM_TEMPLATE.map((item, index) => ({
    ...item,
    id: `${weekId}-report-${index + 1}`,
  }))
}

export const reportWeekGroups: ReportWeekGroup[] = [
  {
    id: "week-1",
    rangeLabel: "9.01 - 9.07",
    items: createWeekItems("week-1"),
  },
  {
    id: "week-2",
    rangeLabel: "9.01 - 9.07",
    items: createWeekItems("week-2"),
  },
  {
    id: "week-3",
    rangeLabel: "9.01 - 9.07",
    items: createWeekItems("week-3"),
  },
  {
    id: "week-4",
    rangeLabel: "9.01 - 9.07",
    items: createWeekItems("week-4"),
  },
]
