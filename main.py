import argparse
import asyncio
import contextlib

from dotenv import load_dotenv

from core.factory import AgentFactory
from core.hitl_hooks import build_hitl_hooks
from core.planner import PlannerAgent

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
        custom_agent = await agent_factory.create_agent_from_spec(agent_spec, stack, tool_hooks=hitl_hooks)

        # Stream tokens/events to stdout
        stream = await custom_agent.arun(agent_spec.prompt, stream=True, stream_intermediate_steps=True)
        async for event in stream:
            if getattr(event, "event", None) == "RunResponseContent":
                print(getattr(event, "content", ""), end="", flush=True)

            elif getattr(event, "event", None) == "ToolCallCompleted":
                tool = getattr(event, "tool", None)
                if tool and getattr(tool, "tool_call_error", False):
                    print(f"\nTool failed: {getattr(tool, 'result', 'error')}")
                    # Optionally: break
                print(f"\n[ToolCallCompleted] {event.tool.name} → {event.tool.result}")

            elif getattr(event, "event", None) == "RunCancelled":
                print(f"\n{getattr(event, 'agent_message', 'Run cancelled.')}")
                break


if __name__ == "__main__":
    asyncio.run(main())
