from core.planner import PlannerAgent
from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent
from core.factory import AgentFactory
import asyncio
import contextlib
from dotenv import load_dotenv

load_dotenv()

def print_agent(agent):
    print("\n Agent created:")
    print(f"  Name: {agent.name}")
    print(f"  Instructions: {agent.instructions}")
    print(f"  MCP Servers: {[server.name for server in agent.mcp_servers]} \n")

async def main():
    # Get the agent spec from the planner
    planner_agent = PlannerAgent()
    agent_factory = AgentFactory()

    user_input = input("Enter your query: ")
    agent_spec = planner_agent.run(user_input)

    async with contextlib.AsyncExitStack() as stack:

        # Create custom agent based on agent spec
        custom_agent = await agent_factory.create_agent_from_spec(agent_spec, stack)

        # Print agent info
        print_agent(custom_agent)

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
