"""
services/metric_service.py
--------------------------
Responsibility: Compute Product-Market Fit (PMF) and performance metrics 
from the AuditLog table.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy import func
from models.schemas import AuditLog
import database

logger = logging.getLogger(__name__)

class MetricService:
    """
    Service to aggregate and calculate system performance metrics 
    used for evaluating product-market fit.
    """

    def __init__(self, db_service):
        self.db_service = db_service

    def get_pmf_metrics(self, hours_back: int = 336) -> Dict[str, Any]:
        """
        Calculate metrics over a sliding window (default 2 weeks).
        """
        if self.db_service.use_mock:
            logger.info("MetricService: Returning mock metrics")
            return {
                "period_hours": hours_back,
                "total_requests": 150,
                "avg_response_time_ms": 1250,
                "ai_resolution_rate": 0.85,
                "human_fallback_rate": 0.10,
                "route_distribution": {"rag": 100, "crm": 30, "advisor": 15, "fallback": 5},
                "status": "mock_data"
            }

        since_date = datetime.utcnow() - timedelta(hours=hours_back)
        
        try:
            with database.SessionLocal() as session:
                # 1. Total Requests
                total = session.query(AuditLog).filter(AuditLog.timestamp >= since_date).count()
                if total == 0:
                    return {"message": "No data for the selected period", "total_requests": 0}

                # 2. Average Latency
                avg_latency = session.query(func.avg(AuditLog.response_time_ms))\
                    .filter(AuditLog.timestamp >= since_date).scalar() or 0

                # 3. AI Resolution Rate (where AI handled the query successfully)
                resolved_count = session.query(AuditLog)\
                    .filter(AuditLog.timestamp >= since_date, AuditLog.ai_resolved == True).count()
                
                # 4. Fallback Rate (escalation to humans)
                fallback_count = session.query(AuditLog)\
                    .filter(AuditLog.timestamp >= since_date, AuditLog.fallback == True).count()

                # 5. Route Distribution
                routes = session.query(AuditLog.route, func.count(AuditLog.id))\
                    .filter(AuditLog.timestamp >= since_date)\
                    .group_by(AuditLog.route).all()
                
                route_dist = {str(r): count for r, count in routes}

                return {
                    "period_hours": hours_back,
                    "total_requests": total,
                    "avg_response_time_ms": round(float(avg_latency), 2),
                    "ai_resolution_rate": round(resolved_count / total, 3),
                    "human_fallback_rate": round(fallback_count / total, 3),
                    "route_distribution": route_dist,
                    "generated_at": datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Error computing metrics: {e}")
            return {
                "error": "Failed to compute metrics",
                "details": str(e)
            }