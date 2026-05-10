"""
services/memory_manager.py
--------------------------
Centralized short-term memory handling.
"""

from typing import List, Dict, Any


class MemoryManager:

    def build_context(
        self,
        message: str,
        history: List[Dict[str, Any]] = None,
    ) -> str:

        if not history:
            return message

        history_lines = []

        # chỉ lấy 6 turns gần nhất
        for msg in history[-6:]:

            role = msg.get("role", "user")
            content = msg.get("content", "")

            if not content:
                continue

            history_lines.append(
                f"{role}: {content}"
            )

        history_text = "\n".join(history_lines)

        enhanced_message = f"""
Conversation History:
{history_text}

Current User Message:
{message}
""".strip()

        return enhanced_message