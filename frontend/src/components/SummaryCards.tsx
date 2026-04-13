import type { ClassifiedTransaction, Transaction } from "../types";
import { CountUp, SpotlightCard, StaggerContainer } from "./ui/animated";

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

  const momColor =
    momChange !== null
      ? momChange > 0
        ? "text-red-600"
        : momChange < 0
          ? "text-emerald-600"
          : "text-gray-900"
      : "text-gray-900";

  return (
    // Animation: StaggerContainer — staggered card entrance
    <StaggerContainer
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
      staggerDelay={0.1}
      direction="up"
      distance={20}
    >
      {/* Animation: SpotlightCard — mouse-tracking spotlight on each card */}
      <SpotlightCard className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
          Total Spent
        </p>
        <p className="mt-1 text-2xl font-bold text-gray-900">
          {/* Animation: CountUp — animated number counting */}
          <CountUp to={totalSpending} prefix="$" decimals={2} duration={1.5} />
        </p>
        <p className="mt-0.5 truncate text-xs text-gray-400">
          {debits.length} transactions
        </p>
      </SpotlightCard>

      <SpotlightCard className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
          Top Category
        </p>
        <p className="mt-1 text-2xl font-bold text-gray-900">
          {topEntry ? topEntry[0] : "—"}
        </p>
        {topEntry && (
          <p className="mt-0.5 truncate text-xs text-gray-400">
            <CountUp to={topEntry[1]} prefix="$" decimals={2} duration={1.5} />
          </p>
        )}
      </SpotlightCard>

      <SpotlightCard className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
          Largest Transaction
        </p>
        <p className="mt-1 text-2xl font-bold text-gray-900">
          {largest ? (
            <CountUp to={Math.abs(largest.amount)} prefix="$" decimals={2} duration={1.5} />
          ) : (
            "—"
          )}
        </p>
        {largest && (
          <p className="mt-0.5 truncate text-xs text-gray-400">
            {largest.description}
          </p>
        )}
      </SpotlightCard>

      <SpotlightCard className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
        <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
          Month-over-Month
        </p>
        <p className={`mt-1 text-2xl font-bold ${momColor}`}>
          {momChange !== null ? (
            <>
              {momChange >= 0 ? "+" : ""}
              <CountUp to={Math.abs(momChange)} prefix={momChange < 0 ? "-" : ""} suffix="%" decimals={1} duration={1.5} />
            </>
          ) : (
            "—"
          )}
        </p>
        <p className="mt-0.5 truncate text-xs text-gray-400">
          {months.length >= 2
            ? `${months[months.length - 2]} → ${months[months.length - 1]}`
            : "Not enough data"}
        </p>
      </SpotlightCard>
    </StaggerContainer>
  );
}
