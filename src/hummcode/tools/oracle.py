import os
from pydantic import BaseModel, Field
from hummcode.llm import LLMClient

class AskOracleArgs(BaseModel):
    question: str = Field(..., description="The question or task to delegate to the Oracle.")
    model: str = Field(default="", description="Optional: The specific model to use. Leave empty for default.")

def ask_oracle(question: str, model: str = "") -> str:
    """Asks a secondary LLM a question to save main context/tokens."""
    oracle_llm = LLMClient()
    
    # Use requested model, ORACLE_MODEL env var, or fallback to the main agent's default model
    target_model = model if model else os.getenv("ORACLE_MODEL", oracle_llm.default_model)
    
    try:
        response = oracle_llm.generate(
            messages=[{"role": "user", "content": question}], 
            model=target_model
        )
        return response.content
    except Exception as e:
        return f"Oracle Error: {str(e)}"
