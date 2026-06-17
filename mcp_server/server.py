import sys
from mcp.server.fastmcp import FastMCP
from .docs_service import append_to_doc
from .gmail_service import send_email

# Initialize the FastMCP server
mcp = FastMCP("Groww_Review_Pulse_MCP")

@mcp.tool()
def append_to_google_doc(document_id: str, content: str) -> str:
    """
    Appends text content to the end of a specified Google Document.
    
    Args:
        document_id: The ID of the Google Document (found in the URL).
        content: The text content to append.
    """
    return append_to_doc(document_id, content)

@mcp.tool()
def send_gmail(to_email: str, subject: str, html_content: str) -> str:
    """
    Sends an HTML email via Gmail to the specified recipient.
    
    Args:
        to_email: The recipient's email address.
        subject: The subject of the email.
        html_content: The HTML body of the email.
    """
    return send_email(to_email, subject, html_content)

if __name__ == "__main__":
    # Run the server with SSE transport
    mcp.run(transport='sse')
