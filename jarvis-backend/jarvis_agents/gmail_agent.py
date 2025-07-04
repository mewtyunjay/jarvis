from agents import Agent, Runner
from tools.gmail_tools import (
    send_email, draft_email, read_email, search_emails, modify_email, 
    delete_email, list_email_labels, create_label, get_latest_emails,
    get_latest_email_with_body, gmail_tools  # Import the main tools instance for authentication
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
        - Get latest emails from inbox (with or without full body)
        - Modify email labels (mark as read/unread, archive, etc.)
        
        Gmail search syntax examples:
        - 'from:user@domain.com' - emails from specific sender
        - 'subject:meeting' - emails with 'meeting' in subject
        - 'is:unread' - unread emails
        - 'has:attachment' - emails with attachments
        - 'after:2023-01-01' - emails after specific date
        - 'label:important' - emails with specific label
        
        IMPORTANT - Tool Selection Guide:
        - For "what's my last email" or "latest email" or "most recent email" requests: 
          USE get_latest_email_with_body() to get the full body content
        - For "latest emails" (plural) or "recent emails": 
          USE get_latest_emails() to get a list with summaries
        - For reading specific emails by ID: USE read_email(message_id)
        - For finding emails first: USE search_emails() then read_email() if full body needed
        
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
            get_latest_emails,
            get_latest_email_with_body
        ]
    )
    
    # Run the agent with the request
    result = await Runner.run(agent, request)
    
    # Show tools called (like the original MCP implementation)
    tools_called = []
    for item in result.new_items:
        if hasattr(item, 'type') and item.type == 'tool_call_item':
            raw = item.raw_item
            tool_name = raw.name if hasattr(raw, 'name') else raw.get('name', 'unknown')
            tools_called.append(tool_name)

    if tools_called:
        print("🔧 Gmail tools called:")
        for i, tool_name in enumerate(tools_called, 1):
            print(f"   {i}. {tool_name}")
    
    return result.final_output if result and result.final_output else "Gmail request processed."
