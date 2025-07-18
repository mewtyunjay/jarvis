import contextlib

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from openai.types.responses import ResponseTextDeltaEvent

from core.factory import AgentFactory
from core.hitl_hooks import build_hitl_hooks
from core.planner import PlannerAgent

app = FastAPI()


@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    user_input = body.get("query")
    debug = body.get("debug", False)
    if not user_input:
        raise HTTPException(status_code=400, detail="Missing 'query' in request.")

    # --- Run planner agent as in main.py ---
    # Fix path mismatch: use mcp/mcp_tools.json instead of MCP/mcp_tools.json
    planner_agent = PlannerAgent(debug=debug)
    agent_spec = planner_agent.run(user_input)
    hitl_hooks = build_hitl_hooks(agent_spec.tools_requiring_approval)

    async def event_stream():
        async with contextlib.AsyncExitStack() as stack:
            # Fix path mismatch: use mcp/mcp_config.json instead of MCP/mcp_config.json
            agent_factory = AgentFactory(config_path="mcp/mcp_config.json", debug=debug)
            custom_agent = await agent_factory.create_agent_from_spec(agent_spec, stack)

            from agents import Runner  # avoid circular import issues

            result = Runner.run_streamed(custom_agent, input=agent_spec.prompt, hooks=hitl_hooks)
            async for event in result.stream_events():
                # Fix streaming logic to match working pattern from main.py
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    yield event.data.delta

    return StreamingResponse(event_stream(), media_type="text/plain")


# Optional: root or healthcheck
@app.get("/")
def root():
    return {"status": "ok"}
