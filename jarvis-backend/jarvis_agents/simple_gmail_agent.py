from agents import Agent, Runner
from tools.gmail_tools import (
    send_email, draft_email, read_email, search_emails, modify_email, 
    delete_email, list_email_labels, create_label, get_latest_emails,
    gmail_tools  # Import the main tools instance for authentication
)
import logging

logger = logging.getLogger(__name__)


async def gmail_agent(request: str) -> str:
    """Gmail agent using function_tool decorated Python tools"""
    
    # Ensure authentication before creating agent
    try:
        await gmail_tools.authenticate()
    except Exception as e:
        return f"❌ Gmail authentication failed: {e}"
    
    # Create agent with function_tool decorated tools
    agent = Agent(
        name="GmailAgent",
        instructions="""You are a Gmail assistant. Help with Gmail operations using the available Gmail tools.
        
        Available capabilities:
        - Send and draft emails with attachments, CC, BCC, and HTML formatting
        - Read emails with full content and attachment details
        - Search emails using Gmail's query syntax
        - List and manage email labels
        - Get latest emails from inbox
        - Modify email labels (mark as read/unread, archive, etc.)
        
        Gmail search syntax examples:
        - 'from:user@domain.com' - emails from specific sender
        - 'subject:meeting' - emails with 'meeting' in subject
        - 'is:unread' - unread emails
        - 'has:attachment' - emails with attachments
        - 'after:2023-01-01' - emails after specific date
        - 'label:important' - emails with specific label
        
        For requests like "what's my last email" or "latest email", use get_latest_emails.
        For reading specific emails, use search_emails first to find the email ID, then read_email.
        
        Always provide helpful and detailed responses about the Gmail operations performed.""",
        tools=[
            send_email,
            draft_email, 
            read_email,
            search_emails,
            modify_email,
            delete_email,
            list_email_labels,
            create_label,
            get_latest_emails
        ]
    )
    
    # Run the agent with the request
    result = await Runner.run(agent, request)
    
    return result.final_output if result and result.final_output else "Gmail request processed."
