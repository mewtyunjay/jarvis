from core_agents.planner import PlannerAgent
from agents import Agent, Runner
from openai.types.responses import ResponseTextDeltaEvent
from core_agents.agent_factory import create_agent_from_spec, load_mcp_registry
import asyncio
import contextlib

from dotenv import load_dotenv
load_dotenv()

def print_agent(agent):
    print("Agent created:")
    print(f"  Name: {agent.name}")
    print(f"  Instructions: {agent.instructions}")
    print(f"  MCP Servers: {[server.name for server in agent.mcp_servers]}")

async def main():
    # Get the agent spec from the planner
    planner_agent = PlannerAgent()
    user_input = input("Enter your query: ")
    agent_spec = planner_agent.run(user_input)

    # Load MCP config
    mcp_registry = load_mcp_registry("/Users/mrityunjay/Code/2025/jarvis_playground/mcp_config.json")

    # Create the agent from factory
    async with contextlib.AsyncExitStack() as stack:
        # Pass the stack into create_agent_from_spec
        custom_agent = await create_agent_from_spec(agent_spec, mcp_registry, stack)
        print(f"Input Prompt to Custom Agent: {agent_spec.prompt}")

        # Normal Output
        # result = await Runner.run(starting_agent=custom_agent, input=agent_spec.prompt)
        # print(result.final_output)

        #Streaming Output
        result = Runner.run_streamed(custom_agent, input=agent_spec.prompt)
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
