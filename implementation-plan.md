# Implementation Plan: Weekly Product Review Pulse

This document breaks down the end-to-end implementation of the Weekly Product Review Pulse (specifically for Groww on the Google Play Store) into logical, sequential phases based on the defined architecture and problem statement.

## Phase 1: Foundation & Custom MCP Server Setup
**Goal:** Establish the project repository and build the custom Google Workspace MCP Server to handle document appending and email delivery securely.

1. **Repository Initialization**
   - Initialize the project workspace (Python or Node.js).
   - Set up linting, formatting, and environment variable management (e.g., `.env` for API keys).
2. **Google Cloud Project Configuration**
   - Create a Google Cloud Console project.
   - Enable Google Docs API and Gmail API.
   - Configure OAuth 2.0 credentials and download client secrets.
3. **Custom MCP Server Development**
   - Build a Model Context Protocol (MCP) server.
   - Implement authentication handling (OAuth token flow and storage).
   - **Tool 1 (`append_to_doc`):** Implement logic to locate a Google Doc ID and append plain text content to the end of it.
   - **Tool 2 (`send_email`):** Implement logic to construct and send a brief HTML email via Gmail API.

## Phase 2: Data Ingestion Layer (Play Store)
**Goal:** Successfully scrape, filter, and normalize raw user reviews from the Google Play Store.

1. **Scraper Integration**
   - Integrate a library like `google-play-scraper`.
   - Configure it to target the Groww app package.
2. **Time-Window Filtering**
   - Implement logic to fetch all reviews from the last 8–12 weeks.
   - Handle pagination if required by the scraper library to ensure complete data extraction.
3. **Data Normalization**
   - Structure the raw scraped data into a clean JSON format (Review ID, Date, Rating, Text, App Version).

## Phase 3: Reasoning & Intelligence Layer
**Goal:** Process the raw text into structured insights, themes, and actionable ideas using embeddings, clustering, and an LLM.

1. **PII Scrubbing**
   - Implement a lightweight regex or Named Entity Recognition (NER) pass to remove phone numbers, emails, and names from the review text.
2. **Embeddings Generation**
   - Integrate an Embedding API (e.g., OpenAI `text-embedding-3-small`, Cohere, or local HuggingFace).
   - Batch process the cleaned reviews to generate vector embeddings.
3. **Density-Based Clustering**
   - Integrate dimensionality reduction (`UMAP`) and clustering (`HDBSCAN`).
   - Group the vectorized reviews into distinct thematic clusters.
4. **LLM Summarization & Quote Extraction**
   - Feed each cluster's reviews to an LLM via Groq API (e.g., Llama 3 models).
   - Prompt the LLM to: Name the theme, propose action ideas, and extract verbatim representative quotes.
   - Implement a validation step to ensure the extracted quotes exist *exactly* in the source review text.

## Phase 4: Output Formatting & Orchestrator
**Goal:** Stitch the pipeline together and format the data for delivery.

1. **Output Formatter**
   - Write templates to convert the structured JSON LLM output into:
     - A strictly plain text block for Google Docs (since the MCP only supports basic text appending without formatting).
     - A brief summary teaser for the Gmail body.
2. **The Orchestrator Agent**
   - Create the main script that sequentially calls: Ingestion $\rightarrow$ PII Scrubbing $\rightarrow$ Embeddings $\rightarrow$ Clustering $\rightarrow$ LLM $\rightarrow$ Formatting.

## Phase 5: Delivery & Idempotency Implementation
**Goal:** Securely deliver the generated reports using the remote MCP Server (`web-production-5f6ae0.up.railway.app`) while preventing duplicate runs.

1. **Idempotency Logic**
   - Generate an ISO week identifier (e.g., `2024-W42`).
   - Implement a run-state file (e.g., `run_history.json`) to prevent appending to the Google Doc or sending the same email twice for a given week. (We will bypass reading the Google Doc for existing headings since the MCP only supports basic appending).
2. **API Client Integration**
   - Have the Orchestrator connect to the remote FastAPI Server using standard HTTP POST requests at `https://web-production-5f6ae0.up.railway.app`.
   - Execute the `/append_to_doc` endpoint with the plain text report.
   - Execute the `/create_email_draft` endpoint with the teaser and link to the newly appended section.

## Phase 6: Testing, CLI, and Automation
**Goal:** Ensure reliability and set up the weekly schedule.

1. **CLI Interface**
   - Add a command-line interface allowing manual triggers (e.g., `npm run start -- --week 2024-W40` or `python main.py --week 2024-W40`).
2. **End-to-End Testing**
   - Run a staging mode (draft-only emails, test Google Doc) to verify the pipeline end-to-end.
3. **Scheduling / Deployment**
   - Configure a cron job on a dedicated server or a CI/CD scheduled workflow (e.g., GitHub Actions running every Monday morning at 8:00 AM IST) to run the Orchestrator automatically.
