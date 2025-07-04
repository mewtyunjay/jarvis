from agents import Agent, Runner, function_tool
from jarvis_agents.simple_calendar_agent import calendar_agent
from jarvis_agents.simple_gmail_agent import gmail_agent

class JarvisOrchestrator:
    def __init__(self) -> None:
        pass

    @function_tool
    async def calendar_tool(task: str) -> str:
        """Handle calendar-related requests"""
        return await calendar_agent(task)

    @function_tool
    async def gmail_tool(task: str) -> str:
        """Handle email-related requests"""
        return await gmail_agent(task)

    async def process_request(self, request: str) -> str:
        """Process any request using specialized agents as tools"""

        # Create orchestrator agent with agent tools
        orchestrator: Agent = Agent(
            name="JarvisOrchestrator",
            instructions="""
            You are Jarvis, a general AI assistant that can handle complex multi-step workflows.

            You have access to specialized agents:
            - calendar_agent: for calendar operations (scheduling, finding free time, etc.)
            - gmail_agent: for email operations (sending, reading emails, etc.)

            For complex requests like "find free time and email someone":
            1. Use calendar_agent to find available times
            2. Use gmail_agent to send the email with that information

            when calling these tools, make sure to pass into the function appropriate request string.

            Break down multi-step requests and use the appropriate tools in sequence.
            """,
            tools=[self.calendar_tool, self.gmail_tool]
        )

        result = await Runner.run(orchestrator, request)
        
        # Show tools called
        tools_called = []
        for item in result.new_items:
            if hasattr(item, 'type') and item.type == 'tool_call_item':
                raw = item.raw_item
                tool_name = raw.name if hasattr(raw, 'name') else raw.get('name', 'unknown')
                tools_called.append(tool_name)

        if tools_called:
            print("🤖 Jarvis tools called:")
            for i, tool_name in enumerate(tools_called, 1):
                print(f"   {i}. {tool_name}")
        
        return result.final_output if result.final_output else "Request processed"
