import os
import json
from dotenv import load_dotenv
from litellm import completion
import litellm

# Import our custom tool and schema
from hummcode.tools.file_ops import read_file, ReadFileArgs

# Load environment and set up observability
load_dotenv()
litellm.success_callback = ["langfuse"]

def main():
    print("🐦 Hummcode Agent Initialized. Type 'exit' to quit.")
    messages = []
    model_name = os.getenv("DEFAULT_MODEL", "anthropic/claude-sonnet-4-5-20250929")
    
    # 1. Register tools using the Pydantic schema
    tools = [{
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a given relative file path.",
            "parameters": ReadFileArgs.model_json_schema()
        }
    }]

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        messages.append({"role": "user", "content": user_input})
        
        # Initial inference call
        response = completion(
            model=model_name,
            messages=messages,
            tools=tools
        )
        
        ai_message = response.choices[0].message

        # 2. Check if the model wants to call a tool
        if ai_message.tool_calls:
            # Append the assistant's tool request to history
            messages.append(ai_message.model_dump())
            
            # Execute each requested tool
            for tool_call in ai_message.tool_calls:
                if tool_call.function.name == "read_file":
                    # Parse the JSON arguments Claude provided
                    args = json.loads(tool_call.function.arguments)
                    print(f"\n[🔧 Executing Tool] read_file({args.get('path')})")
                    
                    # Run our Python function
                    result = read_file(args.get('path'))
                    
                    # 3. Append the tool result to memory
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": result
                    })
            
            # 4. Trigger follow-up inference so Claude can read the result
            followup_response = completion(
                model=model_name,
                messages=messages,
                tools=tools
            )
            final_message = followup_response.choices[0].message
            print(f"\nHummcode: {final_message.content}")
            messages.append(final_message.model_dump())
            
        else:
            # Standard text response with no tools used
            print(f"\nHummcode: {ai_message.content}")
            messages.append(ai_message.model_dump())

if __name__ == "__main__":
    main()
