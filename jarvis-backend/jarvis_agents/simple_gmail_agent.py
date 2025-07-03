from agents import Agent, Runner
from agents.mcp import MCPServerStdio


async def gmail_agent(request: str) -> str:
    """Simple gmail agent function"""

    async with MCPServerStdio(
        params={
            "command": "node",
            "args": ["/Users/mrityunjay/Code/MCP_Servers/Gmail-MCP-Server/dist/index.js"],
            # "env": {"GOOGLE_OAUTH_CREDENTIALS": "/Users/mrityunjay/Code/MCP_Servers/google-calendar-mcp/gcp-oauth.keys.json"}
        },
        cache_tools_list=True
    ) as mcp_server:

        agent = Agent(
            name="GmailAgent",
            instructions="You are a gmail assistant. Help with gmail operations using available Gmail tools.",
            mcp_servers=[mcp_server]
        )

        result = await Runner.run(agent, request)

        # Show tools called
        tools_called = []
        for item in result.new_items:
            if hasattr(item, 'type') and item.type == 'tool_call_item':
                raw = item.raw_item
                tool_name = raw.name if hasattr(raw, 'name') else raw['name']
                tools_called.append(tool_name)

        if tools_called:
            print("🔧 Gmail tools called:")
            for i, tool_name in enumerate(tools_called, 1):
                print(f"   {i}. {tool_name}")

        return result.final_output if result and result.final_output else "gmail request processed."
