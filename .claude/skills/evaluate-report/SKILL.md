---
name: evaluate-report
description: Generate a comprehensive evaluation report for the Penny project, suitable for course submission or demo presentation. Use when the user asks for a final report, project summary, evaluation writeup, or is preparing for a demo or presentation.
allowed-tools: Bash, Read, Write, Glob, Grep
---

# Generate Evaluation Report

Create a comprehensive evaluation report for Penny's classification system.

## Steps

1. **Gather all evaluation data:**
   - Run `/classify-test` if results are not fresh (check timestamps in `backend/evaluation/results/`)
   - Read `backend/evaluation/results/` for accuracy metrics
   - Count entries in `backend/app/data/keyword_map.json`
   - Check how many bank formats are supported in `parser_csv.py`

2. **Generate report** at `backend/evaluation/results/evaluation_report.md` with these sections:

   ### System Overview
   - Brief description of the hybrid classification approach
   - Number of supported bank formats
   - Number of keywords in local classifier
   - Number of categories in taxonomy

   ### Test Methodology
   - Size of test set (must be 300+)
   - Source of test data (Kaggle synthetic + manually curated edge cases)
   - How ground truth labels were assigned
   - Category boundary rules applied

   ### Results
   - Overall accuracy table: Local-only vs Gemini-only vs Hybrid
   - Per-category precision/recall/F1 table
   - Confusion matrix (can be text-based)
   - Classification method distribution (% local, % Gemini, % uncategorized)

   ### Analysis
   - Which categories perform best/worst and why
   - Impact of the local fallback (what accuracy would be without it)
   - Common failure modes with examples
   - How the hybrid approach compares to either method alone

   ### Addressing Instructor Feedback
   - **Feedback 1 (API dependency):** Explain the local fallback classifier, show that the app functions without Gemini, report local-only accuracy
   - **Feedback 2 (Sample size):** Show that evaluation was run on 300+ transactions, document category definitions and edge case rules

   ### Future Improvements
   - Suggested next steps based on current weaknesses

3. **Format the report** cleanly in Markdown suitable for conversion to PDF if needed
