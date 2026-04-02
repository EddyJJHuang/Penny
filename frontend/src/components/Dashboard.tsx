import type { ClassifiedTransaction, Transaction } from "../types";

interface DashboardProps {
  transactions: Transaction[];
  classifications: ClassifiedTransaction[];
}

export function Dashboard({ transactions, classifications }: DashboardProps) {
  const totalSpending = transactions
    .filter((t) => t.amount < 0)
    .reduce((sum, t) => sum + Math.abs(t.amount), 0);

  const categoryTotals: Record<string, number> = {};
  for (const txn of transactions) {
    if (txn.amount >= 0) continue;
    const classified = classifications.find((c) => c.id === txn.id);
    const category = classified?.category ?? "Uncategorized";
    categoryTotals[category] = (categoryTotals[category] ?? 0) + Math.abs(txn.amount);
  }

  const topCategory = Object.entries(categoryTotals).sort(
    ([, a], [, b]) => b - a
  )[0];

  return (
    <div className="mx-auto max-w-5xl">
      <h2 className="mb-6 text-xl font-semibold text-gray-900">
        Spending Dashboard
      </h2>

      {/* Summary cards */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg bg-white p-5 shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Total Spending</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">
            ${totalSpending.toFixed(2)}
          </p>
        </div>
        <div className="rounded-lg bg-white p-5 shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Transactions</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">
            {transactions.length}
          </p>
        </div>
        <div className="rounded-lg bg-white p-5 shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Top Category</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">
            {topCategory ? topCategory[0] : "—"}
          </p>
          {topCategory && (
            <p className="text-sm text-gray-400">
              ${topCategory[1].toFixed(2)}
            </p>
          )}
        </div>
      </div>

      {/* Placeholder for charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-gray-300 bg-white text-sm text-gray-400">
          Pie Chart — coming soon
        </div>
        <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-gray-300 bg-white text-sm text-gray-400">
          Bar Chart — coming soon
        </div>
        <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-gray-300 bg-white text-sm text-gray-400 lg:col-span-2">
          Line Chart — coming soon
        </div>
      </div>

      {/* Placeholder for recommendations */}
      <div className="mt-8 rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center text-sm text-gray-400">
        AI Recommendations — coming soon
      </div>
    </div>
  );
}
