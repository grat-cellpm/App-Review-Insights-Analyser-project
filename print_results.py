import sys
import os
import json

# Add agent directory to path so we can import formatter
sys.path.append(os.path.join(os.path.dirname(__file__), 'agent'))
from formatter import format_for_google_doc, format_for_gmail

def main():
    week_id = "2026-W24"
    doc_link = "https://docs.google.com/document/d/1SkR-L2800zNAR-TsEnf7LtleqUnHxsoJ_38DYQ_KfzA/edit"
    
    with open("temp_reasoning.json", "r", encoding='utf-8') as f:
        reasoning_data = json.load(f)
        
    plain_text_report = format_for_google_doc(week_id, reasoning_data.get("clusters", []))
    html_teaser = format_for_gmail(week_id, reasoning_data.get("clusters", []), doc_link)
    
    print("--- GOOGLE DOC CONTENT ---")
    print(plain_text_report)
    print("--- EMAIL DRAFT CONTENT ---")
    print(html_teaser)

if __name__ == "__main__":
    main()
