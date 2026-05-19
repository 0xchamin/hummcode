import os
import json
from dotenv import load_dotenv
#from litellm import completion
import litellm

# Import our custom tool and schema
from hummcode.tools.file_ops import read_file, ReadFileArgs, list_files, ListFilesArgs, edit_file, EditFileArgs
from hummcode.tools.shell import execute_bash, BashArgs
from hummcode.tools.permissions import PermissionManager
from hummcode.memory import SessionTree
from hummcode.tools.registry import ToolRegistry
from hummcode.llm import LLMClient


# Load environment and set up observability
load_dotenv()
litellm.success_callback = ["langfuse"]

def main():
    print("🐦 Hummcode Agent Initialized. Type 'exit' to quit.")
    messages = []
    memory = SessionTree()

    llm = LLMClient()
    #model_name = os.getenv("DEFAULT_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    
    # 1. Register tools using the Pydantic schema
    tools = ToolRegistry.get_tools()

    # Instantiate the permission manager once per session
    perm_manager = PermissionManager()

    # Outer loop: Waiting for user input
    while True:
        user_input = input("\nYou: ")

        # 1. Handle standard exits
        if user_input.lower() in ['exit', 'quit']:
            break

        # 2. CLI Command Router
        if user_input.startswith('/'):
            parts = user_input.split()
            cmd = parts[0].lower()
            
            if cmd == '/info':
                print("\n🐦 **Hummcode** - The hummingbird coding agent.")
                print("Minimalist, powerful, model-agnostic, and composable.")
            elif cmd == '/list':
                print("\n🛠️ Available Commands:")
                print("  /info         - Show information about Hummcode")
                print("  /list         - List all commands")
                print("  /model <name> - Switch LLM provider/model mid-session")
                print("  /clear        - Clear memory and start a fresh session")
                print("  /rewind       - Undo the last conversation turn")
            elif cmd == '/model':
                if len(parts) > 1:
                    model_name = parts[1]
                    print(f"\n[🔄 Model Switched] Now using: {llm.default_model}")
                else:
                    print(f"\n[ℹ️ Current Model] {llm.default_model}")
            elif cmd == '/clear':
                memory = SessionTree()
                print("\n[🗑️ Memory Cleared] Started a fresh session.")
            elif cmd == '/rewind':
                if 'last_turn_id' in locals() and last_turn_id:
                    memory.rewind(last_turn_id)
                    print("\n[⏪ Rewound] Moved back to the previous turn.")
                else:
                    print("\n[⚠️ Cannot Rewind] No previous turn to rewind to.")
            else:
                print(f"\n[⚠️ Unknown Command] Type /list to see available commands.")
                
            continue # Skip the rest of the loop so Claude doesn't see this command!

        # 3. Track the node ID *before* we add the new user message (for /rewind)
        last_turn_id = memory.current_leaf_id

        # 4. Add user message to memory    
        memory.add_message({"role": "user", "content": user_input})
        
        # Inner loop: The Agent Execution Loop
        while True:
            # 1. Call the model with current history
            # response = completion(
            #     model=model_name,
            #     messages=memory.get_llm_context(),
            #     tools=tools
            # )
            ai_message = llm.generate(messages=memory.get_llm_context(), tools=tools)
            
            #ai_message = response.choices[0].message
            # Append Claude's response (text or tool_use) to history
            memory.add_message(ai_message.model_dump())

            # 2. If Claude didn't ask for any tools, we are done! Break the inner loop.
            if not ai_message.tool_calls:
                print(f"\nHummcode: {ai_message.content}")
                break
            
            # 3. Otherwise, execute each requested tool
            for tool_call in ai_message.tool_calls:
                result = ToolRegistry.execute(
                    tool_name=tool_call.function.name, 
                    arguments=tool_call.function.arguments, 
                    perm_manager=perm_manager
                )
    
                # Append the tool result to memory
                memory.add_message({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": result
                })
            
            # The inner loop automatically restarts here, sending the tool results back to Claude!

if __name__ == "__main__":
    main()
