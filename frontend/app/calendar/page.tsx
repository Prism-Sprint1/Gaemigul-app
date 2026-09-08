import {
  Calendar,
  CalendarMonthView,
} from '@/components/ui/full-calendar';

export default function CalendarPage() {
  return (
      <Calendar
        events={[
          {
            id: '1',
            start: new Date('2026-09-08T09:30:00Z'),
            end: new Date('2026-09-08T14:30:00Z'),
            title: 'Meeting with John',
            color: 'pink',
          },
          {
            id: '2',
            start: new Date('2026-09-26T10:00:00Z'),
            end: new Date('2024-09-26T10:30:00Z'),
            title: 'Project Review',
            color: 'blue',
          },
        ]}
      >
        <CalendarMonthView />
      </Calendar>
  )
}
