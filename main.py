from core_agents.planner import PlannerAgent
import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

planner_agent = PlannerAgent()
resp = planner_agent.run("I want help with flight booking")
print(type(resp))
print(resp)
