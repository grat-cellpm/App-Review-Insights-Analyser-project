# App Review Insights Analyser

A powerful, AI-driven dashboard that automates the extraction, clustering, and summarization of app reviews from the Google Play Store. It uses advanced NLP techniques and Large Language Models to turn thousands of raw user reviews into actionable product insights.

## ✨ Features

- **Automated Data Ingestion:** Scrapes live reviews directly from the Google Play Store.
- **Privacy First:** Automatically scrubs PII (emails, phone numbers) from raw review text.
- **AI Clustering:** Uses `sentence-transformers`, UMAP, and HDBSCAN to group semantically similar reviews into distinct themes (e.g., "Poor App Performance", "High Brokerage Charges").
- **LLM Summarization:** Leverages the Groq API (Llama 3.1) to generate human-readable theme names, actionable product ideas, and exact representative quotes for each cluster.
- **Beautiful Frontend Dashboard:** A premium, modern web dashboard (HTML/CSS/JS) with dark mode and glassmorphism to visualize KPIs, sentiment trends, and cluster details.
- **Seamless Integrations:** Features a local FastAPI bridge that connects the dashboard to an MCP server, allowing you to instantly export insights directly to a **Google Doc** and draft an email summary in **Gmail**.

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- A Groq API Key
- Google Cloud OAuth Credentials (for Docs/Gmail integration)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd "App Review Insights Analyser project"
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Ensure you install dependencies for FastAPI, Uvicorn, SentenceTransformers, UMAP, HDBSCAN, Groq, etc.)*

3. **Configure Environment Variables**
   Copy the `.env.example` file to `.env` and fill in your keys:
   ```bash
   GROQ_API_KEY=your_groq_api_key
   GOOGLE_DOC_ID=your_target_google_doc_id
   TARGET_EMAIL=your_target_email_address
   ```

## 💻 Usage

### 1. Start the API Bridge
The API bridge handles the communication between the frontend dashboard and the Python backend scripts.
```bash
python api_bridge.py
```
*The server will start on `http://127.0.0.1:8003`.*

### 2. Open the Dashboard
To view the frontend dashboard, you can use any local web server. For example, using Python's built-in server:
```bash
# Open a new terminal window
python -m http.server 8080
```
Then, open your browser and navigate to `http://localhost:8080/frontend/`.

### 3. Sync & Export
- **Sync Now:** Click the "Sync Now" button in the dashboard to trigger the orchestrator. It will scrape fresh reviews, run the ML pipeline, and update the dashboard in real-time.
- **Export:** Click the "Export" button to automatically append the latest insights to your configured Google Doc and prepare a summary draft in your Gmail account.
- **Reports:** View the history of generated reports in the "Reports" tab.

## 🏗️ Architecture

- `agent/orchestrator.py`: The main pipeline script that runs ingestion, PII scrubbing, clustering, and LLM summarization.
- `api_bridge.py`: A FastAPI server that exposes endpoints (`/api/sync`, `/api/export`, `/api/reports`) for the frontend.
- `frontend/`: Contains the vanilla HTML, CSS, and JS for the dashboard UI.
- `mcp_server/`: Contains the logic for authenticating with Google Cloud and interacting with the Google Docs and Gmail APIs.

## 🔒 Security
- **Never push your `.env` file to GitHub.** It contains sensitive API keys. A `.gitignore` file is included to prevent this.
