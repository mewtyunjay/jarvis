from agents import Agent, Runner
from tools.calendar_tools import (
    list_calendars, list_events, search_events, list_colors, create_event,
    update_event, delete_event, get_freebusy, get_current_time, calendar_tools
)
import logging

logger = logging.getLogger(__name__)


async def calendar_agent(request: str) -> str:
    """Calendar agent using function_tool decorated Python tools"""

    # Ensure authentication before creating agent
    try:
        await calendar_tools.authenticate()
    except Exception as e:
        return f"❌ Calendar authentication failed: {e}"

    # Create agent with function_tool decorated tools
    agent = Agent(
        name="CalendarAgent",
        model = "gpt-4.1",
        instructions="""You are a Google Calendar assistant optimized for parallel processing and user timezone awareness.

        OPTIMIZATION RULES - FOLLOW THESE STRICTLY:
        1. **Start with get_current_time()** - ALWAYS call this first to get user's timezone and today's date range
        2. **Query ALL calendars efficiently** - Use list_calendars to get all calendar IDs, then query them all in parallel
        3. **Use parallel calendar operations** - Use JSON array format for list_events: '["cal1", "cal2", "cal3"]' to query multiple calendars at once
        4. **Maximize parallel calls** - The list_events function now runs calendar queries in parallel for better performance

        EFFICIENT WORKFLOW FOR "TODAY'S EVENTS":
        1. Call get_current_time() to get timezone and today's date range
        2. Call list_calendars to get all available calendar IDs (fast operation)
        3. Call list_events with ALL calendar IDs as JSON array and the time range from step 1
        4. Format times in user's local timezone from get_current_time response

        TIMEZONE HANDLING:
        - get_current_time() auto-detects user's timezone (likely ET)
        - Use the timezone info to format all event times in user's local time
        - Don't show UTC times to users - convert everything to their timezone

        CALENDAR SELECTION LOGIC:
        - Query ALL user calendars by default to show complete schedule
        - Use list_calendars to get all calendar IDs, then query them all in parallel
        - Only use 'primary' if user specifically asks for "just my main calendar"

        PARALLEL PERFORMANCE:
        - list_events with JSON array '["cal1", "cal2", "cal3"]' runs all queries in parallel
        - This is much faster than sequential calls
        - Always prefer querying multiple calendars over single calendar calls

        Available tools:
        - get_current_time: Get timezone-aware current time and today's date range
        - list_calendars: List available calendars (use to get all calendar IDs)
        - list_events: Get events from calendar(s) - supports parallel JSON array for multiple calendars
        - search_events: Search events by text query
        - create_event, update_event, delete_event: Manage events
        - list_colors, get_freebusy: Advanced features

        BE EFFICIENT: Use parallel calls, query all calendars, show complete schedule.""",
        tools=[
            list_calendars,
            list_events,
            search_events,
            list_colors,
            create_event,
            update_event,
            delete_event,
            get_freebusy,
            get_current_time
        ]
    )

    # Run the agent with the request
    result = await Runner.run(agent, request)

    # Show tools called (matching the original MCP implementation)
    tools_called = []
    for item in result.new_items:
        if hasattr(item, 'type') and item.type == 'tool_call_item':
            raw = item.raw_item
            tool_name = raw.name if hasattr(raw, 'name') else raw.get('name', 'unknown')
            tools_called.append(tool_name)

    if tools_called:
        print("🔧 Calendar tools called:")
        for i, tool_name in enumerate(tools_called, 1):
            print(f"   {i}. {tool_name}")

    return result.final_output if result and result.final_output else "Calendar request processed."
