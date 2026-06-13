from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uvicorn
import subprocess
import shutil
import json
from dotenv import load_dotenv

from mcp_server.docs_service import append_to_doc
from mcp_server.gmail_service import send_email

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExportRequest(BaseModel):
    content: str
    html_content: str
    subject: str = "Groww Review Insights Export"

@app.post("/api/export")
def export_data(req: ExportRequest):
    doc_id = os.environ.get("GOOGLE_DOC_ID")
    to_email = os.environ.get("TARGET_EMAIL")
    
    if not doc_id or not to_email:
        raise HTTPException(status_code=500, detail="Missing configuration in .env")

    doc_res = append_to_doc(doc_id, req.content)
    email_res = send_email(to_email, req.subject, req.html_content)
    
    return {"status": "success", "doc_status": doc_res, "email_status": email_res}

@app.post("/api/sync")
def sync_data():
    try:
        # Run orchestrator in staging mode to generate new insights
        subprocess.run(["python", "agent/orchestrator.py", "--staging"], check=True)
        
        # Update the dashboard data
        if os.path.exists("temp_reasoning.json"):
            shutil.copy("temp_reasoning.json", "frontend/data.json")
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to generate new insights.")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Orchestrator script failed.")

@app.get("/api/reports")
def get_reports():
    history = []
    if os.path.exists("run_history.json"):
        with open("run_history.json", "r") as f:
            data = json.load(f)
            history = data.get("processed_weeks", [])
    
    doc_id = os.environ.get("GOOGLE_DOC_ID")
    return {
        "history": history,
        "doc_link": f"https://docs.google.com/document/d/{doc_id}/edit" if doc_id else "#"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003)
