import { useEffect, useState } from "react";
import { getRecommendations } from "../services/api";
import type { Recommendation } from "../types";
import { SpotlightCard, StaggerContainer } from "./ui/animated";

interface RecommendationsProps {
  spendingByCategory: Record<string, number>;
  monthlyTotals: Record<string, number>;
}

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-lg border border-gray-200 bg-white p-5">
      <div className="mb-3 h-4 w-2/3 rounded bg-gray-200" />
      <div className="mb-2 h-3 w-full rounded bg-gray-100" />
      <div className="mb-2 h-3 w-5/6 rounded bg-gray-100" />
      <div className="mb-4 h-3 w-4/6 rounded bg-gray-100" />
      <div className="flex items-center justify-between">
        <div className="h-3 w-20 rounded bg-gray-100" />
        <div className="h-5 w-24 rounded bg-gray-100" />
      </div>
    </div>
  );
}

export function Recommendations({
  spendingByCategory,
  monthlyTotals,
}: RecommendationsProps) {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchRecommendations() {
      setIsLoading(true);
      setError(null);
      try {
        const response = await getRecommendations({
          spending_by_category: spendingByCategory,
          monthly_totals: monthlyTotals,
        });
        if (!cancelled) {
          setRecommendations(response.recommendations);
        }
      } catch {
        if (!cancelled) {
          setError("Could not generate recommendations. Please try again later.");
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    fetchRecommendations();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <h3 className="mb-4 text-sm font-semibold text-gray-700">
        AI Savings Recommendations
      </h3>

      {/* Error */}
      {error && (
        <div className="rounded-md bg-red-50 px-4 py-3">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Loading skeleton */}
      {isLoading && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && recommendations.length === 0 && (
        <div className="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center text-sm text-gray-400">
          No recommendations available for the current data.
        </div>
      )}

      {/* Animation: StaggerContainer + SpotlightCard — recommendation cards */}
      {!isLoading && recommendations.length > 0 && (
        <StaggerContainer
          className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3"
          staggerDelay={0.12}
          direction="up"
          distance={20}
        >
          {recommendations.map((rec, index) => (
            <SpotlightCard
              key={index}
              className="flex flex-col justify-between rounded-lg border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md"
              spotlightColor="rgba(16, 185, 129, 0.12)"
            >
              <div>
                <h4 className="mb-2 text-sm font-semibold text-gray-900">
                  {rec.title}
                </h4>
                <p className="mb-4 text-xs leading-relaxed text-gray-600">
                  {rec.detail}
                </p>
              </div>
              <div className="flex items-center justify-between border-t border-gray-100 pt-3">
                <span className="inline-flex rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
                  {rec.category}
                </span>
                <span className="text-sm font-semibold text-emerald-600">
                  Save ${rec.potential_savings.toFixed(0)}/mo
                </span>
              </div>
            </SpotlightCard>
          ))}
        </StaggerContainer>
      )}
    </div>
  );
}
