# main.py

import asyncio
from jarvis_agents.simple_calendar_agent import calendar_agent
from jarvis_agents.simple_gmail_agent import gmail_agent
from dotenv import load_dotenv

load_dotenv(override=True)

async def main():
    while True:
        try:
            user_input = input("\n User: ").strip()
            if not user_input:
                continue

            # For now, directly call calendar agent
            # You can add routing logic here later
            # result = await calendar_agent(user_input)
            result = await gmail_agent(user_input)
            print(f"\nCalendar Agent: {result}")

        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f"Error: {e}")

    print("\nGoodbye!")

if __name__ == "__main__":
    print("🔧 Starting Jarvis...")
    asyncio.run(main())
