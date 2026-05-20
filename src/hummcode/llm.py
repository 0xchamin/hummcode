import os
from litellm import completion

class LLMClient:
    def __init__(self):
        self.default_model = os.getenv("DEFAULT_MODEL", "anthropic/claude-sonnet-4-5-20250929")

    def generate(self, messages: list[dict], tools: list[dict] = None, model: str = None):
        """Calls the LLM provider using LiteLLM, automatically injecting AGENTS.md."""
        target_model = model if model else self.default_model
        
        # 1. Read AGENTS.md if it exists in the current directory
        if os.path.exists("AGENTS.md"):
            with open("AGENTS.md", "r", encoding="utf-8") as f:
                system_content = f.read()
                
            # 2. Inject it at the start of the context window
            if messages and messages[0].get("role") == "system":
                # If there's already a system message (like our summary node), append to it
                messages[0]["content"] = f"{system_content}\n\n{messages[0]['content']}"
            else:
                messages.insert(0, {"role": "system", "content": system_content})
        
        response = completion(
            model=target_model,
            messages=messages,
            tools=tools
        )
        
        return response.choices[0].message
