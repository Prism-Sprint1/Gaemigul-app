import { timelineItems } from "@/lib/constant/timeline"

export default function page() {
  return (
    <div className="flex flex-col gap-6 p-6">
      {timelineItems.map((item) => (
        <section
          key={item.id}
          id={item.id}
          className="scroll-mt-6 rounded-lg border p-4"
        >
          <p className="text-sm text-neutral-500">{item.time}</p>
          <h2 className="text-lg font-semibold">{item.title}</h2>
          <p className="text-sm text-neutral-500">{item.description}</p>
        </section>
      ))}
    </div>
  )
}
