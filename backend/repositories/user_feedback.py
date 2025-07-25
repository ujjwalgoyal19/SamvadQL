"""User feedback repository implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from uuid import UUID

from models import UserFeedback
from repositories.base import BaseRepository


class UserFeedbackRepository(BaseRepository[UserFeedback]):
    """Repository for user feedback operations."""

    def get_table_name(self) -> str:
        return "user_feedback"

    def to_dict(self, entity: UserFeedback) -> Dict[str, Any]:
        """Convert UserFeedback to dictionary."""
        return {
            "id": entity.id,
            "user_id": entity.user_id,
            "query_id": entity.query_id,
            "original_query": entity.original_query,
            "generated_sql": entity.generated_sql,
            "feedback_type": entity.feedback_type,
            "comments": entity.comments,
            "rating": entity.rating,
            "created_at": entity.created_at,
        }

    def from_dict(self, data: Dict[str, Any]) -> UserFeedback:
        """Convert dictionary to UserFeedback."""
        return UserFeedback(
            id=str(data["id"]),
            user_id=data["user_id"],
            query_id=str(data["query_id"]),
            original_query=data["original_query"],
            generated_sql=data["generated_sql"],
            feedback_type=data["feedback_type"],
            comments=data.get("comments"),
            rating=data.get("rating"),
            created_at=data["created_at"],
        )

    async def get_by_user_id(
        self, user_id: str, limit: Optional[int] = None
    ) -> List[UserFeedback]:
        """Get feedback by user ID."""
        return await self.find_by(
            filters={"user_id": user_id}, limit=limit, order_by="created_at DESC"
        )

    async def get_by_query_id(self, query_id: str) -> List[UserFeedback]:
        """Get feedback by query ID."""
        return await self.find_by(
            filters={"query_id": query_id}, order_by="created_at DESC"
        )

    async def get_feedback_stats(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get feedback statistics."""
        db_manager = await self.get_db_manager()

        where_clause = ""
        params = []

        if start_date or end_date:
            conditions = []
            if start_date:
                conditions.append(f"created_at >= ${len(params) + 1}")
                params.append(start_date)
            if end_date:
                conditions.append(f"created_at <= ${len(params) + 1}")
                params.append(end_date)
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT
                feedback_type,
                COUNT(*) as count,
                AVG(rating) as avg_rating
            FROM {self.table_name}
            {where_clause}
            GROUP BY feedback_type
        """

        try:
            async with db_manager.get_connection() as connection:
                rows = await connection.fetch(query, *params)
                return {
                    row["feedback_type"]: {
                        "count": row["count"],
                        "avg_rating": (
                            float(row["avg_rating"]) if row["avg_rating"] else None
                        ),
                    }
                    for row in rows
                }
        except Exception as e:
            raise Exception(f"Error getting feedback stats: {e}")

    async def get_recent_feedback(
        self, days: int = 7, limit: int = 100
    ) -> List[UserFeedback]:
        """Get recent feedback within specified days."""
        db_manager = await self.get_db_manager()

        query = f"""
            SELECT * FROM {self.table_name}
            WHERE created_at >= NOW() - INTERVAL '{days} days'
            ORDER BY created_at DESC
            LIMIT {limit}
        """

        try:
            async with db_manager.get_connection() as connection:
                rows = await connection.fetch(query)
                return [self.from_dict(dict(row)) for row in rows]
        except Exception as e:
            raise Exception(f"Error getting recent feedback: {e}")
