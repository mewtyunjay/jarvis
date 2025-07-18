import asyncio
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

MCP_CONFIG_PATH = Path("mcp/mcp_config.json")
TOOL_MAP_OUTPUT = Path("mcp/mcp_tools.json")


async def _list_tools_stdio(conf) -> list[tuple[str, str]]:
    params = StdioServerParameters(
        command=conf["command"],
        args=conf.get("args", []),
        env=conf.get("env", {}),
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        return [(name, description) for name, description in await session.list_tools()]


async def _list_tools_sse(conf) -> list[tuple[str, str]]:
    async with (
        sse_client(url=conf["url"], headers=conf.get("headers", {})) as (read, write),
        ClientSession(read, write) as session,
    ):
        return [(name, description) for name, description in await session.list_tools()]


async def _list_tools_http(conf) -> list[tuple[str, str]]:
    async with (
        streamablehttp_client(url=conf["url"], headers=conf.get("headers", {})) as (
            read,
            write,
            get_session_id,
        ),
        ClientSession(read, write) as session,
    ):
        return [(name, description) for name, description in await session.list_tools()]


async def get_tools_for_server(name, conf):
    t = conf.get("type", "stdio")
    if t == "stdio":
        return await _list_tools_stdio(conf)
    if t == "sse":
        return await _list_tools_sse(conf)
    if t == "streamable_http":
        return await _list_tools_http(conf)
    return []


async def main():
    registry = json.loads(MCP_CONFIG_PATH.read_text())["mcpServers"]
    tool_map = {}
    for name, conf in registry.items():
        print(f"Discovering tools for {name}...")
        tool_map[name] = await get_tools_for_server(name, conf)

    TOOL_MAP_OUTPUT.write_text(json.dumps(tool_map, indent=2))
    print(f"Tool map written to {TOOL_MAP_OUTPUT}")


if __name__ == "__main__":
    asyncio.run(main())
