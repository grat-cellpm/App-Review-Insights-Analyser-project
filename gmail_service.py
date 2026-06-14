import base64
from email.message import EmailMessage
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .google_auth import authenticate_google

def send_email(to_email: str, subject: str, html_content: str) -> str:
    """
    Sends an HTML email using the Gmail API.
    """
    try:
        creds = authenticate_google()
        service = build('gmail', 'v1', credentials=creds)

        message = EmailMessage()
        message.set_content("Please enable HTML to view this email.")
        message.add_alternative(html_content, subtype='html')

        message['To'] = to_email
        message['From'] = 'me'  # 'me' refers to the authenticated user
        message['Subject'] = subject

        # Encode the message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {
            'raw': encoded_message
        }

        # Send the message
        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        
        return f"Email successfully sent to {to_email}. Message Id: {send_message['id']}"

    except HttpError as error:
        return f"An error occurred sending email: {error}"
    except Exception as err:
        return f"An unexpected error occurred: {err}"
