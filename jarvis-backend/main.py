# main.py

import asyncio
from jarvis_agents.calendar_agent import calendar_agent
from jarvis_agents.gmail_agent import gmail_agent
from dotenv import load_dotenv
from jarvis_agents.orchestrator_agent import JarvisOrchestrator

load_dotenv(override=True)

async def main():
    orchestrator = JarvisOrchestrator()
    print("💬 Conversation history is maintained across turns. Type '/reset' to start fresh, '/history' to view conversation, or '/help' for commands.")

    while True:
        try:
            user_input = input("\n User: ").strip()
            if not user_input:
                continue
            
            # Handle special commands
            if user_input == "/reset":
                orchestrator.reset_conversation()
                print("🔄 Conversation history reset!")
                continue
            elif user_input == "/history":
                history = orchestrator.get_conversation_history()
                if history:
                    print(f"📝 Conversation has {len(history)} items")
                    # Show last few items for brevity
                    for item in history[-3:]:
                        role = item.get('role', 'unknown')
                        content = item.get('content', '')[:100]
                        print(f"   {role}: {content}...")
                else:
                    print("📝 No conversation history yet")
                continue
            elif user_input == "/help":
                print("📋 Available commands:")
                print("   /reset  - Reset conversation history")
                print("   /history - View conversation history")
                print("   /help   - Show this help message")
                continue

            # Process normal requests
            result: str = await orchestrator.process_request(user_input)
            print(f"\n{result}")

        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f"Error: {e}")

    print("\nGoodbye!")

if __name__ == "__main__":
    print("🔧 Starting Jarvis...")
    asyncio.run(main())
