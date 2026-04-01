---
name: add-keywords
description: Analyze misclassified or Gemini-classified transactions and expand keyword_map.json to improve local classifier coverage. Use when the user wants to improve local match rate, add merchant keywords, or after running /classify-test and finding low local accuracy.
allowed-tools: Bash, Read, Write, Glob, Grep
---

# Expand Keyword Map

Improve Penny's local keyword classifier by adding new merchant-to-category mappings.

## Steps

1. **Load current keyword map** from `backend/app/data/keyword_map.json`
   - Count existing entries and report current coverage

2. **Identify candidates for new keywords** from one of these sources (in priority order):
   - If `backend/evaluation/results/` has recent evaluation output → extract misclassified transactions where the local classifier returned null but Gemini got it right
   - If the user provides a CSV or transaction list → analyze those
   - If neither → scan `backend/evaluation/test_set.csv` for transactions not matched by current keywords

3. **For each candidate keyword:**
   - Extract the most distinctive substring from the merchant description (e.g., "SQ *BURRITO KING 94105" → "BURRITO KING")
   - Verify it won't conflict with existing mappings (e.g., "UBER" already maps to Transportation — don't add "UBER" → Dining Out; instead add "UBER EATS" → Dining Out)
   - Check for common abbreviations and variations (e.g., "WHOLEFDS" and "WHOLE FOODS" should both exist)
   - Respect the exact category names defined in CLAUDE.md

4. **Present proposed additions** to the user as a table:
   | Keyword | Category | Source Transaction | Confidence |
   Before writing, ask for confirmation.

5. **After confirmation**, update `keyword_map.json`:
   - Maintain alphabetical order by keyword
   - Preserve existing entries — never remove or modify them without explicit user approval
   - Validate JSON syntax after writing

6. **Report summary:**
   - Number of new keywords added
   - Estimated new local coverage percentage (if test set is available)
   - Suggest running `/classify-test` to verify improvement
