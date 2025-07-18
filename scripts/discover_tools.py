# mcp_dump_tools.py
import asyncio
import json
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

MCP_CONFIG_PATH = Path("mcp/mcp_config.json")
TOOL_MAP_OUTPUT = Path("mcp/mcp_tools.json")


async def _list_tools_stdio(conf: dict[str, Any]) -> list[tuple[str, str]]:
    params = StdioServerParameters(
        command=conf["command"],
        args=conf.get("args", []),
        env=conf.get("env"),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resp = await session.list_tools()
            return [(t.name, t.description or "") for t in resp.tools]


async def _list_tools_sse(conf: dict[str, Any]) -> list[tuple[str, str]]:
    # Expected keys: url, headers (opt), timeout (opt seconds), read_timeout (opt seconds)
    async with sse_client(
        url=conf["url"],
        headers=conf.get("headers"),
        timeout=conf.get("timeout", 60.0),
        sse_read_timeout=conf.get("sse_read_timeout", 300.0),
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resp = await session.list_tools()
            return [(t.name, t.description or "") for t in resp.tools]


async def _list_tools_streamable_http(conf: dict[str, Any]) -> list[tuple[str, str]]:
    # Expected keys: url, headers (opt), timeout (opt seconds), read_timeout (opt seconds)
    async with streamablehttp_client(
        url=conf["url"],
        headers=conf.get("headers"),
        timeout=conf.get("timeout", 60.0),
        sse_read_timeout=conf.get("sse_read_timeout", 300.0),
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resp = await session.list_tools()
            return [(t.name, t.description or "") for t in resp.tools]


async def list_tools_any(name: str, conf: dict[str, Any]) -> list[tuple[str, str]]:
    stype = conf.get("type", "stdio")
    if stype == "stdio":
        return await _list_tools_stdio(conf)
    if stype == "sse":
        return await _list_tools_sse(conf)
    if stype in ("streamable_http", "streamable-http"):
        return await _list_tools_streamable_http(conf)
    print(f"Unsupported MCP type for {name}: {stype}")
    return []


async def main() -> None:
    registry = json.loads(MCP_CONFIG_PATH.read_text())["mcpServers"]
    tool_map: dict[str, list[tuple[str, str]]] = {}
    for name, conf in registry.items():
        print(f"Discovering tools for {name}...")
        tools = await list_tools_any(name, conf)
        tool_map[name] = tools
    TOOL_MAP_OUTPUT.write_text(json.dumps(tool_map, indent=2))
    print(f"Wrote {TOOL_MAP_OUTPUT}")


if __name__ == "__main__":
    asyncio.run(main())
