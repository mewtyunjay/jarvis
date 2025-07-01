# main.py
import asyncio
import json
import uvicorn
from agents import Agent, Runner, MCPServerStdio
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings

load_dotenv(override=True)

app = FastAPI(title="Jarvis Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def create_universal_agent():
    """Universal agent with all MCP capabilities"""
    
    calendar_mcp = MCPServerStdio(
        params={
            "command": "node",
            "args": [settings.CALENDAR_MCP_PATH]
        },
        env={
            "GOOGLE_OAUTH_CREDENTIALS": settings.CALENDAR_MCP_CREDENTIALS
        }
    )
    
    return Agent(
        name="Jarvis",
        instructions="""
        You are Jarvis, an AI assistant. Use available tools to help users:
        - For calendar requests: use Google Calendar tools to check/manage schedule
        - For other requests: provide helpful responses
        
        Be proactive and use tools when they would be helpful.
        """,
        mcp_servers=[calendar_mcp]
    )

# Create agent on startup
agent = None

@app.on_event("startup")
async def startup():
    global agent
    agent = await create_universal_agent()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text(
        json.dumps({
            "type": "connection",
            "status": "connected", 
            "message": "Connected to Jarvis Backend",
        })
    )
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "user_message":
                response = await Runner.run(agent, message["content"])
                await websocket.send_text(
                    json.dumps({
                        "type": "assistant_message",
                        "content": response.final_output,
                    })
                )
    except Exception as e:
        print(f"WebSocket Error: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)