import { useEffect, useRef, useState } from "react";
import { Dashboard } from "./components/Dashboard";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { FileUpload } from "./components/FileUpload";
import { Stepper } from "./components/Stepper";
import { TransactionTable } from "./components/TransactionTable";
import { LandingPage } from "./components/LandingPage";
import type {
  ClassificationStats,
  ClassifiedTransaction,
  Step,
  Transaction,
} from "./types";

const STEPS: Step[] = [
  { label: "Upload", description: "Upload a bank statement" },
  { label: "Review", description: "Classify and review transactions" },
  { label: "Dashboard", description: "View spending insights" },
];

function App() {
  // State for toggling between the Landing Page and the main application
  const [showLanding, setShowLanding] = useState(true);
  
  // State to track the current step in the application flow (0: Upload, 1: Review, 2: Dashboard)
  const [currentStep, setCurrentStep] = useState(0);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [classifications, setClassifications] = useState<
    ClassifiedTransaction[]
  >([]);
  const [_stats, setStats] = useState<ClassificationStats | null>(null);

  // Step transition animation
  const contentRef = useRef<HTMLDivElement>(null);

  // Handles the transition animation between steps
  // Triggered whenever the current step or the landing page visibility changes
  useEffect(() => {
    const el = contentRef.current;
    if (!el) return;
    
    // Reset animation classes
    el.classList.remove("step-visible");
    el.classList.add("step-enter");

    // Force reflow to restart the animation, then apply the visible class
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        el.classList.remove("step-enter");
        el.classList.add("step-visible");
      });
    });
  }, [currentStep, showLanding]);

  // Reset the application state and return to the landing page
  const handleStartOver = () => {
    setShowLanding(true);
    setCurrentStep(0);
    setTransactions([]);
    setClassifications([]);
    setStats(null);
  };

  // Conditionally render the Landing Page if showLanding is true
  if (showLanding) {
    return <LandingPage onGetStarted={() => setShowLanding(false)} />;
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#fafcff] font-sans selection:bg-emerald-100 selection:text-emerald-900">
      {/* Header */}
      <header className="sticky top-0 z-20 border-b border-gray-100 bg-white/70 backdrop-blur-xl transition-all">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6 sm:py-4">
          <div className="flex items-center gap-2.5">
            {/* Logo */}
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-yellow-300 to-yellow-500 border-[2px] border-yellow-600 flex items-center justify-center shadow-[inset_0_-2px_4px_rgba(0,0,0,0.2),_0_2px_4px_rgba(0,0,0,0.1)] relative">
              <div className="w-5 h-5 rounded-full border border-yellow-600/40 flex items-center justify-center">
                 <span className="text-yellow-800 font-bold text-xs">¢</span>
              </div>
            </div>
            <div>
              <h1 className="text-lg font-bold leading-none text-gray-900">
                Penny
              </h1>
              <p className="hidden text-[10px] leading-tight text-gray-400 sm:block">
                Personal Finance Tracker
              </p>
            </div>
          </div>

          {currentStep > 0 && (
            <button
              type="button"
              className="flex items-center gap-1.5 rounded-full border border-gray-200 bg-white px-4 py-2 text-xs font-semibold text-gray-700 transition-all hover:bg-gray-50 hover:shadow-sm active:scale-95 sm:text-sm"
              onClick={handleStartOver}
            >
              <svg
                className="h-3.5 w-3.5"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182"
                />
              </svg>
              Start Over
            </button>
          )}
        </div>
      </header>

      {/* Stepper */}
      <Stepper steps={STEPS} currentStep={currentStep} />

      {/* Step content with transition */}
      <main className="flex-1 px-4 pb-12 pt-6 sm:px-6 sm:pb-16 sm:pt-8">
        <ErrorBoundary>
          <div ref={contentRef} className="step-enter">
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
                onClassifyComplete={(results, stats) => {
                  setClassifications(results);
                  setStats(stats);
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
          </div>
        </ErrorBoundary>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-white py-4 text-center text-xs text-gray-400">
        Penny — AI-powered finance insights. No data is stored.
      </footer>
    </div>
  );
}

export default App;
