import os 
from typing import Optional
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
    

#Skip these to keep the LLM's context window clean
IGNORE_DIRS = {".git", ".venv", "venv", "env", "__pycache__", "node_modules", "build", "dist"}


class ListFilesArgs(BaseModel):
    path: Optional[str] = Field(".", description="The directory path to list. Defaults to current directory")

def list_files(path: Optional[str] = ".") -> str:
    """List files in the given directory, skipping noisy folders."""
    target_path = path or "."

    found_files = []
    for root, dirs, files in os.walk(target_path):
        # Modify 'dirs' in-place to prevent os.walk from entering ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            # Create a clean relative path to display
            full_path = os.path.relpath(os.path.join(root, file), start=target_path)
            found_files.append(full_path)
    
    if not found_files:
        return "No files found"
    
    return "\n".join(sorted(found_files))
    

class EditFileArgs(BaseModel):
    path: str = Field(..., description="The path to the file to edit.")
    old_str: str = Field(..., description="The exact string to replace. Must be unique. Leave empty to append or create a new file.")
    new_str: str = Field(..., description="The new string to replace old_str with.")

def edit_file(path: str, old_str: str, new_str: str) -> str:
    """Edit a file using surgical search and replace, or create/append if old_str is empty."""
    # 1. Handle file creation
    if not os.path.exists(path):
        if old_str:
            return f"Error: File '{path}' not found. To create a new file, leave old_str empty."
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_str)
        return f"Successfully created new file {path}."
    
    # 2. Read existing content
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 3. Handle appending
    if not old_str:
        with open(path, 'a', encoding='utf-8') as f:
            f.write(new_str)
        return f"Successfully appended to {path}."
        
    # 4. Handle search and replace validation
    count = content.count(old_str)
    if count == 0:
        return f"Error: old_str not found in {path}. Make sure to include exact whitespace and indentation."
    elif count > 1:
        return f"Error: old_str appears {count} times in {path}. It must be unique. Please include more context."
        
    # 5. Execute the edit
    new_content = content.replace(old_str, new_str)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    return f"Successfully edited {path}."
