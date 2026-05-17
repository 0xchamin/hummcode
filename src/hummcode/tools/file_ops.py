import os 
from pydantic import BaseModel, Field

class ReadFileArgs(BaseModel):
    path: str = Field(..., description="The relative path of a file in the working directory.")

def read_file(path: str) -> str:
    """
    Read the contents of a given relative file path. Use this when you want to see what's inside a file.
    """
    if not os.path.exists(path):
        return f"Error: File '{path}' not found"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {str(e)}"