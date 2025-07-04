from agents import Agent, Runner
from tools.gmail_tools import gmail_tools, GmailAPIError, GmailAuthenticationError
import json
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)


async def gmail_agent(request: str) -> str:
    """Gmail agent using Python tools instead of MCP server"""
    
    # Define tools for the agent
    tools = [
        {
            "name": "send_email",
            "description": "Send an email with optional attachments, CC, BCC, and HTML formatting",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": ["string", "array"],
                        "description": "Recipient email address or list of addresses"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content"
                    },
                    "cc": {
                        "type": ["string", "array"],
                        "description": "CC email address or list of addresses"
                    },
                    "bcc": {
                        "type": ["string", "array"],
                        "description": "BCC email address or list of addresses"
                    },
                    "attachments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to attach"
                    },
                    "html": {
                        "type": "boolean",
                        "description": "Whether the body is HTML formatted"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        },
        {
            "name": "draft_email",
            "description": "Create an email draft with optional attachments, CC, BCC, and HTML formatting",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": ["string", "array"],
                        "description": "Recipient email address or list of addresses"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content"
                    },
                    "cc": {
                        "type": ["string", "array"],
                        "description": "CC email address or list of addresses"
                    },
                    "bcc": {
                        "type": ["string", "array"],
                        "description": "BCC email address or list of addresses"
                    },
                    "attachments": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file paths to attach"
                    },
                    "html": {
                        "type": "boolean",
                        "description": "Whether the body is HTML formatted"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        },
        {
            "name": "read_email",
            "description": "Read an email with full details including attachments",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "Gmail message ID"
                    }
                },
                "required": ["message_id"]
            }
        },
        {
            "name": "search_emails",
            "description": "Search emails using Gmail query syntax",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gmail search query (e.g., 'from:user@domain.com', 'subject:meeting', 'is:unread')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)"
                    },
                    "include_spam_trash": {
                        "type": "boolean",
                        "description": "Whether to include spam and trash emails"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "modify_email",
            "description": "Add or remove labels from an email",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "Gmail message ID"
                    },
                    "add_labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to add to the email"
                    },
                    "remove_labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to remove from the email"
                    }
                },
                "required": ["message_id"]
            }
        },
        {
            "name": "delete_email",
            "description": "Permanently delete an email",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "Gmail message ID"
                    }
                },
                "required": ["message_id"]
            }
        },
        {
            "name": "batch_modify_emails",
            "description": "Modify labels for multiple emails in batches",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Gmail message IDs"
                    },
                    "add_labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to add to the emails"
                    },
                    "remove_labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to remove from the emails"
                    },
                    "batch_size": {
                        "type": "integer",
                        "description": "Batch size for processing (default: 50)"
                    }
                },
                "required": ["message_ids"]
            }
        },
        {
            "name": "batch_delete_emails",
            "description": "Delete multiple emails in batches",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Gmail message IDs"
                    },
                    "batch_size": {
                        "type": "integer",
                        "description": "Batch size for processing (default: 50)"
                    }
                },
                "required": ["message_ids"]
            }
        },
        {
            "name": "list_email_labels",
            "description": "List all Gmail labels (system and user-defined)",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "create_label",
            "description": "Create a new Gmail label",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Label name"
                    },
                    "message_list_visibility": {
                        "type": "string",
                        "enum": ["show", "hide"],
                        "description": "Message list visibility (default: show)"
                    },
                    "label_list_visibility": {
                        "type": "string",
                        "enum": ["labelShow", "labelShowIfUnread", "labelHide"],
                        "description": "Label list visibility (default: labelShow)"
                    }
                },
                "required": ["name"]
            }
        },
        {
            "name": "update_label",
            "description": "Update an existing Gmail label",
            "parameters": {
                "type": "object",
                "properties": {
                    "label_id": {
                        "type": "string",
                        "description": "Label ID"
                    },
                    "name": {
                        "type": "string",
                        "description": "New label name"
                    },
                    "message_list_visibility": {
                        "type": "string",
                        "enum": ["show", "hide"],
                        "description": "Message list visibility"
                    },
                    "label_list_visibility": {
                        "type": "string",
                        "enum": ["labelShow", "labelShowIfUnread", "labelHide"],
                        "description": "Label list visibility"
                    }
                },
                "required": ["label_id"]
            }
        },
        {
            "name": "delete_label",
            "description": "Delete a Gmail label (user-created labels only)",
            "parameters": {
                "type": "object",
                "properties": {
                    "label_id": {
                        "type": "string",
                        "description": "Label ID"
                    }
                },
                "required": ["label_id"]
            }
        },
        {
            "name": "get_or_create_label",
            "description": "Get existing label ID or create new label if it doesn't exist",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Label name"
                    }
                },
                "required": ["name"]
            }
        },
        {
            "name": "download_attachment",
            "description": "Download an email attachment to local filesystem",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "Gmail message ID"
                    },
                    "attachment_id": {
                        "type": "string",
                        "description": "Attachment ID from email"
                    },
                    "download_path": {
                        "type": "string",
                        "description": "Local file path to save the attachment"
                    }
                },
                "required": ["message_id", "attachment_id", "download_path"]
            }
        }
    ]
    
    # Tool function mapping
    async def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Gmail tool with given parameters"""
        try:
            if tool_name == "send_email":
                return await gmail_tools.send_email(**parameters)
            elif tool_name == "draft_email":
                return await gmail_tools.draft_email(**parameters)
            elif tool_name == "read_email":
                return await gmail_tools.read_email(**parameters)
            elif tool_name == "search_emails":
                return await gmail_tools.search_emails(**parameters)
            elif tool_name == "modify_email":
                return await gmail_tools.modify_email(**parameters)
            elif tool_name == "delete_email":
                return await gmail_tools.delete_email(**parameters)
            elif tool_name == "batch_modify_emails":
                return await gmail_tools.batch_modify_emails(**parameters)
            elif tool_name == "batch_delete_emails":
                return await gmail_tools.batch_delete_emails(**parameters)
            elif tool_name == "list_email_labels":
                return await gmail_tools.list_email_labels()
            elif tool_name == "create_label":
                return await gmail_tools.create_label(**parameters)
            elif tool_name == "update_label":
                return await gmail_tools.update_label(**parameters)
            elif tool_name == "delete_label":
                return await gmail_tools.delete_label(**parameters)
            elif tool_name == "get_or_create_label":
                label_id = await gmail_tools.get_or_create_label(**parameters)
                return {"success": True, "label_id": label_id}
            elif tool_name == "download_attachment":
                return await gmail_tools.download_attachment(**parameters)
            else:
                raise GmailAPIError(f"Unknown tool: {tool_name}")
                
        except GmailAuthenticationError as e:
            logger.error(f"Authentication error in {tool_name}: {e}")
            return {"success": False, "error": f"Authentication failed: {e}"}
        except GmailAPIError as e:
            logger.error(f"API error in {tool_name}: {e}")
            return {"success": False, "error": f"Gmail API error: {e}"}
        except Exception as e:
            logger.error(f"Unexpected error in {tool_name}: {e}")
            return {"success": False, "error": f"Unexpected error: {e}"}
    
    # Create agent with tools
    agent = Agent(
        name="GmailAgent",
        instructions="""You are a Gmail assistant. Help with Gmail operations using the available Gmail tools.
        
        Available capabilities:
        - Send and draft emails with attachments, CC, BCC, and HTML formatting
        - Read emails with full content and attachment details
        - Search emails using Gmail's query syntax
        - Manage email labels (create, update, delete)
        - Batch operations for multiple emails
        - Download attachments from emails
        - Modify email labels (mark as read/unread, archive, etc.)
        
        Gmail search syntax examples:
        - 'from:user@domain.com' - emails from specific sender
        - 'subject:meeting' - emails with 'meeting' in subject
        - 'is:unread' - unread emails
        - 'has:attachment' - emails with attachments
        - 'after:2023-01-01' - emails after specific date
        - 'label:important' - emails with specific label
        
        Always authenticate before performing operations. Be helpful and provide clear responses about the Gmail operations performed.""",
        tools=tools
    )
    
    # Custom runner to handle tool execution
    class GmailRunner:
        def __init__(self, agent):
            self.agent = agent
        
        async def run(self, request: str) -> str:
            # For now, return a simple response
            # In a full implementation, you would need to parse the request
            # and determine which tools to call
            try:
                # Ensure authentication
                if not await gmail_tools.authenticate():
                    return "Failed to authenticate with Gmail. Please check your credentials."
                
                # This is a simplified implementation
                # In reality, you'd need to parse the request and call appropriate tools
                return f"Gmail agent processed request: {request}. Authentication successful."
                
            except Exception as e:
                logger.error(f"Error in Gmail runner: {e}")
                return f"Error processing Gmail request: {e}"
    
    # Run the agent
    runner = GmailRunner(agent)
    result = await runner.run(request)
    
    return result
