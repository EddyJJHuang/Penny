import type { Step } from "../types";

interface StepperProps {
  steps: Step[];
  currentStep: number;
}

export function Stepper({ steps, currentStep }: StepperProps) {
  return (
    <nav className="border-b border-gray-100 bg-white/50 backdrop-blur-md px-4 py-6">
      <div className="mx-auto flex max-w-lg items-center justify-center gap-1 sm:gap-2">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;

          return (
            <div key={step.label} className="flex items-center">
              <div className="flex items-center gap-1.5 sm:gap-2">
                {/* 
                  Progress Circle Indicator
                  Uses dynamic styling: emerald gradient for completed, dark styling for current step, and basic outline for upcoming steps
                */}
                <div
                  className={`flex h-8 w-8 sm:h-10 sm:w-10 items-center justify-center rounded-full text-xs sm:text-sm font-bold transition-all duration-500 ${
                    isCompleted
                      ? "bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md scale-105"
                      : isCurrent
                        ? "bg-gray-900 text-white ring-[4px] ring-gray-900/10 shadow-lg scale-110"
                        : "bg-white text-gray-400 border-2 border-gray-200"
                  }`}
                >
                  {isCompleted ? (
                    <svg
                      className="h-3.5 w-3.5 sm:h-4 sm:w-4"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth={2.5}
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  ) : (
                    index + 1
                  )}
                </div>

                {/* Label — hidden on very small screens */}
                <div className="hidden sm:block">
                  <span
                    className={`text-sm font-bold transition-colors duration-300 ${
                      isCurrent 
                        ? "text-gray-900" 
                        : isCompleted
                        ? "text-emerald-600"
                        : "text-gray-400 font-medium"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
              </div>

              {/* Connector */}
              {index < steps.length - 1 && (
                <div
                  className={`mx-2 sm:mx-4 h-1 w-8 sm:w-16 rounded-full transition-colors duration-500 ${
                    isCompleted ? "bg-emerald-500" : "bg-gray-200"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Mobile step label */}
      <p className="mt-2 text-center text-xs text-gray-500 sm:hidden">
        {steps[currentStep].description}
      </p>
    </nav>
  );
}
