import {
  ArcElement,
  Chart as ChartJS,
  Legend,
  Tooltip,
} from "chart.js";
import { Pie } from "react-chartjs-2";

ChartJS.register(ArcElement, Tooltip, Legend);

const CATEGORY_COLORS: Record<string, string> = {
  "Groceries": "#10b981",
  "Dining Out": "#f59e0b",
  "Transportation": "#3b82f6",
  "Gas & Auto": "#6366f1",
  "Shopping": "#ec4899",
  "Entertainment": "#8b5cf6",
  "Subscriptions": "#14b8a6",
  "Utilities": "#64748b",
  "Health & Pharmacy": "#ef4444",
  "Housing": "#f97316",
  "Education": "#06b6d4",
  "Travel": "#a855f7",
  "Income / Refund": "#22c55e",
  "Credit Card Payment": "#0ea5e9",
  "Uncategorized": "#9ca3af",
};

interface PieChartProps {
  categoryTotals: Record<string, number>;
}

export function SpendingPieChart({ categoryTotals }: PieChartProps) {
  const sorted = Object.entries(categoryTotals).sort(([, a], [, b]) => b - a);
  const labels = sorted.map(([cat]) => cat);
  const values = sorted.map(([, val]) => val);
  const total = values.reduce((s, v) => s + v, 0);

  const data = {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor: labels.map(
          (cat) => CATEGORY_COLORS[cat] ?? "#9ca3af"
        ),
        borderWidth: 2,
        borderColor: "#ffffff",
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "right" as const,
        labels: {
          boxWidth: 12,
          padding: 12,
          font: { size: 11 },
          generateLabels: (chart: ChartJS) => {
            const dataset = chart.data.datasets[0];
            return (chart.data.labels as string[]).map((label, i) => {
              const value = (dataset.data as number[])[i];
              const pct = total > 0 ? ((value / total) * 100).toFixed(1) : "0";
              return {
                text: `${label}  ${pct}%`,
                fillStyle: (dataset.backgroundColor as string[])[i],
                strokeStyle: "#ffffff",
                lineWidth: 1,
                index: i,
              };
            });
          },
        },
      },
      tooltip: {
        callbacks: {
          label: (ctx: { label: string; parsed: number }) => {
            const pct =
              total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : "0";
            return `${ctx.label}: $${ctx.parsed.toFixed(2)} (${pct}%)`;
          },
        },
      },
    },
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-gray-700">
        Spending by Category
      </h3>
      <div className="h-64">
        <Pie data={data} options={options} />
      </div>
    </div>
  );
}
