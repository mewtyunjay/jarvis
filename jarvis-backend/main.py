# main.py

import asyncio
from jarvis_agents.simple_calendar_agent import calendar_agent
from jarvis_agents.simple_gmail_agent import gmail_agent
from dotenv import load_dotenv
from jarvis_agents.orchestrator_agent import JarvisOrchestrator

load_dotenv(override=True)

async def main():
    orchestrator = JarvisOrchestrator()

    while True:
        try:
            user_input = input("\n User: ").strip()
            if not user_input:
                continue

            result:str = await orchestrator.process_request(user_input)
            print(f"\n{result}")

        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f"Error: {e}")

    print("\nGoodbye!")

if __name__ == "__main__":
    print("🔧 Starting Jarvis...")
    asyncio.run(main())
