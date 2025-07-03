#!/usr/bin/env python3
"""
Interactive test client for the Jarvis orchestrator
"""

import asyncio
import json
import websockets
import sys

class JarvisTestClient:
    def __init__(self, ws_url: str = "ws://localhost:8000/ws"):
        self.ws_url = ws_url
        self.websocket = None
    
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            print(f"✅ Connected to {self.ws_url}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            print("🔌 Disconnected")
    
    async def send_message(self, message: str):
        """Send a message to the server"""
        if not self.websocket:
            print("❌ Not connected to server")
            return
        
        try:
            # Send message in the expected format
            message_data = {
                "type": "user_message",
                "content": message
            }
            await self.websocket.send(json.dumps(message_data))
            print(f"📤 You: {message}")
            
            # Wait for response
            response = await self.websocket.recv()
            
            try:
                response_data = json.loads(response)
                if response_data.get("type") == "assistant_message":
                    print(f"🤖 Jarvis: {response_data.get('content', '')}")
                elif response_data.get("type") == "connection":
                    print(f"🔗 Connection: {response_data.get('message', '')}")
                elif response_data.get("type") == "error":
                    print(f"❌ Error: {response_data.get('message', '')}")
                else:
                    print(f"📥 Raw response: {response}")
            except json.JSONDecodeError:
                print(f"📥 Raw response: {response}")
                
        except websockets.ConnectionClosed:
            print("❌ Connection closed by server")
            self.websocket = None
        except Exception as e:
            print(f"❌ Error sending message: {e}")
    
    async def interactive_chat(self):
        """Run an interactive chat session"""
        print("🎯 Jarvis Interactive Chat")
        print("Type your messages and press Enter to send")
        print("Type 'quit', 'exit', or 'q' to exit, or press Ctrl+C")
        print("=" * 60)
        
        # Connect to server
        if not await self.connect():
            return
        
        # Wait for connection message
        try:
            initial_response = await self.websocket.recv()
            response_data = json.loads(initial_response)
            if response_data.get("type") == "connection":
                print(f"🔗 {response_data.get('message', '')}")
        except:
            pass
        
        print("\n💡 Try asking about:")
        print("   • General questions: 'Hello, how are you?'")
        print("   • Calendar requests: 'What's my schedule today?'")
        print("   • Scheduling: 'Schedule a meeting for tomorrow at 2 PM'")
        print("   • Any other questions you have!")
        print("-" * 60)
        
        try:
            while True:
                try:
                    # Get user input
                    user_input = input("\n💬 You: ").strip()
                    
                    # Check for exit commands
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("👋 Goodbye!")
                        break
                    
                    # Skip empty messages
                    if not user_input:
                        continue
                    
                    # Send message and get response
                    await self.send_message(user_input)
                    
                except EOFError:
                    print("\n👋 Goodbye!")
                    break
                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                    
        except Exception as e:
            print(f"❌ Chat error: {e}")
        finally:
            await self.disconnect()

async def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Extract host and port from URL if provided
        url = sys.argv[1]
        if not url.startswith("ws://"):
            url = f"ws://{url}/ws"
        elif not url.endswith("/ws"):
            url = f"{url}/ws"
    else:
        url = "ws://localhost:8000/ws"
    
    client = JarvisTestClient(url)
    await client.interactive_chat()

if __name__ == "__main__":
    print("🚀 Starting Jarvis Interactive Chat Client...")
    asyncio.run(main()) 