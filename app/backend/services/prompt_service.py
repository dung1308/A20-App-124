import os
from typing import Optional
from services.db_service import DBService
from utils.logger import get_logger

logger = get_logger(__name__)

class PromptService:
    """
    Quản lý nạp các phiên bản prompt từ file hệ thống.
    """
    def __init__(self):
        self.db = DBService()

    def get_prompt(self, agent_name: str, version: str = "latest") -> str:
        """
        Lấy prompt từ database.
        """
        try:
            content = self.db.get_prompt_from_db(agent_name, version)
            
            if content:
                return content

            # Fallback: Nếu DB trống (lần đầu setup), hãy thử đọc từ file local v1
            # Điều này giúp hệ thống không bị crash khi mới deploy.
            local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", f"{agent_name}_v1.txt")
            if os.path.exists(local_path):
                with open(local_path, "r", encoding="utf-8") as f:
                    fallback_content = f.read().strip()
                    # Tự động nạp vào DB để lần sau lấy nhanh hơn
                    self.save_prompt(agent_name, "v1", fallback_content)
                    return fallback_content

            logger.error(
                f"No prompt found for {agent_name} (version: {version}). "
                f"Checked DB and local path: {os.path.abspath(local_path)}"
            )
            return ""
        except Exception as e:
            logger.error(f"Error loading prompt for {agent_name}: {e}")
            return ""

    def save_prompt(self, agent_name: str, version: str, content: str):
        """Lưu prompt mới vào PostgreSQL."""
        if self.db.save_prompt_to_db(agent_name, version, content):
            logger.info(f"Successfully saved {agent_name} version {version} to DB.")