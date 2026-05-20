import os
import sys 
import asyncio
from dotenv import load_dotenv
import litellm

# Import our modular components
from hummcode.memory import SessionTree
from hummcode.tools.registry import ToolRegistry
from hummcode.tools.permissions import PermissionManager
from hummcode.llm import LLMClient

# Load environment and set up observability
load_dotenv()
litellm.success_callback = ["langfuse"]

class HummcodeAgent:
    def __init__(self):
        self.memory = SessionTree()
        self.llm = LLMClient()
        self.perm_manager = PermissionManager()
        self.tools = ToolRegistry.get_tools()
        self.last_turn_id = None

    async def process_prompt(self, user_input: str):
        """Processes a single prompt and yields events to the UI."""
        
        # 1. CLI Command Router
        if user_input.startswith('/'):
            parts = user_input.split()
            cmd = parts[0].lower()
            
            if cmd == '/info':
                yield {"type": "system", "content": "\n🐦 **Hummcode** - Minimalist, powerful, model-agnostic, and composable."}
            elif cmd == '/list':
                yield {"type": "system", "content": "\n🛠️ Available Commands:\n  /info, /list, /model <name>, /clear, /rewind"}
            elif cmd == '/model':
                if len(parts) > 1:
                    self.llm.default_model = parts[1]
                    yield {"type": "system", "content": f"\n[🔄 Model Switched] Now using: {self.llm.default_model}"}
                else:
                    yield {"type": "system", "content": f"\n[ℹ️ Current Model] {self.llm.default_model}"}
            elif cmd == '/clear':
                self.memory = SessionTree()
                yield {"type": "system", "content": "\n[🗑️ Memory Cleared] Started a fresh session."}
            
            elif cmd == '/key':
                if len(parts) >= 3:
                    key_name = parts[1].upper()
                    key_value = parts[2]
                    
                    from dotenv import set_key
                    set_key('.env', key_name, key_value)
                    os.environ[key_name] = key_value # Update active memory
                    
                    yield {"type": "system", "content": f"\n[🔑 Key Set] Successfully saved {key_name} to .env"}
                else:
                    yield {"type": "system", "content": "\n[⚠️ Usage] /key <KEY_NAME> <YOUR_KEY>"}

            elif cmd == '/rewind':
                if self.last_turn_id:
                    self.memory.rewind(self.last_turn_id)
                    yield {"type": "system", "content": "\n[⏪ Rewound] Moved back to the previous turn."}
                else:
                    yield {"type": "system", "content": "\n[⚠️ Cannot Rewind] No previous turn to rewind to."}
            return

        # 2. Track node ID for /rewind, then add user message
        self.last_turn_id = self.memory.current_leaf_id
        self.memory.add_message({"role": "user", "content": user_input})

        # Trigger context compaction if memory gets too large
        if self.memory.compact():
            yield {"type": "status", "content": "[🧹 Memory] Context limit reached. Older messages summarized."}

        
        # 3. Inner Agent Execution Loop
        while True:
            yield {"type": "status", "content": "Thinking..."}
            
            # Call the LLM using our wrapper
            ai_message = self.llm.generate(messages=self.memory.get_llm_context(), tools=self.tools)
            self.memory.add_message(ai_message.model_dump())
            
            # If no tools are called, we're done!
            if not ai_message.tool_calls:
                yield {"type": "message", "role": "assistant", "content": ai_message.content}
                break
            
            # Execute requested tools
            for tool_call in ai_message.tool_calls:
                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments
                
                yield {"type": "status", "content": f"[🔧 Executing Tool] {tool_name}"}
                
                # Use our registry to run the tool (Note: perm_manager currently blocks for input here)
                result = await ToolRegistry.execute(tool_name, arguments, self.perm_manager)
                
                self.memory.add_message({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": result
                })
                
                yield {"type": "tool_result", "content": f"Result: {result[:100]}..."} # Truncated log for UI


async def main_cli():
    """A temporary async CLI wrapper to test the agent before building the TUI."""
    print("🐦 Hummcode Agent Initialized. Type 'exit' to quit.")
    agent = HummcodeAgent()
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        # Iterate over the yielded events from our agent
        async for event in agent.process_prompt(user_input):
            if event["type"] in ["system", "status", "tool_result"]:
                print(event["content"])
            elif event["type"] == "message":
                print(f"\n🐦 Hummcode: {event['content']}")

def main():
    if "--cli" in sys.argv:
        # Run the headless text version
        asyncio.run(main_cli())
    else:
        # Run the Textual UI by default
        from hummcode.ui.tui import HummcodeApp
        app = HummcodeApp()
        app.run()

if __name__ == "__main__":
    main()

