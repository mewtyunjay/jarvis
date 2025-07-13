from core_agents.planner import PlannerAgent
from dotenv import load_dotenv
load_dotenv()

planner_agent = PlannerAgent() # print(planner_agent.show_mcp_servers())
resp = planner_agent.run("I want help with searching my calendar")
print(type(resp))
print(resp)
