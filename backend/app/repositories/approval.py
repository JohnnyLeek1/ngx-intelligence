"""
Approval queue repository for approval workflow operations.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ApprovalQueue, ApprovalStatus
from app.repositories.base import SQLAlchemyRepository


class ApprovalRepository(SQLAlchemyRepository[ApprovalQueue]):
    """Repository for ApprovalQueue model operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ApprovalQueue, session)

    async def get_pending_approvals(
        self, user_id: UUID, limit: Optional[int] = None
    ) -> List[ApprovalQueue]:
        """
        Get pending approvals for a user.

        Args:
            user_id: User UUID
            limit: Optional limit on results

        Returns:
            List of pending approvals
        """
        return await self.list(
            filters={"user_id": user_id, "status": ApprovalStatus.PENDING},
            limit=limit,
            order_by="-created_at",
        )

    async def approve(
        self, approval_id: UUID, feedback: Optional[str] = None
    ) -> Optional[ApprovalQueue]:
        """
        Approve a suggestion.

        Args:
            approval_id: Approval queue item UUID
            feedback: Optional user feedback

        Returns:
            Updated approval item or None
        """
        item = await self.get_by_id(approval_id)
        if item:
            item.status = ApprovalStatus.APPROVED
            item.approved_at = datetime.utcnow()
            if feedback:
                item.feedback = feedback
            return await self.update(item)
        return None

    async def reject(
        self, approval_id: UUID, feedback: Optional[str] = None
    ) -> Optional[ApprovalQueue]:
        """
        Reject a suggestion.

        Args:
            approval_id: Approval queue item UUID
            feedback: Optional user feedback

        Returns:
            Updated approval item or None
        """
        item = await self.get_by_id(approval_id)
        if item:
            item.status = ApprovalStatus.REJECTED
            item.approved_at = datetime.utcnow()
            if feedback:
                item.feedback = feedback
            return await self.update(item)
        return None

    async def get_approval_stats(self, user_id: UUID) -> dict:
        """
        Get approval statistics for a user.

        Args:
            user_id: User UUID

        Returns:
            Dictionary with approval statistics
        """
        pending = await self.count(
            {"user_id": user_id, "status": ApprovalStatus.PENDING}
        )
        approved = await self.count(
            {"user_id": user_id, "status": ApprovalStatus.APPROVED}
        )
        rejected = await self.count(
            {"user_id": user_id, "status": ApprovalStatus.REJECTED}
        )

        total = pending + approved + rejected
        approval_rate = (approved / (approved + rejected) * 100) if (approved + rejected) > 0 else 0

        return {
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "total": total,
            "approval_rate": approval_rate,
        }
