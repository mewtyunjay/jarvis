from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from config.settings import settings
from datetime import datetime
import pytz


class CalendarAgent:
    """Calendar specialist agent using Agent SDK"""
    
    def __init__(self):
        self._agent = None
        self._mcp_server = None
    
    def _get_current_timestamp_info(self) -> str:
        """Get current timestamp information for the agent"""
        now_utc = datetime.now(pytz.UTC)
        now_local = now_utc.astimezone()
        
        return f"""
CURRENT TIMESTAMP INFORMATION:
- Current UTC time: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}
- Current local time: {now_local.strftime('%Y-%m-%d %H:%M:%S %Z (%z)')}
- Current date: {now_local.strftime('%A, %B %d, %Y')}
- Current timezone: {now_local.tzname()}

Use this timestamp information as your reference for "today", "now", "current time", etc.
"""
    
    async def _initialize_if_needed(self):
        """Initialize the calendar agent and MCP server if not already done"""
        if self._agent is None:
            # Create MCP server parameters as a dictionary
            params = {
                "command": "node",
                "args": [settings.CALENDAR_MCP_PATH],
                "env": {"GOOGLE_OAUTH_CREDENTIALS": settings.CALENDAR_MCP_CREDENTIALS}
            }
            
            # Create MCP server for calendar
            self._mcp_server = MCPServerStdio(
                params=params,
                name="Google Calendar MCP Server"
            )
            
            # Connect to the MCP server
            await self._mcp_server.connect()
            
            self._agent = Agent(
                name="Calendar Agent",
                instructions=f"""
                You are a calendar assistant specialist. You help with:
                - Checking calendar schedules and availability
                - Creating and managing calendar events
                - Scheduling meetings and appointments
                - Managing time-related tasks
                - Providing calendar information
                
                {self._get_current_timestamp_info()}
                
                IMPORTANT: Always use the current timestamp information provided above as your reference point.
                When users ask about "today", "tomorrow", "this week", etc., calculate based on the current date provided.
                
                Use the available Google Calendar tools to help users with their calendar needs.
                Be helpful and proactive in suggesting optimal times and managing conflicts.
                Always provide specific dates and times in your responses when relevant.
                """,
                model="gpt-4o-mini",
                mcp_servers=[self._mcp_server]
            )
    
    async def process_request(self, request: str) -> str:
        """Process calendar request using Agent SDK with fresh timestamp"""
        try:
            # Always reinitialize to get fresh timestamp
            self._agent = None
            await self._initialize_if_needed()
            
            # Add current timestamp to the request for context
            timestamp_context = self._get_current_timestamp_info()
            enhanced_request = f"{timestamp_context}\n\nUser Request: {request}"
            
            result = await Runner.run(self._agent, enhanced_request)
            return result.final_output if result and result.final_output else "Sorry, couldn't process your calendar request."
                
        except Exception as e:
            return f"Calendar error: {str(e)}"
    
    async def cleanup(self):
        """Clean up MCP server connection"""
        if self._mcp_server:
            await self._mcp_server.cleanup()
            self._mcp_server = None
            self._agent = None