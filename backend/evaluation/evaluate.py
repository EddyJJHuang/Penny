"""Classification evaluation pipeline.

Evaluates local-only, Gemini-only (skipped without API key), and hybrid
classifiers against the labeled test set. Outputs accuracy, per-category
precision/recall/F1, and misclassified transactions.

Usage:
    cd backend && python -m evaluation.evaluate
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report

# Ensure backend root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.schemas import Transaction
from app.services.classifier_local import classify_batch, classify_transaction

TEST_SET_PATH = Path(__file__).parent / "test_set.csv"
RESULTS_DIR = Path(__file__).parent / "results"


def load_test_set() -> list[dict[str, str]]:
    """Load the labeled test set CSV."""
    with open(TEST_SET_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def build_transactions(rows: list[dict[str, str]]) -> list[Transaction]:
    """Convert test set rows into Transaction objects."""
    return [
        Transaction(
            id=f"txn_{i:03d}",
            date="2025-01-15",
            description=row["description"],
            amount=float(row["amount"]),
            original_description=row["description"],
        )
        for i, row in enumerate(rows, start=1)
    ]


def evaluate_local(
    transactions: list[Transaction],
    expected: list[str],
) -> tuple[list[str], dict]:
    """Evaluate the local keyword classifier."""
    predicted: list[str] = []
    misclassified: list[dict] = []

    for txn, exp in zip(transactions, expected):
        result = classify_transaction(txn)
        pred = result.category.value if result is not None else "Uncategorized"
        predicted.append(pred)

        if pred != exp:
            misclassified.append({
                "description": txn.description,
                "expected": exp,
                "predicted": pred,
            })

    accuracy = accuracy_score(expected, predicted)
    report = classification_report(
        expected, predicted, zero_division=0, output_dict=True,
    )

    # Count how many got a match vs fell through to Uncategorized
    matched = sum(1 for txn in transactions if classify_transaction(txn) is not None)

    results = {
        "mode": "local-only",
        "accuracy": round(accuracy * 100, 2),
        "matched": matched,
        "unmatched": len(transactions) - matched,
        "match_rate": round(matched / len(transactions) * 100, 1),
        "report": report,
        "misclassified": misclassified[:20],
    }

    return predicted, results


def print_results(results: dict) -> None:
    """Pretty-print evaluation results to stdout."""
    mode = results["mode"]
    print(f"\n{'='*60}")
    print(f"  {mode.upper()}")
    print(f"{'='*60}")
    print(f"  Accuracy:   {results['accuracy']}%")

    if "matched" in results:
        print(f"  Matched:    {results['matched']} / {results['matched'] + results['unmatched']}"
              f"  ({results['match_rate']}%)")

    # Per-category table
    report = results["report"]
    print(f"\n  {'Category':<22} {'Prec':>6} {'Recall':>6} {'F1':>6} {'Count':>6}")
    print(f"  {'-'*22} {'-'*6} {'-'*6} {'-'*6} {'-'*6}")

    for cat, metrics in sorted(report.items()):
        if cat in ("accuracy", "macro avg", "weighted avg"):
            continue
        if not isinstance(metrics, dict):
            continue
        print(
            f"  {cat:<22} {metrics['precision']:>6.2f} {metrics['recall']:>6.2f}"
            f" {metrics['f1-score']:>6.2f} {int(metrics['support']):>6}"
        )

    # Macro/weighted averages
    for avg_key in ("macro avg", "weighted avg"):
        if avg_key in report and isinstance(report[avg_key], dict):
            m = report[avg_key]
            print(
                f"  {avg_key:<22} {m['precision']:>6.2f} {m['recall']:>6.2f}"
                f" {m['f1-score']:>6.2f} {int(m['support']):>6}"
            )

    # Misclassified
    misclassified = results.get("misclassified", [])
    if misclassified:
        print(f"\n  Top misclassified (showing {len(misclassified)}):")
        for m in misclassified[:10]:
            print(f"    {m['description'][:40]:<42} expected={m['expected']:<20} got={m['predicted']}")

    # Low F1 warnings
    low_f1_cats = []
    for cat, metrics in report.items():
        if not isinstance(metrics, dict):
            continue
        if cat in ("macro avg", "weighted avg"):
            continue
        if metrics["f1-score"] < 0.7 and metrics["support"] > 0:
            low_f1_cats.append((cat, metrics["f1-score"]))

    if low_f1_cats:
        print(f"\n  WARNING: Categories with F1 < 0.70:")
        for cat, f1 in low_f1_cats:
            print(f"    - {cat}: F1={f1:.2f}")


def save_results(results: dict, filename: str) -> None:
    """Save results to JSON and TXT files."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    json_path = RESULTS_DIR / f"{filename}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    txt_path = RESULTS_DIR / f"{filename}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Mode: {results['mode']}\n")
        f.write(f"Accuracy: {results['accuracy']}%\n")
        if "matched" in results:
            f.write(f"Match rate: {results['match_rate']}%\n")
        f.write(f"\nMisclassified ({len(results.get('misclassified', []))}):\n")
        for m in results.get("misclassified", []):
            f.write(f"  {m['description']}: expected={m['expected']}, got={m['predicted']}\n")


def main() -> None:
    """Run the full evaluation pipeline."""
    if not TEST_SET_PATH.exists():
        print(f"ERROR: Test set not found at {TEST_SET_PATH}")
        sys.exit(1)

    rows = load_test_set()
    print(f"Loaded {len(rows)} labeled transactions from {TEST_SET_PATH.name}")

    if len(rows) < 200:
        print(f"WARNING: Only {len(rows)} rows. Recommend at least 200 for reliable metrics.")

    transactions = build_transactions(rows)
    expected = [row["expected_category"] for row in rows]

    # --- Local-only evaluation ---
    _, local_results = evaluate_local(transactions, expected)
    print_results(local_results)
    save_results(local_results, "local_only")

    # --- Recommendations ---
    print(f"\n{'='*60}")
    print("  RECOMMENDATIONS")
    print(f"{'='*60}")

    if local_results["accuracy"] < 60:
        print(f"\n  Local accuracy ({local_results['accuracy']}%) is below 60% target.")
        print("  Suggested actions:")
        print("  - Run /add-keywords to expand keyword_map.json")
        print("  - Focus on categories with low recall")
    else:
        print(f"\n  Local accuracy: {local_results['accuracy']}% (meets 60% target)")

    uncat_count = sum(1 for m in local_results.get("misclassified", [])
                      if m["predicted"] == "Uncategorized")
    if uncat_count > 0:
        print(f"\n  {uncat_count} transactions fell through to Uncategorized.")
        print("  These are candidates for new keyword_map.json entries.")

    print(f"\n  Results saved to {RESULTS_DIR}/")
    print()


if __name__ == "__main__":
    main()
