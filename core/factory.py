import json
from contextlib import AsyncExitStack
from typing import Any

# from agno import tools #noqa
from agno.agent import Agent
from agno.models.google import Gemini  # noqa
from agno.models.openai import OpenAIChat  # noqa
from agno.tools.mcp import MCPTools, SSEClientParams, StreamableHTTPClientParams

from mcp import StdioServerParameters


class AgentFactory:
    def __init__(self, config_path: str = "MCP/mcp_config.json", debug: bool = False):
        """Initialize the AgentFactory with the path to the MCP configuration file."""
        self.config_path = config_path
        self._mcp_registry = None
        self.debug = debug

    def _debug_log(self, msg):
        if self.debug:
            print(f"[AgentFactory] {msg}")

    def load_mcp_registry(self) -> dict[str, Any]:
        """Load and cache the MCP registry from config file"""
        if self._mcp_registry is None:
            with open(self.config_path) as f:
                data = json.load(f)
            if "mcpServers" not in data:
                raise ValueError("MCP Config missing top-level 'mcpServers' key")
            self._mcp_registry = data["mcpServers"]
        return self._mcp_registry

    def reload_config(self) -> None:
        """Force reload of the configuration file"""
        self._mcp_registry = None
        self.load_mcp_registry()

    async def _connect_mcp_tools(self, name: str, conf: dict[str, Any], stack: AsyncExitStack):
        """Return an *opened* MCPTools instance for the given server."""
        stype = conf.get("type", "stdio")
        self._debug_log(f"Connecting {name} via {stype}")

        if stype == "stdio":
            params = StdioServerParameters(
                command=conf["command"],
                args=conf.get("args", []),
                env=conf.get("env", {}),
            )
            tools_ctx = MCPTools(transport="stdio", server_params=params)

        elif stype == "sse":
            sse_params = SSEClientParams(
                url=conf["url"],
                headers=conf.get("headers", {}),
                timeout=conf.get("timeout", 30.0),
                sse_read_timeout=conf.get("sse_read_timeout", 300.0),
            )
            tools_ctx = MCPTools(transport="sse", server_params=sse_params)

        elif stype == "streamable_http":
            http_params = StreamableHTTPClientParams(
                url=conf["url"],
                headers=conf.get("headers", {}),
                timeout=conf.get("timeout", 60.0),
                sse_read_timeout=conf.get("sse_read_timeout", 300.0),
            )
            tools_ctx = MCPTools(
                transport="streamable-http",
                server_params=http_params,
                timeout_seconds=conf.get("timeout", 60.0),
            )
        else:
            raise ValueError(f"Unsupported MCP server type: {stype}")

        # open context manager inside the shared AsyncExitStack
        return await stack.enter_async_context(tools_ctx)

    async def create_agent_from_spec(
        self,
        agent_spec,
        stack: AsyncExitStack,
        *,
        tool_hooks: list | None = None,
    ) -> Agent:
        """Create an agent from specification with MCP servers"""
        if not getattr(agent_spec, "instructions", None):
            raise ValueError("Invalid AgentSpec passed to factory")
        mcp_registry = self.load_mcp_registry()
        mcp_tools = []
        for mcp_name in getattr(agent_spec, "mcp_servers", []) or []:
            if mcp_name not in mcp_registry:
                raise ValueError(f"MCP server '{mcp_name}' not found in registry")
            mcp_tools.append(await self._connect_mcp_tools(mcp_name, mcp_registry[mcp_name], stack))

        agent = Agent(
            name=agent_spec.name,
            instructions=agent_spec.instructions,
            # model=Gemini(id="gemini-2.5-flash"),
            model=OpenAIChat(id="gpt-4.1"),
            # tools=mcp_tools + [ReasoningTools(add_instructions=True)],
            tools=mcp_tools,
            tool_hooks=tool_hooks or [],
            markdown=True,
        )

        self._debug_log(f"Created Agno agent '{agent.name}' with tools {agent.tools}")
        self._debug_log(f"Instructions: {agent.instructions}")
        return agent
