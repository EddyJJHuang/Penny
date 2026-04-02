import { useState } from "react";
import { Dashboard } from "./components/Dashboard";
import { FileUpload } from "./components/FileUpload";
import { Stepper } from "./components/Stepper";
import { TransactionTable } from "./components/TransactionTable";
import type { ClassifiedTransaction, Step, Transaction } from "./types";

const STEPS: Step[] = [
  { label: "Upload", description: "Upload a bank statement" },
  { label: "Review", description: "Classify and review transactions" },
  { label: "Dashboard", description: "View spending insights" },
];

function App() {
  const [currentStep, setCurrentStep] = useState(0);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [classifications, setClassifications] = useState<ClassifiedTransaction[]>([]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <h1 className="text-xl font-bold text-gray-900">Penny</h1>
          {currentStep > 0 && (
            <button
              type="button"
              className="text-sm text-gray-500 hover:text-gray-700 transition"
              onClick={() => {
                setCurrentStep(0);
                setTransactions([]);
                setClassifications([]);
              }}
            >
              Start Over
            </button>
          )}
        </div>
      </header>

      {/* Stepper */}
      <Stepper steps={STEPS} currentStep={currentStep} />

      {/* Step content */}
      <main className="px-6 pb-16">
        {currentStep === 0 && (
          <FileUpload
            onUploadComplete={(txns) => {
              setTransactions(txns);
              setCurrentStep(1);
            }}
          />
        )}

        {currentStep === 1 && (
          <TransactionTable
            transactions={transactions}
            classifications={classifications}
            onClassifyComplete={(results) => {
              setClassifications(results);
            }}
            onContinue={() => setCurrentStep(2)}
          />
        )}

        {currentStep === 2 && (
          <Dashboard
            transactions={transactions}
            classifications={classifications}
          />
        )}
      </main>
    </div>
  );
}

export default App;
