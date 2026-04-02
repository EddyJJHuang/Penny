import type { ClassifiedTransaction, Transaction } from "../types";

interface SummaryCardsProps {
  transactions: Transaction[];
  classifications: ClassifiedTransaction[];
}

export function SummaryCards({
  transactions,
  classifications,
}: SummaryCardsProps) {
  const classMap = new Map(classifications.map((c) => [c.id, c]));
  const debits = transactions.filter((t) => t.amount < 0);

  // Total spending
  const totalSpending = debits.reduce((s, t) => s + Math.abs(t.amount), 0);

  // Top category
  const catTotals: Record<string, number> = {};
  for (const txn of debits) {
    const cat = classMap.get(txn.id)?.category ?? "Uncategorized";
    catTotals[cat] = (catTotals[cat] ?? 0) + Math.abs(txn.amount);
  }
  const topEntry = Object.entries(catTotals).sort(([, a], [, b]) => b - a)[0];

  // Largest single transaction
  const largest = debits.length > 0
    ? debits.reduce((max, t) =>
        Math.abs(t.amount) > Math.abs(max.amount) ? t : max
      )
    : null;

  // Month-over-month change
  const monthlyTotals: Record<string, number> = {};
  for (const txn of debits) {
    const month = txn.date.slice(0, 7);
    monthlyTotals[month] = (monthlyTotals[month] ?? 0) + Math.abs(txn.amount);
  }
  const months = Object.keys(monthlyTotals).sort();
  let momChange: number | null = null;
  if (months.length >= 2) {
    const prev = monthlyTotals[months[months.length - 2]];
    const curr = monthlyTotals[months[months.length - 1]];
    if (prev > 0) {
      momChange = ((curr - prev) / prev) * 100;
    }
  }

  const cards = [
    {
      label: "Total Spent",
      value: `$${totalSpending.toFixed(2)}`,
      sub: `${debits.length} transactions`,
      color: "text-gray-900",
    },
    {
      label: "Top Category",
      value: topEntry ? topEntry[0] : "—",
      sub: topEntry ? `$${topEntry[1].toFixed(2)}` : "",
      color: "text-gray-900",
    },
    {
      label: "Largest Transaction",
      value: largest ? `$${Math.abs(largest.amount).toFixed(2)}` : "—",
      sub: largest ? largest.description : "",
      color: "text-gray-900",
    },
    {
      label: "Month-over-Month",
      value:
        momChange !== null
          ? `${momChange >= 0 ? "+" : ""}${momChange.toFixed(1)}%`
          : "—",
      sub:
        months.length >= 2
          ? `${months[months.length - 2]} → ${months[months.length - 1]}`
          : "Not enough data",
      color:
        momChange !== null
          ? momChange > 0
            ? "text-red-600"
            : momChange < 0
              ? "text-emerald-600"
              : "text-gray-900"
          : "text-gray-900",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm"
        >
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
            {card.label}
          </p>
          <p className={`mt-1 text-2xl font-bold ${card.color}`}>
            {card.value}
          </p>
          {card.sub && (
            <p className="mt-0.5 truncate text-xs text-gray-400">{card.sub}</p>
          )}
        </div>
      ))}
    </div>
  );
}
