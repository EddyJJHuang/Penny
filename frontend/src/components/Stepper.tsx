import type { Step } from "../types";

interface StepperProps {
  steps: Step[];
  currentStep: number;
}

export function Stepper({ steps, currentStep }: StepperProps) {
  return (
    <nav className="border-b border-gray-100 bg-white px-4 py-4 sm:py-5">
      <div className="mx-auto flex max-w-lg items-center justify-center gap-1 sm:gap-2">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isCurrent = index === currentStep;

          return (
            <div key={step.label} className="flex items-center">
              <div className="flex items-center gap-1.5 sm:gap-2">
                {/* Circle */}
                <div
                  className={`flex h-7 w-7 sm:h-8 sm:w-8 items-center justify-center rounded-full text-xs sm:text-sm font-semibold transition-all duration-300 ${
                    isCompleted
                      ? "bg-emerald-600 text-white scale-100"
                      : isCurrent
                        ? "bg-emerald-600 text-white ring-4 ring-emerald-100"
                        : "bg-gray-200 text-gray-400"
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
                    className={`text-sm font-medium transition-colors duration-300 ${
                      isCurrent || isCompleted
                        ? "text-emerald-700"
                        : "text-gray-400"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
              </div>

              {/* Connector */}
              {index < steps.length - 1 && (
                <div
                  className={`mx-2 sm:mx-4 h-0.5 w-8 sm:w-16 rounded transition-colors duration-500 ${
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
