import os
import json
from dotenv import load_dotenv
from litellm import completion
import litellm

# Import our custom tool and schema
from hummcode.tools.file_ops import read_file, ReadFileArgs, list_files, ListFilesArgs, edit_file, EditFileArgs
from hummcode.tools.shell import execute_bash, BashArgs
from hummcode.tools.permissions import PermissionManager

# Load environment and set up observability
load_dotenv()
litellm.success_callback = ["langfuse"]

def main():
    print("🐦 Hummcode Agent Initialized. Type 'exit' to quit.")
    messages = []
    model_name = os.getenv("DEFAULT_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    
    # 1. Register tools using the Pydantic schema
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the contents of a given relative file path.",
                "parameters": ReadFileArgs.model_json_schema()
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files in the given directory, skipping noisy folders.",
                "parameters": ListFilesArgs.model_json_schema()
            }
        },
        {
            "type": "function",
            "function": {
                "name": "edit_file",
                "description": "Edit a file using surgical search and replace, or create/append if old_str is empty.",
                "parameters": EditFileArgs.model_json_schema()
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_bash",
                "description": "Execute a bash command and return its combined stdout and stderr.",
                "parameters": BashArgs.model_json_schema()
            }
        }
    ]

    # Instantiate the permission manager once per session
    perm_manager = PermissionManager()

    # Outer loop: Waiting for user input
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        messages.append({"role": "user", "content": user_input})
        
        # Inner loop: The Agent Execution Loop
        while True:
            # 1. Call the model with current history
            response = completion(
                model=model_name,
                messages=messages,
                tools=tools
            )
            
            ai_message = response.choices[0].message
            # Append Claude's response (text or tool_use) to history
            messages.append(ai_message.model_dump())

            # 2. If Claude didn't ask for any tools, we are done! Break the inner loop.
            if not ai_message.tool_calls:
                print(f"\nHummcode: {ai_message.content}")
                break
            
            # 3. Otherwise, execute each requested tool
            for tool_call in ai_message.tool_calls:
                
                if tool_call.function.name == "read_file":
                    args = json.loads(tool_call.function.arguments)
                    print(f"\n[🔧 Executing Tool] read_file('{args.get('path')}')")
                    result = read_file(args.get('path'))
                    
                elif tool_call.function.name == "list_files":
                    args = json.loads(tool_call.function.arguments)
                    target_path = args.get('path', '.') 
                    print(f"\n[🔧 Executing Tool] list_files('{target_path}')")
                    result = list_files(target_path)

                elif tool_call.function.name == "edit_file":
                    args = json.loads(tool_call.function.arguments)
                    path = args.get('path')
                    old_str = args.get('old_str', '')
                    new_str = args.get('new_str', '')

                    # Create a clear summary for the permission prompt
                    if not old_str:
                        action_details = f"Create or append to '{path}'"
                    else:
                        action_details = f"Modify '{path}'. Replacing '{old_str[:30]}...' with '{new_str[:30]}...'"
                        
                    # Check with the user before executing
                    if perm_manager.check_permission("edit_file", action_details):
                        print(f"\n[🔧 Executing Tool] edit_file('{path}')")
                        result = edit_file(path, old_str, new_str)
                    else:
                        print(f"\n[❌ Action Denied] edit_file('{path}')")
                        result = "Error: The user denied permission to execute this edit. Ask the user what to do next."
                
                elif tool_call.function.name == "execute_bash":
                    args = json.loads(tool_call.function.arguments)
                    command = args.get('command', '')
                    
                    # Check with the user before executing dangerous bash commands
                    if perm_manager.check_permission("execute_bash", command):
                        print(f"\n[🔧 Executing Tool] execute_bash('{command}')")
                        result = execute_bash(command)
                    else:
                        print(f"\n[❌ Action Denied] execute_bash('{command}')")
                        result = "Error: The user denied permission to execute this command. Ask the user what to do next."
                
                else:
                    # Catch-all for unrecognized tools so we don't crash!
                    print(f"\n[⚠️ Unknown Tool Requested] {tool_call.function.name}")
                    result = f"Error: Tool '{tool_call.function.name}' is not recognized."

                # Append the tool result to memory
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": result
                })
            
            # The inner loop automatically restarts here, sending the tool results back to Claude!

if __name__ == "__main__":
    main()
