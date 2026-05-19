import json
from typing import Dict, Any

from hummcode.tools.file_ops import read_file, ReadFileArgs, list_files, ListFilesArgs, edit_file, EditFileArgs
from hummcode.tools.shell import execute_bash, BashArgs
from hummcode.tools.permissions import PermissionManager
from hummcode.tools.oracle import ask_oracle, AskOracleArgs


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
            },
            {
                "type": "function",
                "function": {
                    "name": "ask_oracle",
                    "description": "Ask a secondary LLM a question to save main context/tokens.",
                    "parameters": AskOracleArgs.model_json_schema()
                }
            }

        ]

    @staticmethod
    async def execute(tool_name: str, arguments: str, perm_manager: PermissionManager) -> str:
        """Routes the tool call to the correct Python function, handling permissions asynchronously."""
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            return "Error: Failed to parse tool arguments as valid JSON."

        if tool_name == "read_file":
            return read_file(args.get('path'))

        elif tool_name == "list_files":
            target_path = args.get('path', '.')
            return list_files(target_path)
        
        elif tool_name == "ask_oracle":
            question = args.get('question', '')
            model = args.get('model', '')
            # No permission check needed since it just talks to an API!
            return ask_oracle(question, model)


        elif tool_name == "edit_file":
            path = args.get('path')
            old_str = args.get('old_str', '')
            new_str = args.get('new_str', '')
            
            if not old_str:
                action_details = f"Create or append to '{path}'"
            else:
                action_details = f"Modify '{path}'. Replacing '{old_str[:30]}...' with '{new_str[:30]}...'"
                
            # Note the 'await' here!
            if await perm_manager.check_permission("edit_file", action_details):
                return edit_file(path, old_str, new_str)
            else:
                return "Error: The user denied permission to execute this edit. Ask the user what to do next."

        elif tool_name == "execute_bash":
            command = args.get('command', '')
            # Note the 'await' here!
            if await perm_manager.check_permission("execute_bash", command):
                return execute_bash(command)
            else:
                return "Error: The user denied permission to execute this command. Ask the user what to do next."

        else:
            return f"Error: Tool '{tool_name}' is not recognized."
