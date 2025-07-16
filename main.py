from core.planner import PlannerAgent
from agents import Runner, ItemHelpers  # noqa
from openai.types.responses import ResponseTextDeltaEvent
from core.factory import AgentFactory
from core.hitl_hooks import build_hitl_hooks
import asyncio
import contextlib
from dotenv import load_dotenv
import argparse

load_dotenv(override=True)


async def main():
    parser = argparse.ArgumentParser(description="Run agent with optional debug mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    planner_agent = PlannerAgent(debug=args.debug)
    agent_factory = AgentFactory(debug=args.debug)

    user_input = input("Enter your query: ")
    agent_spec = planner_agent.run(user_input)
    hitl_hooks = build_hitl_hooks(agent_spec.tools_requiring_approval, debug=args.debug)

    async with contextlib.AsyncExitStack() as stack:
        custom_agent = await agent_factory.create_agent_from_spec(agent_spec, stack)

        # Streaming Output
        result = Runner.run_streamed(custom_agent, input=agent_spec.prompt, hooks=hitl_hooks)
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
