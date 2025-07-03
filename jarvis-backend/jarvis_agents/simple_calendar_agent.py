from agents import Agent, Runner
from agents.mcp import MCPServerStdio


async def calendar_agent(request: str) -> str:
    """Simple calendar agent function"""

    async with MCPServerStdio(
        params={
            "command": "node",
            "args": ["/Users/mrityunjay/Code/MCP_Servers/google-calendar-mcp/build/index.js"],
            "env": {"GOOGLE_OAUTH_CREDENTIALS": "/Users/mrityunjay/Code/MCP_Servers/google-calendar-mcp/gcp-oauth.keys.json"}
        },
        cache_tools_list=True
    ) as mcp_server:

        agent = Agent(
            name="CalendarAgent",
            instructions="You are a calendar assistant. Help with calendar operations using available Google Calendar tools.",
            mcp_servers=[mcp_server]
        )

        result = await Runner.run(agent, request)

        # # Print RunResult details
        # print("=" * 50)
        # print("RAW RESULT")
        # print(f"- Last agent: {result.last_agent}")
        # print(f"- Final output: {result.final_output}")
        # print(f"- New items count: {len(result.new_items)}")
        # print(f"- Raw responses count: {len(result.raw_responses) if hasattr(result, 'raw_responses') else 'N/A'}")

        # print("\nNew items details:")
        # for i, item in enumerate(result.new_items):
        #     print(f"  Item {i+1}: {type(item).__name__}")
        #     if hasattr(item, 'type'):
        #         print(f"    Type: {item.type}")
        #     if hasattr(item, 'raw_item'):
        #         print(f"    Raw item: {item.raw_item}")

        # print("\nAll result attributes:")
        # for attr in dir(result):
        #     if not attr.startswith('_'):
        #         try:
        #             value = getattr(result, attr)
        #             if not callable(value):
        #                 print(f"  {attr}: {value}")
        #         except:
        #             print(f"  {attr}: <unable to access>")
        # print("=" * 50)

        # Show tools called
        tools_called = []
        for item in result.new_items:
            if hasattr(item, 'type') and item.type == 'tool_call_item':
                raw = item.raw_item
                tool_name = raw.name if hasattr(raw, 'name') else raw['name']
                tools_called.append(tool_name)

        if tools_called:
            print("🔧 Calendar tools called:")
            for i, tool_name in enumerate(tools_called, 1):
                print(f"   {i}. {tool_name}")

        return result.final_output if result and result.final_output else "Calendar request processed."
