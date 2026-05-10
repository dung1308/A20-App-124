from collections import deque
from typing import Dict, List

class ShortTermMemory:
    def __init__(self, max_turns=10):
        self.max_turns = max_turns
        self.memory: Dict[str, deque] = {}

    def add_message(self, user_id: str, role: str, content: str):
        if user_id not in self.memory:
            self.memory[user_id] = deque(maxlen=self.max_turns)

        self.memory[user_id].append({
            "role": role,
            "content": content
        })

    def get_context(self, user_id: str) -> List[dict]:
        return list(self.memory.get(user_id, []))

    def clear(self, user_id: str):
        if user_id in self.memory:
            del self.memory[user_id]