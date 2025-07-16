from pydantic import BaseModel, ValidationError
from google import genai
import json
import os

class ToolApprovalSpec(BaseModel):
    server: str
    tools: list[str]

class AgentSpec(BaseModel):
    name: str
    instructions: str
    mcp_servers : list[str]
    prompt: str
    tools_requiring_approval: list[ToolApprovalSpec] = []


class PlannerAgent:
    def __init__(self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        mcp_tools_file: str = "MCP/mcp_tools.json"
        ):
        self.MODEL = model

        if not api_key:
            api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("API Key not provided for Gemini")
        self.client = genai.Client(api_key=api_key)

        self.mcp_tools, self.mcp_servers = self.__get_mcp_servers(mcp_tools_file)
        tool_map_str = self._build_tool_map_string(self.mcp_tools)

        self.SYSTEM_PROMPT = f"""
        You are an expert in intent analysis and agent configuration. Your task is to:

        1. Analyze the user's query to fully understand their goals and requirements.
        2. Break down the query into clear, actionable steps or tasks needed to fulfill the user's intent.
        3. Design an agent specification in structured JSON format, following this schema:

            {{
              "name": "A concise, descriptive name for the agent.",
              "instructions": "A one-sentence summary of the agent's primary function. Start with: you are a helpful agent who ...",
              "mcp_servers": ["List of relevant MCP server names used below (from the list provided)"],
              "prompt": "A well-crafted prompt that enables the agent to perform the required tasks effectively. List atomic, numbered steps.",
              "tools_requiring_approval": [
                {{"server": "gmail", "tools": ["send_email", "delete_draft"]}},
                {{"server": "filesystem", "tools": ["delete_file"]}}
              ]
              }}
            }}

            If no tools need approval, output [] (an empty list).

        The available MCP servers and their tools are:
        {tool_map_str}

        **Human Approval Requirement:**
        For any tool that may have side effects or needs user review (such as sending emails, deleting files, or modifying events), include its name under `tools_requiring_approval` for its respective server. Only include tools that genuinely require human approval for safety or correctness.

        - For example, if the user asks to send an email, add `"send_email"` under `"gmail"` in `tools_requiring_approval`.
        - If no tools require approval for this query, leave the field empty: {{}}

        **Additional Instructions:**
        - Output only the agent specification in valid JSON. No extra commentary, no markdown.
        - Do not invent new tool names—only use tools and servers listed above.
        - Do not ask the user if they want anything else.
        - Steps in the prompt should be atomic, clearly numbered, and use only the servers/tools from the list.

        ---

        Begin the agent specification.
        """


    def __get_mcp_servers(self, mcp_tools_file: str):
        try:
            with open(mcp_tools_file, 'r') as f:
                mcp_tools = json.load(f)
            servers = list(mcp_tools.keys())
            return mcp_tools, servers
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading MCP servers from {mcp_tools_file}: {e}")
            return {}, []
        except Exception as e:
            print(f"Unexpected error reading MCP servers: {e}")
            return {}, []

    def _build_tool_map_string(self, tool_map: dict):
        out = []
        for server, tools in tool_map.items():
            out.append(f"{server}:")
            for t, desc in tools:
                out.append(f"  - {t}: {desc}")
        return "\n".join(out)

    def run(self, user_input:str):
        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=user_input,
                config={
                    "system_instruction": self.SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                    "response_schema": AgentSpec,
                    },
            )
            if response.text is None:
                raise RuntimeError("No response text received from model.")
            data = json.loads(response.text)
            spec = AgentSpec.model_validate(data)
            return spec
        except ValidationError as e:
            raise ValueError(f"AgentSpec validation failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate agent specification: {e}")
