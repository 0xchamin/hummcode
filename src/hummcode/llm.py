import os
from litellm import completion

class LLMClient:
    def __init__(self):
        # We load the default model once when the client starts
        self.default_model = os.getenv("DEFAULT_MODEL", "anthropic/claude-sonnet-4-5-20250929")

    def generate(self, messages: list[dict], tools: list[dict] = None, model: str = None):
        """
        Calls the LLM provider using LiteLLM.
        Abstracts away the provider-specific logic and handles basic routing.
        """
        target_model = model if model else self.default_model
        
        # In the future, we can easily add retry logic, fallback models, 
        # or token-limit checks right here before making the API call!
        response = completion(
            model=target_model,
            messages=messages,
            tools=tools
        )
        
        return response.choices[0].message
