import json
import os
import datetime
import requests
from dotenv import load_dotenv

from ingestion import fetch_recent_reviews
from reasoning import process_phase_3
from formatter import format_for_google_doc, format_for_gmail

load_dotenv()

# Constants
MCP_SERVER_URL = "http://127.0.0.1:8000"
TARGET_EMAIL = os.environ.get("TARGET_EMAIL", "example@example.com")
GOOGLE_DOC_ID = os.environ.get("GOOGLE_DOC_ID", "YOUR_DOCUMENT_ID")
DOC_LINK = f"https://docs.google.com/document/d/{GOOGLE_DOC_ID}/edit"

def get_current_week_id():
    now = datetime.datetime.now()
    return f"{now.isocalendar().year}-W{now.isocalendar().week}"

def check_idempotency(week_id: str) -> bool:
    """Returns True if this week has already been processed."""
    run_file = "run_history.json"
    if not os.path.exists(run_file):
        return False
        
    with open(run_file, "r") as f:
        history = json.load(f)
        
    return week_id in history.get("processed_weeks", [])

def mark_as_processed(week_id: str):
    run_file = "run_history.json"
    history = {"processed_weeks": []}
    if os.path.exists(run_file):
        with open(run_file, "r") as f:
            history = json.load(f)
            
    if week_id not in history["processed_weeks"]:
        history["processed_weeks"].append(week_id)
        
    with open(run_file, "w") as f:
        json.dump(history, f, indent=2)

def trigger_mcp_actions(plain_text: str, html_teaser: str, week_id: str, staging: bool = False):
    mcp_url = os.environ.get("MCP_SERVER_URL", "https://mcp-server-xv9m.onrender.com").rstrip("/")
    api_key = os.environ.get("API_KEY", "")
    
    print(f"Connecting to remote MCP server at {mcp_url}...")
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    if staging:
        plain_text = f"[STAGING DRAFT - {week_id}]\n\n{plain_text}"
        html_teaser = f"<h2>[STAGING DRAFT]</h2>\n{html_teaser}"
        print("Staging mode: added draft tags to content.")

    try:
        # 1. Append to Google Doc
        print(f"Appending to Google Doc ({GOOGLE_DOC_ID})...")
        doc_payload = {
            "doc_id": GOOGLE_DOC_ID,
            "content": plain_text
        }
        res1 = requests.post(f"{mcp_url}/append_to_doc", json=doc_payload, headers=headers)
        res1.raise_for_status()
        print("Doc append result:", res1.json())
        
        # 2. Create Email Draft
        print(f"Creating email draft for {TARGET_EMAIL}...")
        email_payload = {
            "to": TARGET_EMAIL,
            "subject": f"[STAGING] Groww Review Insights: {week_id}" if staging else f"Groww Review Insights: {week_id}",
            "body": html_teaser
        }
        res2 = requests.post(f"{mcp_url}/create_email_draft", json=email_payload, headers=headers)
        res2.raise_for_status()
        print("Email result:", res2.json())
                
    except Exception as e:
        print(f"Error calling MCP tools: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response details: {e.response.text}")
        raise

def main(week_id: str = None, staging: bool = False):
    if week_id is None:
        week_id = get_current_week_id()
    print(f"Starting Orchestrator for {week_id}...")
    if staging:
        print("RUNNING IN STAGING MODE. Operations will be marked as [DRAFT] and not saved to history.")
    
    if not staging and check_idempotency(week_id):
        print(f"Week {week_id} has already been processed. Exiting to prevent duplicates.")
        return
        
    # Phase 2: Ingestion
    print("--- Phase 2: Ingestion ---")
    data = fetch_recent_reviews(app_id="com.nextbillion.groww", target_count=300)
    
    # Save normalized intermediate state
    with open("temp_normalized.json", "w", encoding='utf-8') as f:
        json.dump(data["normalized"], f, indent=2)
        
    # Phase 3: Reasoning
    print("--- Phase 3: Reasoning ---")
    process_phase_3("temp_normalized.json", "temp_reasoning.json")
    
    # Phase 4: Formatter
    print("--- Phase 4: Formatting ---")
    with open("temp_reasoning.json", "r", encoding='utf-8') as f:
        reasoning_data = json.load(f)
        
    plain_text_report = format_for_google_doc(week_id, reasoning_data.get("clusters", []))
    html_teaser = format_for_gmail(week_id, reasoning_data.get("clusters", []), DOC_LINK)
    
    # Phase 5: Delivery
    print("--- Phase 5: Delivery (API) ---")
    trigger_mcp_actions(plain_text_report, html_teaser, week_id, staging=staging)
    
    # Cleanup and Mark Done
    if not staging:
        mark_as_processed(week_id)
    print("Orchestrator finished successfully!")

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Review Insights Orchestrator.")
    parser.add_argument("--week", type=str, help="ISO week identifier (e.g., 2024-W40). Defaults to current week.")
    parser.add_argument("--staging", action="store_true", help="Run in staging mode (simulated delivery, draft emails).")
    args = parser.parse_args()
    main(week_id=args.week, staging=args.staging)
