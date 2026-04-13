import { useMemo } from "react";
import type { ClassifiedTransaction, Transaction } from "../types";
import { SpendingBarChart } from "./BarChart";
import { ExportButtons } from "./ExportButtons";
import { SpendingLineChart } from "./LineChart";
import { SpendingPieChart } from "./PieChart";
import { Recommendations } from "./Recommendations";
import { SpendingQuery } from "./SpendingQuery";
import { SummaryCards } from "./SummaryCards";
import { FadeIn } from "./ui/animated";

interface DashboardProps {
  transactions: Transaction[];
  classifications: ClassifiedTransaction[];
}

export function Dashboard({ transactions, classifications }: DashboardProps) {
  const classMap = useMemo(
    () => new Map(classifications.map((c) => [c.id, c])),
    [classifications]
  );

  // Category totals for pie chart
  const categoryTotals = useMemo(() => {
    const totals: Record<string, number> = {};
    for (const txn of transactions) {
      if (txn.amount >= 0) continue;
      const cat = classMap.get(txn.id)?.category ?? "Uncategorized";
      totals[cat] = (totals[cat] ?? 0) + Math.abs(txn.amount);
    }
    // Round values
    for (const key of Object.keys(totals)) {
      totals[key] = Math.round(totals[key] * 100) / 100;
    }
    return totals;
  }, [transactions, classMap]);

  // Monthly totals for recommendations
  const monthlyTotals = useMemo(() => {
    const totals: Record<string, number> = {};
    for (const txn of transactions) {
      if (txn.amount >= 0) continue;
      const month = txn.date.slice(0, 7);
      totals[month] = (totals[month] ?? 0) + Math.abs(txn.amount);
    }
    for (const key of Object.keys(totals)) {
      totals[key] = Math.round(totals[key] * 100) / 100;
    }
    return totals;
  }, [transactions]);

  return (
    <div className="mx-auto max-w-6xl">
      {/* Animation: FadeIn — dashboard header */}
      <FadeIn direction="down" duration={0.4}>
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <h2 className="text-xl font-semibold text-gray-900">
            Spending Dashboard
          </h2>
          <ExportButtons
            transactions={transactions}
            classifications={classifications}
          />
        </div>
      </FadeIn>

      {/* Summary cards — full width */}
      <div className="mb-6">
        <SummaryCards
          transactions={transactions}
          classifications={classifications}
        />
      </div>

      {/* Animation: FadeIn — charts section */}
      <FadeIn delay={0.2} duration={0.5}>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <SpendingPieChart categoryTotals={categoryTotals} />
          <SpendingBarChart
            transactions={transactions}
            classifications={classifications}
          />
          <div className="lg:col-span-2">
            <SpendingLineChart transactions={transactions} />
          </div>
        </div>
      </FadeIn>

      {/* Animation: FadeIn — AI Recommendations */}
      <FadeIn delay={0.3} duration={0.5}>
        <div className="mt-6">
          <Recommendations
            spendingByCategory={categoryTotals}
            monthlyTotals={monthlyTotals}
          />
        </div>
      </FadeIn>

      {/* Animation: FadeIn — Natural Language Query */}
      <FadeIn delay={0.4} duration={0.5}>
        <div className="mt-6">
          <h3 className="mb-3 text-lg font-semibold text-gray-900">
            Ask Penny
          </h3>
          <SpendingQuery
            transactions={transactions}
            classifications={classifications}
          />
        </div>
      </FadeIn>
    </div>
  );
}
