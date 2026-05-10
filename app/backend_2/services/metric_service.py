"""
services/metric_service.py
--------------------------
Provides PMF-related metric calculations from audit logs and chat history.
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from services.db_service import DBService
from models.schemas import AuditLog, ChatMessage
from utils.logger import get_logger

logger = get_logger(__name__)


class MetricService:
    def __init__(self):
        self.db_service = DBService()
        self.use_mock = self.db_service.use_mock

    def _since(self, hours: int) -> datetime:
        return datetime.utcnow() - timedelta(hours=hours)

    def average_response_time(self, hours: int = 336) -> float:
        if self.use_mock:
            return 0.0

        since = self._since(hours)
        with self.db_service.SessionLocal() as session:
            rows = session.query(AuditLog.response_time_ms).filter(
                AuditLog.timestamp >= since,
                AuditLog.route == "chat",
            ).all()

            values = [r[0] for r in rows if r[0] is not None]
            if not values:
                return 0.0
            return sum(values) / len(values)

    def ai_resolution_rate(self, hours: int = 336) -> float:
        if self.use_mock:
            return 1.0

        since = self._since(hours)
        with self.db_service.SessionLocal() as session:
            total = session.query(AuditLog).filter(
                AuditLog.timestamp >= since,
                AuditLog.route == "chat",
            ).count()
            if total == 0:
                return 0.0
            resolved = session.query(AuditLog).filter(
                AuditLog.timestamp >= since,
                AuditLog.route == "chat",
                AuditLog.ai_resolved == True,
            ).count()
            return resolved / total

    def ai_no_followup_rate(self, hours: int = 336, followup_hours: int = 24) -> float:
        if self.use_mock:
            return 1.0

        since = self._since(hours)
        window = timedelta(hours=followup_hours)
        with self.db_service.SessionLocal() as session:
            successful_audits = session.query(AuditLog).filter(
                AuditLog.timestamp >= since,
                AuditLog.route == "chat",
                AuditLog.ai_resolved == True,
                AuditLog.fallback == False,
            ).all()

            if not successful_audits:
                return 0.0

            resolved_without_followup = 0
            for audit in successful_audits:
                followup = session.query(ChatMessage).filter(
                    ChatMessage.user_id == audit.user_id,
                    ChatMessage.role == "user",
                    ChatMessage.timestamp > audit.timestamp,
                    ChatMessage.timestamp <= audit.timestamp + window,
                ).order_by(ChatMessage.timestamp.asc()).first()
                if not followup:
                    resolved_without_followup += 1

            return resolved_without_followup / len(successful_audits)

    def get_pmf_metrics(self, hours: int = 336) -> Dict[str, Any]:
        return {
            "average_response_time_ms": self.average_response_time(hours=hours),
            "ai_resolution_rate": self.ai_resolution_rate(hours=hours),
            "ai_no_followup_rate": self.ai_no_followup_rate(hours=hours),
            "metric_window_hours": hours,
        }
