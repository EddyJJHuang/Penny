import type { TooltipItem } from "chart.js";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from "chart.js";
import { Bar } from "react-chartjs-2";
import type { ClassifiedTransaction, Transaction } from "../types";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

const TOP_N = 5;

const COLORS = [
  "#10b981",
  "#f59e0b",
  "#3b82f6",
  "#ec4899",
  "#8b5cf6",
];

interface BarChartProps {
  transactions: Transaction[];
  classifications: ClassifiedTransaction[];
}

export function SpendingBarChart({
  transactions,
  classifications,
}: BarChartProps) {
  const classMap = new Map(classifications.map((c) => [c.id, c]));

  // Build { month → { category → total } }
  const monthCat: Record<string, Record<string, number>> = {};
  const catTotals: Record<string, number> = {};

  for (const txn of transactions) {
    if (txn.amount >= 0) continue;
    const cat = classMap.get(txn.id)?.category ?? "Uncategorized";
    const month = txn.date.slice(0, 7);
    monthCat[month] = monthCat[month] ?? {};
    monthCat[month][cat] = (monthCat[month][cat] ?? 0) + Math.abs(txn.amount);
    catTotals[cat] = (catTotals[cat] ?? 0) + Math.abs(txn.amount);
  }

  const topCategories = Object.entries(catTotals)
    .sort(([, a], [, b]) => b - a)
    .slice(0, TOP_N)
    .map(([cat]) => cat);

  const months = Object.keys(monthCat).sort();

  const datasets = topCategories.map((cat, i) => ({
    label: cat,
    data: months.map((m) => Math.round((monthCat[m]?.[cat] ?? 0) * 100) / 100),
    backgroundColor: COLORS[i % COLORS.length],
    borderRadius: 3,
  }));

  const data = { labels: months, datasets };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top" as const,
        labels: { boxWidth: 12, padding: 10, font: { size: 11 } },
      },
      tooltip: {
        callbacks: {
          label: (ctx: TooltipItem<"bar">) =>
            `${ctx.dataset.label ?? ""}: $${(ctx.parsed.y ?? 0).toFixed(2)}`,
        },
      },
    },
    scales: {
      x: { grid: { display: false } },
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value: string | number) => `$${value}`,
        },
      },
    },
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-700">
        Monthly Spending by Category (Top {TOP_N})
      </h3>
      <div className="h-64">
        <Bar data={data} options={options} />
      </div>
    </div>
  );
}
