from pydantic import BaseModel, ValidationError
from google import genai
import json
import os

class AgentSpec(BaseModel):
    name: str
    instructions: str
    mcp_servers : list[str]
    prompt: str

class PlannerAgent:
    def __init__(self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        mcp_file_path: str = "MCP/mcp_config.json"
    ):
        self.MODEL = model
        if not api_key:
            api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("API Key not provided for Gemini")
        self.client = genai.Client(api_key=api_key)
        self.mcp_servers = self.__get_mcp_servers(mcp_file_path)
        self.SYSTEM_PROMPT = f'''
            You are an expert in intent analysis and agent configuration. Your task is to:
            1. Analyze the user's query to fully understand their goals and requirements.
            2. Break down the query into clear, actionable steps or tasks needed to fulfill the user's intent.
            3. Design an agent specification in structured YAML or JSON format, following this schema:
                name: A concise, descriptive name for the agent.
                instructions: A one-sentence summary of the agent's primary function. Start with
                you are a helpful agent who ...
                mcp_servers: List of relevant MCP server from:
                    <mcp_servers>
                    {self.mcp_servers}
                    </mcp_servers>.
                prompt: A well-crafted prompt that will enable the agent to perform the required tasks effectively.
                        Detailed steps atomically in which the task can be accomplished.
                        Each atomic step is to be performed by independent agent, and if it required two agents, it should be done in order to avoid cyclic dependencies.
                        It should be numbered. Instruct the output to be plaintext, no markdown formatting and do not ask if the user wants anything else.
                        Do not suggest specific functions, just which tool (gmail, github etc) to use and what action to perform.
            Mention the best format to get the information so that when information trickles down from tool to tool, only relevant information is passed.
            For any kind of event creation, always ask the agent to return the link to event created whenever possible.
            Output only the agent specification in the requested structured format. Do not include explanations or additional commentary.
            This prompt ensures the agent will:
                1. Thoroughly understand and decompose the user's intent.
                2. Generate a complete and structured agent configuration.
                3. Provide clear, actionable instructions and a high-quality prompt for downstream use.
            '''

    def __get_mcp_servers(self, mcp_file: str) -> list[str] | None:
        try:
            with open(mcp_file, 'r') as f:
                mcp_servers = json.load(f)
                servers = mcp_servers.get('mcpServers', {})
                return list(servers) if servers else []
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading MCP servers from {mcp_file}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error reading MCP servers: {e}")
            return None

    def show_mcp_servers(self):
        return self.mcp_servers

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
