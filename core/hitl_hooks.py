from agno.exceptions import StopAgentRun

from core.models import ToolApprovalSpec


def build_hitl_hooks(tools_requiring_approval: list[ToolApprovalSpec], debug=False):
    approval_tools = {tool for spec in tools_requiring_approval for tool in spec.tools}
    session_approvals = set()

    def _log(msg: str):
        if debug:
            print(f"[HITL]: {msg}")

    # Agno tool‑hook -> wraps every tool call
    async def hitl_hook(
        function_name: str,
        function_call,
        arguments: dict,
        **_,
    ):
        if function_name in approval_tools and function_name not in session_approvals:
            _log(f"Tool about to be called: {function_name}")
            if not input(f"HITL: Approve {function_name}? (y/n): ").lower().startswith("y"):
                _log(f"Denied tool call {function_name}")
                raise StopAgentRun(
                    "Tool call cancelled by user",
                    agent_message="Stopping execution as permission was not granted.",
                )
            _log(f"Approved tool call {function_name}")
            session_approvals.add(function_name)

        # execute tool
        return await function_call(**arguments)

    return [hitl_hook]
