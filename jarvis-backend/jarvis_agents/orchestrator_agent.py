from agents import Agent, Runner, function_tool
from jarvis_agents.calendar_agent import calendar_agent
from jarvis_agents.gmail_agent import gmail_agent

class JarvisOrchestrator:
    def __init__(self) -> None:
        self.conversation_inputs = []  # Store cumulative conversation history
        self.last_agent = None  # Store last agent for continuity

    @function_tool
    async def calendar_tool(task: str) -> str:
        """Handle calendar-related requests"""
        return await calendar_agent(task)

    @function_tool
    async def gmail_tool(task: str) -> str:
        """Handle email-related requests"""
        return await gmail_agent(task)

    async def process_request(self, request: str) -> str:
        """Process any request using specialized agents as tools with conversation history"""

        # Build inputs with conversation history
        if not self.conversation_inputs:
            # First interaction - just the user message
            current_inputs = request
        else:
            # Subsequent interactions - full conversation + new message
            current_inputs = self.conversation_inputs + [{"role": "user", "content": request}]

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
            
            You maintain conversation context and can reference previous interactions.
            """,
            tools=[self.calendar_tool, self.gmail_tool]
        )

        # Run agent with conversation context
        result = await Runner.run(orchestrator, current_inputs)
        
        # Update conversation state using framework methods
        self.conversation_inputs = result.to_input_list()
        self.last_agent = result.last_agent
        
        # Enhanced logging using new_items
        self._log_run_items(result.new_items)
        
        return result.final_output if result.final_output else "Request processed"
    
    def _log_run_items(self, new_items):
        """Enhanced logging using RunItems from result.new_items"""
        tool_calls = []
        handoffs = []
        
        for item in new_items:
            if hasattr(item, 'type'):
                if item.type == 'tool_call_item':
                    # Extract tool name from the raw item
                    raw = item.raw_item
                    tool_name = raw.name if hasattr(raw, 'name') else raw.get('name', 'unknown')
                    tool_calls.append(tool_name)
                elif item.type == 'handoff_call_item':
                    # Track handoffs between agents
                    raw = item.raw_item
                    target = getattr(raw, 'target', 'unknown')
                    handoffs.append(target)
        
        # Log tool calls
        if tool_calls:
            print("🤖 Jarvis tools called:")
            for i, tool_name in enumerate(tool_calls, 1):
                print(f"   {i}. {tool_name}")
        
        # Log handoffs if any
        if handoffs:
            print("🔄 Agent handoffs:")
            for i, target in enumerate(handoffs, 1):
                print(f"   {i}. → {target}")
    
    def get_conversation_history(self):
        """Get current conversation history (for debugging/inspection)"""
        return self.conversation_inputs
    
    def reset_conversation(self):
        """Reset conversation history (for new conversation)"""
        self.conversation_inputs = []
        self.last_agent = None
