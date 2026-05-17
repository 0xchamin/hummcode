import os 
from litellm import completion 

def main():
    print("🐦 Hummingbird Agent Initialized. Type 'exit' to quit.")
    messages = []

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            break 
        
        # 1. Append user message to history
        messages.append({"role": "user", "content": user_input})

        # 2. Call the model (we're using Claude 3.5 Sonnet as our agentic foundation)
        response = completion(
            model = "anthropic/claude-sonnet-4-5-20250929",
            messages=messages
        )

        # 3. Extract the text and print it
        ai_message = response.choices[0].message.content 
        print(f"\nHummcode: {ai_message}")

        # 4. Save the AI's response to our memory
        messages.append({"role": "assistant", "content": ai_message})



