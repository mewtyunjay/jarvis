import contextlib

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from core.factory import AgentFactory
from core.hitl_hooks import build_hitl_hooks
from core.planner import PlannerAgent
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()


@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_input = body.get("query")
    debug = body.get("debug", False)
    if not user_input:
        raise HTTPException(status_code=400, detail="Missing 'query' in request.")

    # --- Run planner agent as in main.py ---
    planner_agent = PlannerAgent(debug=debug)
    agent_spec = planner_agent.run(user_input)
    hitl_hooks = build_hitl_hooks(agent_spec.tools_requiring_approval, debug=debug)

    # Collect response content instead of streaming
    response_content = ""
    tool_calls = []
    status = "completed"
    error_message = None

    async with contextlib.AsyncExitStack() as stack:
        # Updated to match main.py pattern - no config_path parameter
        agent_factory = AgentFactory(
            debug=debug, config_path="/Users/mrityunjay/Code/2025/jarvis_playground/mcp/mcp_config.json"
        )
        custom_agent = await agent_factory.create_agent_from_spec(agent_spec, stack, tool_hooks=hitl_hooks)

        # Collect all events instead of streaming
        stream = await custom_agent.arun(agent_spec.prompt, stream=True, stream_intermediate_steps=True)
        async for event in stream:
            if getattr(event, "event", None) == "RunResponseContent":
                content = getattr(event, "content", "")
                if content:
                    response_content += content

            elif getattr(event, "event", None) == "ToolCallCompleted":
                tool = getattr(event, "tool", None)
                if tool:
                    tool_info = {
                        "name": getattr(tool, "name", "unknown"),
                        "result": getattr(tool, "result", ""),
                        "error": getattr(tool, "tool_call_error", False),
                    }
                    tool_calls.append(tool_info)
                    if getattr(tool, "tool_call_error", False):
                        status = "error"
                        error_message = f"Tool failed: {getattr(tool, 'result', 'error')}"
                        break

            elif getattr(event, "event", None) == "RunCancelled":
                status = "cancelled"
                error_message = getattr(event, "agent_message", "Run cancelled.")
                break

    # Return structured JSON response
    return JSONResponse(
        {
            "status": status,
            "content": response_content,
            "tool_calls": tool_calls,
            "error": error_message,
            "agent_spec": {
                "tools_required": [
                    {"server": tool.server, "tools": tool.tools} 
                    for tool in agent_spec.tools_requiring_approval
                ]
                if agent_spec.tools_requiring_approval
                else [],
                "prompt": agent_spec.prompt,
            },
        }
    )


# Optional: root or healthcheck
@app.get("/")
def root():
    return {"status": "ok"}
