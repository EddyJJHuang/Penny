---
name: gemini-prompt
description: Design, test, and iterate on Gemini API prompts for transaction classification or savings recommendations. Use when the user wants to improve classification accuracy, adjust the Gemini prompt, tune recommendation quality, or debug unexpected API responses.
allowed-tools: Bash, Read, Write, Glob, Grep
---

# Gemini Prompt Engineering

Iterate on the Gemini API prompts used in Penny for classification and recommendations.

## Classification Prompt (`classifier_gemini.py`)

### When improving classification:

1. **Read current prompt** from `backend/app/services/classifier_gemini.py`

2. **Identify the problem** — ask the user or check recent evaluation results:
   - Systematic misclassification (e.g., all coffee shops going to Groceries)
   - Inconsistent outputs (same merchant getting different categories)
   - JSON parsing failures (malformed responses)
   - Specific edge cases failing

3. **Apply prompt improvements** using these techniques (in order of impact):
   - **Category definitions**: Include the exact taxonomy and edge case rules from CLAUDE.md in the system prompt
   - **Few-shot examples**: Add 3-5 examples of tricky transactions with correct categories, especially for the failing cases
   - **Output format enforcement**: Use explicit JSON schema in the prompt, e.g.:
     ```
     Respond ONLY with a JSON array. No markdown, no explanation.
     [{"description": "...", "category": "..."}]
     ```
   - **Batch framing**: Remind the model it's classifying a batch and each item is independent
   - **Negative examples**: If a specific error keeps recurring, add "Do NOT classify X as Y"

4. **Test the new prompt** against 10-20 previously misclassified transactions:
   ```bash
   cd backend && python -c "
   from app.services.classifier_gemini import classify_batch
   test_txns = [...]  # paste problem transactions here
   results = classify_batch(test_txns)
   for t, r in zip(test_txns, results):
       print(f'{t[\"description\"]:40s} -> {r}')
   "
   ```

5. **If results improve**, suggest running `/classify-test` for full evaluation

## Recommendation Prompt (`recommender.py`)

### When improving recommendations:

1. **Read current prompt** from `backend/app/services/recommender.py`

2. **Check recommendation quality criteria:**
   - References actual dollar amounts from user data (not generic)
   - Provides specific, actionable suggestions (not "spend less")
   - Includes estimated savings amounts
   - Covers the top 2-3 spending categories
   - Tone is helpful and non-judgmental

3. **Improve by:**
   - Including percentage of total spend per category in the prompt data
   - Adding month-over-month delta so the model can spot trends
   - Requesting exactly 3-5 recommendations (no more, no less)
   - Specifying output JSON schema for frontend parsing

4. **Test with sample aggregation data** before deploying changes
