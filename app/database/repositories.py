"""Data access layer - repositories."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import (
    User,
    Interview,
    NotificationSettings,
    NotificationLog,
    InterviewType,
)
from app.config import settings


class UserRepository:
    """Repository for User operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram ID."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, telegram_id: int, username: Optional[str] = None) -> User:
        """Create new user."""
        user = User(telegram_id=telegram_id, username=username)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
    ) -> User:
        """Get or create user."""
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            user = await self.create(telegram_id, username)
        return user


class InterviewRepository:
    """Repository for Interview operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        user_id: int,
        company: str,
        position: str,
        vacancy_url: Optional[str],
        recruiter_name: str,
        interview_date: datetime,
        platform_name: str,
        platform_url: Optional[str],
        camera_required: bool,
        interview_type: InterviewType,
    ) -> Interview:
        """Create new interview."""
        interview = Interview(
            user_id=user_id,
            company=company,
            position=position,
            vacancy_url=vacancy_url,
            recruiter_name=recruiter_name,
            interview_date=interview_date,
            platform_name=platform_name,
            platform_url=platform_url,
            camera_required=camera_required,
            interview_type=interview_type,
        )
        self.session.add(interview)
        await self.session.commit()
        await self.session.refresh(interview)
        return interview
    
    async def get_by_id(self, interview_id: int) -> Optional[Interview]:
        """Get interview by ID."""
        result = await self.session.execute(
            select(Interview)
            .options(selectinload(Interview.user))
            .where(Interview.id == interview_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_interviews(
        self,
        user_id: int,
        include_past: bool = False,
    ) -> List[Interview]:
        """Get all user's interviews."""
        query = select(Interview).where(Interview.user_id == user_id)
        
        if not include_past:
            query = query.where(Interview.interview_date >= datetime.utcnow())
        
        query = query.order_by(Interview.interview_date)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_upcoming_interviews(self) -> List[Interview]:
        """Get all upcoming interviews."""
        result = await self.session.execute(
            select(Interview)
            .options(selectinload(Interview.user))
            .where(Interview.interview_date >= datetime.utcnow())
            .order_by(Interview.interview_date)
        )
        return list(result.scalars().all())
    
    async def delete(self, interview_id: int) -> bool:
        """Delete interview."""
        result = await self.session.execute(
            delete(Interview).where(Interview.id == interview_id)
        )
        await self.session.commit()
        return result.rowcount > 0


class NotificationSettingsRepository:
    """Repository for NotificationSettings operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_user_id(self, user_id: int) -> Optional[NotificationSettings]:
        """Get notification settings by user ID."""
        result = await self.session.execute(
            select(NotificationSettings).where(
                NotificationSettings.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
    
    async def create_default(self, user_id: int) -> NotificationSettings:
        """Create default notification settings."""
        notification_settings = NotificationSettings(
            user_id=user_id,
            notification_times=settings.default_notification_times,
            enabled=True,
        )
        self.session.add(notification_settings)
        await self.session.commit()
        await self.session.refresh(notification_settings)
        return notification_settings
    
    async def get_or_create(self, user_id: int) -> NotificationSettings:
        """Get or create notification settings."""
        notification_settings = await self.get_by_user_id(user_id)
        if not notification_settings:
            notification_settings = await self.create_default(user_id)
        return notification_settings
    
    async def update_times(
        self,
        user_id: int,
        notification_times: List[float],
    ) -> NotificationSettings:
        """Update notification times."""
        notification_settings = await self.get_or_create(user_id)
        notification_settings.notification_times = notification_times
        await self.session.commit()
        await self.session.refresh(notification_settings)
        return notification_settings
    
    async def toggle_enabled(self, user_id: int) -> NotificationSettings:
        """Toggle notifications enabled/disabled."""
        notification_settings = await self.get_or_create(user_id)
        notification_settings.enabled = not notification_settings.enabled
        await self.session.commit()
        await self.session.refresh(notification_settings)
        return notification_settings


class NotificationLogRepository:
    """Repository for NotificationLog operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        interview_id: int,
        notification_time_hours: float,
        success: bool = True,
    ) -> NotificationLog:
        """Create notification log."""
        log = NotificationLog(
            interview_id=interview_id,
            notification_time_hours=notification_time_hours,
            success=success,
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log
    
    async def was_sent(
        self,
        interview_id: int,
        notification_time_hours: float,
    ) -> bool:
        """Check if notification was already sent."""
        result = await self.session.execute(
            select(NotificationLog).where(
                and_(
                    NotificationLog.interview_id == interview_id,
                    NotificationLog.notification_time_hours == notification_time_hours,
                    NotificationLog.success == True,
                )
            )
        )
        return result.scalar_one_or_none() is not None