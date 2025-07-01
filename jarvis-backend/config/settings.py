import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    #MCP paths
    CALENDAR_MCP_PATH = "/Users/mrityunjay/Code/MCP_Servers/google-calendar-mcp/build/index.js"
    CALENDAR_MCP_CREDENTIALS = "/Users/mrityunjay/Code/MCP_Servers/google-calendar-mcp/gcp-oauth.keys.json"

settings = Settings()