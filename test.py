import random
from textwrap import dedent

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools import tool
from agno.tools.reasoning import ReasoningTools
from agno.tools.thinking import ThinkingTools
from dotenv import load_dotenv

load_dotenv()

# dictionary for context
user_context = []

@tool(show_result=True)
def ask_followup(information: str = ""):
    """Ask the user follow-up questions"""
    info = input(information)
    user_context.append(info)
    return user_context.copy()

agent = Agent(
    model=Gemini(id="gemini-2.5-flash"),
    tools=[ask_followup,
        ReasoningTools(),
        ThinkingTools(think=True, add_instructions=True)],
    markdown=True,
    stream_intermediate_steps=True,
    show_tool_calls=True,
    instructions=dedent("""\
    You are a planner agent who will try to figure out user's actions from their request.
    You take as input the user's vague request, try to understand what they're trying to accomplish, and map
    out the necessary details. If some critical information is missing to perform that task, use @ask_followup tool
    to take more input from them (HITL: pause and get manual details via console) till you build the case. If you think you have all the information necessary to execute the task,
    simply return the steps needed to perform that task.

    For eg:
        If a user asks you to send an email, the minimum information needed to perform that task is receiver email id and content,
        so until you have that, you prompt the user for more info. Ask in first person.

    Do not ask the user if you want to perform the action, you are simply a planner for another agent. That other agent's
    job is to execute the task.
    """)
)
user_input = input("What would you like me to do: ")
response_stream = agent.run(user_input, stream=True)
for event in response_stream:
    print(f"User context: {user_context}")
    if event.event == "RunResponseContent":
            print(f"Content: {event.content}")
