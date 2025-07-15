import json
from agents import Agent
from agents.mcp import MCPServerStdio, MCPServerSse, MCPServerStreamableHttp

def load_mcp_registry(path="/Users/mrityunjay/Code/2025/jarvis_playground/mcp_config.json"):
    with open(path, "r") as f:
        data = json.load(f)
    if "mcpServers" not in data:
        raise ValueError("Config missing top-level 'mcpServers' key")
    return data["mcpServers"]

async def create_mcp_server(mcp_name, mcp_conf, stack):
    """Create an MCP server based on its type configuration"""
    server_type = mcp_conf.get("type", "stdio")  # Default to stdio if not specified

    if server_type == "stdio":
        server = MCPServerStdio(
            name=mcp_name,
            params={
                "command": mcp_conf["command"],
                "args": mcp_conf.get("args", []),
                "env": mcp_conf.get("env", {}),
                "cwd": mcp_conf.get("cwd"),
                "encoding": mcp_conf.get("encoding", "utf-8"),
                "encoding_error_handler": mcp_conf.get("encoding_error_handler", "strict")
            },
            cache_tools_list=mcp_conf.get("cache_tools_list", False),
            client_session_timeout_seconds=mcp_conf.get("client_session_timeout_seconds"),
            tool_filter=mcp_conf.get("tool_filter")
        )
    elif server_type == "sse":
        server = MCPServerSse(
            name=mcp_name,
            params={
                "url": mcp_conf["url"],
                "headers": mcp_conf.get("headers", {}),
                "timeout": mcp_conf.get("timeout", 30.0),  # HTTP request timeout in seconds
                "sse_read_timeout": mcp_conf.get("sse_read_timeout", 300.0)  # SSE connection timeout in seconds
            },
            cache_tools_list=mcp_conf.get("cache_tools_list", False),
            client_session_timeout_seconds=mcp_conf.get("client_session_timeout_seconds"),
            tool_filter=mcp_conf.get("tool_filter")
        )
    elif server_type == "streamable_http":
        server = MCPServerStreamableHttp(
            name=mcp_name,
            params={
                "url": mcp_conf["url"],
                "headers": mcp_conf.get("headers", {}),
                "timeout": mcp_conf.get("timeout", 60.0),
                "sse_read_timeout": mcp_conf.get("sse_read_timeout", 300.0)
            },
            cache_tools_list=mcp_conf.get("cache_tools_list", False),
            client_session_timeout_seconds=mcp_conf.get("client_session_timeout_seconds"),
            tool_filter=mcp_conf.get("tool_filter")
        )
    else:
        raise ValueError(f"Unsupported MCP server type: {server_type}. Supported types: stdio, sse, streamable_http")

    # Connect the server using the async context manager
    connected_server = await stack.enter_async_context(server)
    return connected_server

async def create_agent_from_spec(agent_spec, mcp_registry, stack) -> Agent:
    # validation
    if not hasattr(agent_spec, "name") or not hasattr(agent_spec, "instructions") or not hasattr(agent_spec, "mcp_servers") or not hasattr(agent_spec, "prompt"):
        raise ValueError("agent_spec is missing required fields.")
    if not isinstance(agent_spec.mcp_servers, list) or not agent_spec.mcp_servers:
        raise ValueError("agent_spec.mcp_servers must be a non-empty list.")

    servers = []
    for mcp_name in agent_spec.mcp_servers:
        if mcp_name not in mcp_registry:
            raise ValueError(f"MCP server '{mcp_name}' not found in registry")

        mcp_conf = mcp_registry[mcp_name]

        # Create server based on type
        connected_server = await create_mcp_server(mcp_name, mcp_conf, stack)
        servers.append(connected_server)

    agent = Agent(
        name=agent_spec.name,
        instructions=agent_spec.instructions,
        mcp_servers=servers,
    )
    return agent
