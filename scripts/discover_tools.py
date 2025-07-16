# This file contains the code for discovering tools from MCP servers
# Needs to run every time the MCP config is updated

import json
import asyncio
from agents import Agent
from agents.mcp import MCPServerStdio, MCPServerSse, MCPServerStreamableHttp
from agents.run_context import RunContextWrapper

MCP_CONFIG_PATH = "mcp/mcp_config.json"
TOOL_MAP_OUTPUT = "mcp/mcp_tools.json"

async def get_tools_for_server(name, conf):
    """Returns a tuple of tool name, tool description per MCP"""
    run_context = RunContextWrapper(context=None)
    agent = Agent(name="discovery_agent", instructions="tool discovery")

    server_type = conf.get("type", "stdio")
    if server_type == "stdio":
        async with MCPServerStdio(
            name=name,
            params={
                "command": conf["command"],
                "args": conf.get("args", []),
                "env": conf.get("env", {}),
            }
        ) as server:
            try:
                tools = await server.list_tools(run_context, agent)
                return [(t.name, t.description) for t in tools]
            except Exception as e:
                print(f"Error discovering tools for server {name}: {e}")
                return []
    elif server_type == 'sse':
        async with MCPServerSse(
            name=name,
            params={
                "url": conf["url"],
                "headers": conf.get("headers", {}),
            }
        ) as server:
            try:
                tools = await server.list_tools(run_context, agent)
                return [(t.name, t.description) for t in tools]
            except Exception as e:
                print(f"Error discovering tools for server {name}: {e}")
                return []
    elif server_type == 'streamable_http':
        async with MCPServerStreamableHttp(
            name=name,
            params={
                "url": conf["url"],
                "headers": conf.get("headers", {}),
            }
        ) as server:
            try:
                tool_list = await server.list_tools(run_context, agent)
                return [(t.name, t.description) for t in tool_list]
                # return [f"{t.name}: {t.description}" for t in tool_list]
            except Exception as e:
                print(f"Error discovering tools for server {name}: {e}")
                return []
    return []

async def main():
    with open(MCP_CONFIG_PATH, "r") as f:
        mcp_registry = json.load(f)["mcpServers"]

    tool_map = {}
    for name, conf in mcp_registry.items():
        print(f"Discovering tools for {name}...")
        tool_map[name] = await get_tools_for_server(name, conf)

    with open(TOOL_MAP_OUTPUT, "w") as f:
        json.dump(tool_map, f, indent=2)
    print(f"Tool map written to {TOOL_MAP_OUTPUT}")

if __name__ == "__main__":
    asyncio.run(main())
