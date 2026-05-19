import uuid
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
            
        return context[::-1]  # Reverse so it goes Root -> Leaf (oldest to newest)

    def rewind(self, node_id: str):
        """Moves the active pointer back to an older node, abandoning bad branches."""
        if node_id in self.nodes:
            self.current_leaf_id = node_id
        else:
            raise ValueError(f"Node {node_id} not found in memory.")
