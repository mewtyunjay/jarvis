import asyncio
import json

import uvicorn
from agents import Agent, Runner
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

load_dotenv(override=True)

app = FastAPI(title="Jarvis Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = Agent(name="Jarvis", model="gpt-4.1-mini", instructions="You are a helpful assistant")

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