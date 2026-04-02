import type { ClassifiedTransaction, Transaction } from "../types";

interface TransactionTableProps {
  transactions: Transaction[];
  classifications: ClassifiedTransaction[];
  onClassifyComplete: (results: ClassifiedTransaction[]) => void;
  onContinue: () => void;
}

export function TransactionTable({
  transactions,
  classifications,
  onClassifyComplete,
  onContinue,
}: TransactionTableProps) {
  const hasResults = classifications.length > 0;

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            Review Transactions
          </h2>
          <p className="text-sm text-gray-500">
            {transactions.length} transactions parsed.{" "}
            {hasResults
              ? "Review and correct categories below."
              : "Click Classify to categorize."}
          </p>
        </div>
        <div className="flex gap-3">
          {!hasResults && (
            <button
              type="button"
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-blue-700 transition"
              onClick={() => {
                /* TODO: wire up classifyTransactions API call */
                onClassifyComplete([]);
              }}
            >
              Classify
            </button>
          )}
          {hasResults && (
            <button
              type="button"
              className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-emerald-700 transition"
              onClick={onContinue}
            >
              View Dashboard
            </button>
          )}
        </div>
      </div>

      {/* Transaction table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Date
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                Description
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                Amount
              </th>
              {hasResults && (
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Category
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {transactions.map((txn) => {
              const classified = classifications.find((c) => c.id === txn.id);
              return (
                <tr key={txn.id} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
                    {txn.date}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {txn.description}
                  </td>
                  <td
                    className={`whitespace-nowrap px-4 py-3 text-right text-sm font-medium ${
                      txn.amount < 0 ? "text-red-600" : "text-emerald-600"
                    }`}
                  >
                    {txn.amount < 0 ? "-" : "+"}$
                    {Math.abs(txn.amount).toFixed(2)}
                  </td>
                  {hasResults && (
                    <td className="whitespace-nowrap px-4 py-3 text-sm">
                      <span className="inline-flex rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                        {classified?.category ?? "—"}
                      </span>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
