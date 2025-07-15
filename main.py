from core.planner import PlannerAgent
from agents import Runner, ItemHelpers
from openai.types.responses import ResponseTextDeltaEvent
from core.factory import AgentFactory
import asyncio
import contextlib
from dotenv import load_dotenv
import argparse
import json

load_dotenv(override=True)

def print_agent(agent):
    print("\n Agent created:")
    print(f"  Name: {agent.name}")
    print(f"  Instructions: {agent.instructions}")
    print(f"  MCP Servers: {[server.name for server in agent.mcp_servers]} \n")

async def main():

    # CLI args
    parser = argparse.ArgumentParser(description='Run agent with optional debug mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Get the agent spec from the planner
    planner_agent = PlannerAgent()
    agent_factory = AgentFactory()

    user_input = input("Enter your query: ")
    agent_spec = planner_agent.run(user_input)

    async with contextlib.AsyncExitStack() as stack:
        # Create custom agent based on agent spec
        custom_agent = await agent_factory.create_agent_from_spec(agent_spec, stack)

        # Print agent info
        if args.debug:
            print("========= Debug =========")
            print(f"Custom Agent:")
            print_agent(custom_agent)
            print(f"Input to Custom Agent:")
            print(agent_spec.prompt)

        # Non-Streaming Output
        # result = await Runner.run(starting_agent=custom_agent, input=agent_spec.prompt)
        # print(result.final_output)

        # #Streaming Output
        result = Runner.run_streamed(custom_agent, input=agent_spec.prompt)
        if args.debug:
            async for event in result.stream_events():
                # We'll ignore the raw responses event deltas
                if event.type == "raw_response_event":
                    continue

                # When items are generated, print them
                elif event.type == "run_item_stream_event":
                    if event.item.type == "tool_call_item":
                        tool_argument = json.loads(event.item.raw_item.arguments)
                        tool_name = event.item.raw_item.name
                        print(f"\n TOOL CALLED : {tool_name}")
                        print(f"\n TOOL CALL ARGS : {tool_argument}")
                        print()
                    elif event.item.type == "tool_call_output_item":
                        tool_output = json.loads(event.item.output)
                        print(f"\n OUTPUT FROM TOOL CALL : {tool_output.get('text', '')}")
                        print()
                    elif event.item.type == "message_output_item":
                        print(f"======== FINAL OUTPUT ========:\n {ItemHelpers.text_message_output(event.item)}")
                    else:
                        pass  # Ignore other event types
        else:
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    print(event.data.delta, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
