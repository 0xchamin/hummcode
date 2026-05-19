import subprocess
from pydantic import BaseModel, Field

class BashArgs(BaseModel):
    command: str = Field(..., description="The bash command to execute. Can include pipes and redirects.")

def execute_bash(command: str) -> str:
    """Execute a bash command and return its combined stdout and stderr."""
    try:
        # shell=True allows standard bash features. 
        # timeout=120 prevents the LLM from accidentally hanging the agent with a command like 'ping'
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=120
        )
        
        # Combine stdout and stderr so the LLM gets the full picture
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
            
        # If the command failed (e.g., tests failed), make sure the LLM knows
        if result.returncode != 0:
            output = f"Command failed with exit code {result.returncode}.\n{output}"
            
        return output.strip() or "Command executed successfully with no output."
        
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 120 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"
