from pydantic import BaseModel


class ToolApprovalSpec(BaseModel):
    server: str
    tools: list[str]


class AgentSpec(BaseModel):
    name: str
    instructions: str
    mcp_servers: list[str]
    prompt: str
    tools_requiring_approval: list[ToolApprovalSpec] = []
