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

/** Return the ISO week label "YYYY-Www" for a date string "YYYY-MM-DD". */
function isoWeekLabel(dateStr: string): string {
  const d = new Date(dateStr + "T12:00:00");
  const thursday = new Date(d);
  thursday.setDate(d.getDate() - ((d.getDay() + 6) % 7) + 3);
  const year = thursday.getFullYear();
  const jan4 = new Date(year, 0, 4);
  const week = Math.ceil(
    ((thursday.getTime() - jan4.getTime()) / 86400000 + ((jan4.getDay() + 6) % 7) + 1) / 7
  );
  return `${year}-W${String(week).padStart(2, "0")}`;
}

export function SpendingLineChart({ transactions }: LineChartProps) {
  const debits = transactions.filter((t) => t.amount < 0);

  // Determine granularity: weekly if ≤3 distinct months, otherwise monthly
  const distinctMonths = new Set(debits.map((t) => t.date.slice(0, 7))).size;
  const useWeekly = distinctMonths <= 3;

  const buckets: Record<string, number> = {};
  for (const txn of debits) {
    const key = useWeekly ? isoWeekLabel(txn.date) : txn.date.slice(0, 7);
    buckets[key] = (buckets[key] ?? 0) + Math.abs(txn.amount);
  }

  const months = Object.keys(buckets).sort();
  const values = months.map((m) => Math.round(buckets[m] * 100) / 100);

  // Format x-axis labels to be human-readable
  const labels = months.map((key) => {
    if (useWeekly) {
      // "2026-W05" → "Feb W5"
      const [yr, wPart] = key.split("-W");
      const weekNum = parseInt(wPart, 10);
      // Approximate: week 1 starts Jan 4
      const jan4 = new Date(parseInt(yr, 10), 0, 4);
      const monday = new Date(jan4);
      monday.setDate(jan4.getDate() - ((jan4.getDay() + 6) % 7) + (weekNum - 1) * 7);
      return monday.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }
    const [yr, mo] = key.split("-");
    return new Date(parseInt(yr, 10), parseInt(mo, 10) - 1, 1).toLocaleDateString("en-US", {
      month: "short",
      year: "numeric",
    });
  });

  const data = {
    labels,
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
