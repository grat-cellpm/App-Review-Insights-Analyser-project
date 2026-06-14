import json
from formatter import format_for_google_doc, format_for_gmail

def test_formatter():
    mock_summaries = [
        {
            "theme_name": "Login Issues",
            "review_count": 45,
            "actionable_ideas": ["Fix OTP delivery delay", "Improve biometric auth fallback"],
            "representative_quotes": ["I can't login with my fingerprint anymore", "OTP takes 5 minutes to arrive"]
        },
        {
            "theme_name": "UI Confusion",
            "review_count": 22,
            "actionable_ideas": ["Make portfolio graph more intuitive"],
            "representative_quotes": ["The new dashboard is very confusing to read."]
        }
    ]
    
    week_id = "2024-W42"
    doc_link = "https://docs.google.com/document/d/mock_doc_id"
    
    print("--- Google Docs Formatting ---")
    doc_text = format_for_google_doc(week_id, mock_summaries)
    print(doc_text)
    
    print("\n--- Gmail Formatting ---")
    email_html = format_for_gmail(week_id, mock_summaries, doc_link)
    print(email_html)

if __name__ == "__main__":
    test_formatter()
