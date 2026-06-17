from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .google_auth import authenticate_google

def append_to_doc(document_id: str, content: str) -> str:
    """
    Appends the provided content to the end of a Google Document.
    """
    try:
        creds = authenticate_google()
        service = build('docs', 'v1', credentials=creds)

        # Retrieve the document to find its end index
        document = service.documents().get(documentId=document_id).execute()
        
        # The end of the document is the end index of the last element in the body
        end_index = document.get('body').get('content')[-1].get('endIndex') - 1

        requests = [
            {
                'insertText': {
                    'location': {
                        'index': end_index,
                    },
                    'text': '\n' + content + '\n'
                }
            }
        ]

        result = service.documents().batchUpdate(
            documentId=document_id, body={'requests': requests}).execute()
            
        return f"Successfully appended content to document: {document_id}"

    except HttpError as err:
        return f"An error occurred appending to Google Docs: {err}"
    except Exception as err:
        return f"An unexpected error occurred: {err}"
