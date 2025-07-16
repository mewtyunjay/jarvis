from agents import RunHooks
from core.models import ToolApprovalSpec


class HitlHooks(RunHooks):
    def __init__(self, approval_set: set[tuple[str, str]], debug: bool = False):
        super().__init__()
        self.approval_tools = {tool for _, tool in approval_set}
        self.session_approvals = set()  # remember approval for this session
        self.debug = debug

    def _debug_log(self, msg):
        if self.debug:
            print(f"[HITL] {msg}")

    async def on_tool_start(self, context, agent, tool):
        tool_name = getattr(tool, "name", None)
        self._debug_log(f"Tool about to be called for: {tool_name}")

        if tool_name in self.approval_tools and tool_name not in self.session_approvals:
            # args = getattr(tool, "params_json_schema", {}).get("properties", {})
            approve = input(f"HITL: Approve {tool_name}? (y/n): ")
            if not approve.lower().startswith("y"):
                self._debug_log(f"Denied tool call {tool_name}")
                raise RuntimeError("Tool call denied by user.")
            else:
                self.session_approvals.add(tool_name)
                self._debug_log(f"Approved tool call {tool_name}")
        return None  # continue as normal


def build_hitl_hooks(tools_requiring_approval: list[ToolApprovalSpec], debug=False):
    approval_set = {(spec.server, tool) for spec in tools_requiring_approval for tool in spec.tools}
    return HitlHooks(approval_set, debug=debug)
