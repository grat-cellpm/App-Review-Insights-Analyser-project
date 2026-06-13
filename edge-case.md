# Corner Cases & Edge Cases

This document outlines potential edge cases and failure modes for the Weekly Product Review Pulse system, categorized by architectural components, along with suggested mitigation strategies.

## 1. Data Ingestion (Play Store Scraper)

| Edge Case | Description | Mitigation Strategy |
| :--- | :--- | :--- |
| **Zero Reviews Fetched** | The scraper returns 0 reviews for the configured 8-12 week window (could be due to a bug, scraper block, or network issue). | Add a pre-check before the LLM step. If reviews < threshold, abort the pipeline and send an alert email instead of a blank report. |
| **Pagination/Rate Limit Blocks** | Fetching 12 weeks of data for a high-volume app like Groww might hit Google Play Store rate limits or scraper pagination limits. | Implement exponential backoff, user-agent rotation, and batching in the scraping module. |
| **Non-English/Hinglish Reviews** | Reviews written in regional languages or mixed scripts (e.g., Hinglish) may not be clustered or summarized correctly. | Ensure the embedding model supports multilinguality (e.g., `text-embedding-3-small` handles this reasonably well). Prompt the LLM to translate quotes into English but preserve the original for authenticity. |
| **Play Store DOM Changes** | The unofficial Google Play Scraper breaks because Google updates its frontend API or DOM structure. | Monitor ingestion logs closely. Use robust, community-maintained libraries (`google-play-scraper`) that update quickly when DOMs change. |

## 2. Reasoning Layer (Embeddings, Clustering & LLM)

| Edge Case | Description | Mitigation Strategy |
| :--- | :--- | :--- |
| **Context Window Overflow** | A single massive cluster contains thousands of reviews, exceeding the LLM's token limit. | Implement a sampling mechanism. If a cluster size > `N`, randomly or semantically sample the top `N` most representative reviews closest to the cluster centroid. |
| **Quote Hallucination** | The LLM subtly tweaks a quote (e.g., fixing typos) which causes the exact-match verbatim validation to fail. | Use strict prompting: *"Do not fix grammar. Quote exactly."* Implement a fuzzy-matching fallback (e.g., Levenshtein distance) during validation, or rely strictly on substring matching and retry the LLM call if it fails. |
| **"Noise" Dominance** | HDBSCAN assigns the vast majority of reviews as "noise" (label `-1`) because reviews are too brief (e.g., "nice app"). | Filter out ultra-short reviews (e.g., < 3 words) before clustering. Tune HDBSCAN hyperparameters (`min_cluster_size`, `min_samples`). |
| **PII Scrubber Failures** | The scrubber either misses a phone number (privacy risk) or redacts critical non-PII numbers (e.g., "I lost 5000 Rs" $\rightarrow$ "I lost [REDACTED]"). | Use a specialized NER model over simple regex. Treat numeric strings contextually. |
| **API Rate Limits / Cost Spikes** | Hitting OpenAI/Anthropic/Google API rate limits, or incurring high costs during a massive influx of reviews (e.g., post-major release). | Implement token counting before API calls. Set hard token limits per run. Add retry logic with `Retry-After` handling for 429 rate limit errors. |

## 3. Output Delivery (Custom MCP Server)

| Edge Case | Description | Mitigation Strategy |
| :--- | :--- | :--- |
| **Google Doc Size Limit** | Over months/years, appending to a single master Google Doc will hit Google's size limits or become unnavigably slow. | Implement Doc rotation (e.g., creating a new Doc annually: `Weekly Review Pulse - Groww (2024)`). |
| **Expired/Revoked OAuth Tokens** | The Google Workspace refresh token expires, or the Google Cloud project's OAuth consent screen requires re-verification. | The MCP Server should log a distinct `AUTH_ERROR` which triggers an immediate failure alert to the admin to re-authenticate. |
| **Gmail Formatting Rejection** | The Gmail API rejects the payload due to malformed HTML, or spam filters block the email because of the content. | Keep the email HTML extremely simple (minimal inline CSS). Send from an internal corporate domain to internal groups to bypass spam filters. |

## 4. Orchestration & Idempotency

| Edge Case | Description | Mitigation Strategy |
| :--- | :--- | :--- |
| **Partial Pipeline Failures** | The script appends the report to Google Docs successfully, but crashes before sending the Gmail. On re-run, it might append a duplicate Doc section. | Ensure Google Doc idempotency strictly checks the Doc *content* for the current week's anchor (e.g., `# Week 42`) *before* attempting the append. |
| **Cross-Year Week Boundaries** | ISO weeks around New Year (e.g., Dec 31st falling in Week 1 of the next year) cause naming collisions or missed weeks. | Standardize strictly on the `ISO 8601` week date standard (`YYYY-Www`) across all logic, avoiding custom date math. |
| **Concurrent Execution** | The weekly cron job runs at the same time an admin manually triggers a backfill for the same week via CLI. | Use a local lock file (`.run.lock`) or a simple database lock to prevent concurrent executions of the pipeline. |
