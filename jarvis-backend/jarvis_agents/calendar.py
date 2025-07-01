# jarvis_agents/calendar.py

import asyncio
from agents import Agent, MCPServerStdio, Runner
from config.settings import settings

async def calendar_agent():
   """Creates a calendar agent with Google Calendar MCP integration"""
   
   calendar_mcp = MCPServerStdio(
       params={
           "command": "node",
           "args": [settings.CALENDAR_MCP_PATH]
       },
       env={
           "GOOGLE_OAUTH_CREDENTIALS": settings.CALENDAR_MCP_CREDENTIALS
       }
   )
   
   agent = Agent(
       name="CalendarAgent",
       instructions="""
       You are a calendar management specialist. Use Google Calendar tools to:
       - Check schedules and find free time
       - Create, update, and delete events
       - Find scheduling conflicts
       - Suggest optimal meeting times
       - Provide schedule summaries
       
       Be proactive about time zone handling and scheduling etiquette.
       """,
       mcp_servers=[calendar_mcp]
   )
   
   return agent