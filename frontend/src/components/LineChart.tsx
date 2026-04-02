import type { TooltipItem } from "chart.js";
import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { Line } from "react-chartjs-2";
import type { Transaction } from "../types";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

interface LineChartProps {
  transactions: Transaction[];
}

export function SpendingLineChart({ transactions }: LineChartProps) {
  // Aggregate monthly spending (debits only)
  const monthlyTotals: Record<string, number> = {};
  for (const txn of transactions) {
    if (txn.amount >= 0) continue;
    const month = txn.date.slice(0, 7);
    monthlyTotals[month] = (monthlyTotals[month] ?? 0) + Math.abs(txn.amount);
  }

  const months = Object.keys(monthlyTotals).sort();
  const values = months.map((m) => Math.round(monthlyTotals[m] * 100) / 100);

  const data = {
    labels: months,
    datasets: [
      {
        label: "Total Spending",
        data: values,
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        fill: true,
        tension: 0.3,
        pointRadius: 4,
        pointBackgroundColor: "#3b82f6",
        pointBorderColor: "#ffffff",
        pointBorderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx: TooltipItem<"line">) =>
            `$${(ctx.parsed.y ?? 0).toFixed(2)}`,
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
        Spending Trend
      </h3>
      <div className="h-64">
        <Line data={data} options={options} />
      </div>
    </div>
  );
}
