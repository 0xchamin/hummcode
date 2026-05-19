import uuid
import litellm
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class Node:
    data: Dict[str, Any]
    parent_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

class SessionTree:
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.current_leaf_id: Optional[str] = None

    def add_message(self, data: Dict[str, Any]) -> str:
        """Adds a message as a child of the current leaf and moves the pointer."""
        node = Node(data=data, parent_id=self.current_leaf_id)
        self.nodes[node.id] = node
        self.current_leaf_id = node.id
        return node.id

    def get_llm_context(self) -> List[Dict[str, Any]]:
        """Walks from the current leaf up to the root, then reverses it for the LLM."""
        context = []
        curr_id = self.current_leaf_id
        
        while curr_id and curr_id in self.nodes:
            node = self.nodes[curr_id]
            context.append(node.data)
            curr_id = node.parent_id
            
        return context[::-1]

    def rewind(self, node_id: str):
        """Moves the active pointer back to an older node, abandoning bad branches."""
        if node_id in self.nodes:
            self.current_leaf_id = node_id
        else:
            raise ValueError(f"Node {node_id} not found in memory.")

    def compact(self, max_tokens: int = 40000, window_size: int = 10, oracle_model: str = None) -> bool:
        """Summarizes older context into a single node if the token limit is exceeded."""
        context = self.get_llm_context()
        
        from hummcode.llm import LLMClient  # Local import prevents circular dependency
        oracle_llm = LLMClient()
        
        # Safely determine the model to use for summarization
        import os
        target_model = oracle_model or os.getenv("ORACLE_MODEL", oracle_llm.default_model)
        
        # 1. Check if we actually need to compact
        try:
            current_tokens = litellm.token_counter(model=target_model, messages=context)
        except Exception:
            current_tokens = sum(len(str(m.get("content", ""))) // 4 for m in context)

        if current_tokens <= max_tokens or len(context) <= window_size:
            return False # No compaction needed

        # 2. Split context: what to summarize vs. recent sliding window to keep
        old_context = context[:-window_size]
        
        summary_prompt = "Summarize the following previous conversation and tool executions briefly but retain key facts, file paths, and context:\n\n"
        for msg in old_context:
            summary_prompt += f"{msg.get('role', 'system')}: {str(msg.get('content', ''))[:1000]}...\n"

        # 3. Call the model to generate the summary
        response = oracle_llm.generate(
            messages=[{"role": "user", "content": summary_prompt}],
            model=target_model
        )
        summary_text = f"Summary of earlier conversation: {response.content}"

        # 4. Create the new Summary Node
        summary_node = Node(data={"role": "system", "content": summary_text}, parent_id=None)
        self.nodes[summary_node.id] = summary_node

        # 5. Link the oldest node in our sliding window to this new summary node
        curr_id = self.current_leaf_id
        for _ in range(window_size - 1):
            if curr_id and curr_id in self.nodes:
                curr_id = self.nodes[curr_id].parent_id
                
        if curr_id and curr_id in self.nodes:
            self.nodes[curr_id].parent_id = summary_node.id

        return True
