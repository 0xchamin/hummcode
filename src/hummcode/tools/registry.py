import json
from typing import Dict, Any

from hummcode.tools.file_ops import read_file, ReadFileArgs, list_files, ListFilesArgs, edit_file, EditFileArgs
from hummcode.tools.shell import execute_bash, BashArgs
from hummcode.tools.permissions import PermissionManager

class ToolRegistry:
    @staticmethod
    def get_tools() -> list[Dict[str, Any]]:
        """Returns the JSON schema array required by LiteLLM."""
        return [
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

    @staticmethod
    def execute(tool_name: str, arguments: str, perm_manager: PermissionManager) -> str:
        """Routes the tool call to the correct Python function, handling permissions."""
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            return "Error: Failed to parse tool arguments as valid JSON."

        if tool_name == "read_file":
            print(f"\n[🔧 Executing Tool] read_file('{args.get('path')}')")
            return read_file(args.get('path'))

        elif tool_name == "list_files":
            target_path = args.get('path', '.')
            print(f"\n[🔧 Executing Tool] list_files('{target_path}')")
            return list_files(target_path)

        elif tool_name == "edit_file":
            path = args.get('path')
            old_str = args.get('old_str', '')
            new_str = args.get('new_str', '')
            
            if not old_str:
                action_details = f"Create or append to '{path}'"
            else:
                action_details = f"Modify '{path}'. Replacing '{old_str[:30]}...' with '{new_str[:30]}...'"
                
            if perm_manager.check_permission("edit_file", action_details):
                print(f"\n[🔧 Executing Tool] edit_file('{path}')")
                return edit_file(path, old_str, new_str)
            else:
                print(f"\n[❌ Action Denied] edit_file('{path}')")
                return "Error: The user denied permission to execute this edit. Ask the user what to do next."

        elif tool_name == "execute_bash":
            command = args.get('command', '')
            if perm_manager.check_permission("execute_bash", command):
                print(f"\n[🔧 Executing Tool] execute_bash('{command}')")
                return execute_bash(command)
            else:
                print(f"\n[❌ Action Denied] execute_bash('{command}')")
                return "Error: The user denied permission to execute this command. Ask the user what to do next."

        else:
            print(f"\n[⚠️ Unknown Tool Requested] {tool_name}")
            return f"Error: Tool '{tool_name}' is not recognized."
