"""Data access layer - repositories."""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, delete, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.database.models import (
    User,
    Interview,
    InterviewStatusHistory,
    NotificationSettings,
    NotificationLog,
    InterviewType,
    InterviewStatus,
    FollowUp,
    Company,
    Recruiter,
    InterviewTemplate,
    Backup,
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
    
    async def update_locale(self, user_id: int, locale: str) -> User:
        """Update user locale."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one()
        user.locale = locale
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update_timezone(self, user_id: int, timezone: str) -> User:
        """Update user timezone."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one()
        user.timezone = timezone
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_all_users(self) -> List[User]:
        """Get all users."""
        result = await self.session.execute(select(User))
        return list(result.scalars().all())


class CompanyRepository:
    """Repository for Company operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_or_create(
        self,
        user_id: int,
        name: str,
        website: Optional[str] = None,
    ) -> Company:
        """Get or create company."""
        result = await self.session.execute(
            select(Company).where(
                and_(
                    Company.user_id == user_id,
                    Company.name == name,
                )
            )
        )
        company = result.scalar_one_or_none()
        
        if not company:
            company = Company(
                user_id=user_id,
                name=name,
                website=website,
            )
            self.session.add(company)
            await self.session.commit()
            await self.session.refresh(company)
        
        return company
    
    async def get_user_companies(self, user_id: int) -> List[Company]:
        """Get all user's companies."""
        result = await self.session.execute(
            select(Company)
            .where(Company.user_id == user_id)
            .order_by(Company.name)
        )
        return list(result.scalars().all())


class RecruiterRepository:
    """Repository for Recruiter operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        user_id: int,
        name: str,
        company_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        telegram: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Recruiter:
        """Create recruiter."""
        recruiter = Recruiter(
            user_id=user_id,
            name=name,
            company_name=company_name,
            email=email,
            phone=phone,
            telegram=telegram,
            notes=notes,
        )
        self.session.add(recruiter)
        await self.session.commit()
        await self.session.refresh(recruiter)
        return recruiter
    
    async def get_by_id(self, recruiter_id: int) -> Optional[Recruiter]:
        """Get recruiter by ID."""
        result = await self.session.execute(
            select(Recruiter).where(Recruiter.id == recruiter_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_recruiters(self, user_id: int) -> List[Recruiter]:
        """Get all user's recruiters."""
        result = await self.session.execute(
            select(Recruiter)
            .where(Recruiter.user_id == user_id)
            .order_by(Recruiter.name)
        )
        return list(result.scalars().all())
    
    async def search_by_name(self, user_id: int, query: str) -> List[Recruiter]:
        """Search recruiters by name."""
        result = await self.session.execute(
            select(Recruiter)
            .where(
                and_(
                    Recruiter.user_id == user_id,
                    Recruiter.name.ilike(f"%{query}%"),
                )
            )
            .order_by(Recruiter.name)
        )
        return list(result.scalars().all())
    
    async def delete(self, recruiter_id: int) -> bool:
        """Delete recruiter."""
        result = await self.session.execute(
            delete(Recruiter).where(Recruiter.id == recruiter_id)
        )
        await self.session.commit()
        return result.rowcount > 0


class InterviewRepository:
    """Repository for Interview operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        user_id: int,
        company_name: str,
        position: str,
        vacancy_url: Optional[str],
        recruiter_name: str,
        interview_date: datetime,
        platform_name: str,
        platform_url: Optional[str],
        camera_required: bool,
        interview_type: InterviewType,
        company_id: Optional[int] = None,
        recruiter_id: Optional[int] = None,
        parent_interview_id: Optional[int] = None,
        preparation_notes: Optional[str] = None,
        checklist: Optional[List[dict]] = None,
    ) -> Interview:
        """Create new interview."""
        interview = Interview(
            user_id=user_id,
            company_id=company_id,
            recruiter_id=recruiter_id,
            parent_interview_id=parent_interview_id,
            company_name=company_name,
            position=position,
            vacancy_url=vacancy_url,
            recruiter_name=recruiter_name,
            interview_date=interview_date,
            platform_name=platform_name,
            platform_url=platform_url,
            camera_required=camera_required,
            interview_type=interview_type,
            preparation_notes=preparation_notes,
            checklist=checklist,
        )
        self.session.add(interview)
        await self.session.commit()
        await self.session.refresh(interview)
        return interview
    
    async def get_by_id(self, interview_id: int) -> Optional[Interview]:
        """Get interview by ID."""
        result = await self.session.execute(
            select(Interview)
            .options(
                selectinload(Interview.user),
                selectinload(Interview.company),
                selectinload(Interview.recruiter),
                selectinload(Interview.status_history),
            )
            .where(Interview.id == interview_id)
        )
        return result.scalar_one_or_none()
    
    async def update(self, interview_id: int, **kwargs) -> Optional[Interview]:
        """Update interview."""
        result = await self.session.execute(
            select(Interview).where(Interview.id == interview_id)
        )
        interview = result.scalar_one_or_none()
        
        if interview:
            for key, value in kwargs.items():
                if hasattr(interview, key):
                    setattr(interview, key, value)
            
            interview.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(interview)
        
        return interview
    
    async def get_user_interviews(
        self,
        user_id: int,
        include_past: bool = False,
        status: Optional[InterviewStatus] = None,
        limit: Optional[int] = None,
    ) -> List[Interview]:
        """Get all user's interviews."""
        query = select(Interview).where(Interview.user_id == user_id)
        
        if not include_past:
            query = query.where(Interview.interview_date >= datetime.utcnow())
        
        if status:
            query = query.where(Interview.status == status)
        
        query = query.order_by(Interview.interview_date)
        
        if limit:
            query = query.limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_upcoming_interviews(self) -> List[Interview]:
        """Get all upcoming interviews."""
        result = await self.session.execute(
            select(Interview)
            .options(selectinload(Interview.user))
            .where(
                and_(
                    Interview.interview_date >= datetime.utcnow(),
                    Interview.status == InterviewStatus.SCHEDULED,
                )
            )
            .order_by(Interview.interview_date)
        )
        return list(result.scalars().all())
    
    async def search(
        self,
        user_id: int,
        query: str,
    ) -> List[Interview]:
        """Search interviews."""
        result = await self.session.execute(
            select(Interview)
            .where(
                and_(
                    Interview.user_id == user_id,
                    or_(
                        Interview.company_name.ilike(f"%{query}%"),
                        Interview.position.ilike(f"%{query}%"),
                        Interview.recruiter_name.ilike(f"%{query}%"),
                    ),
                )
            )
            .order_by(Interview.interview_date.desc())
        )
        return list(result.scalars().all())
    
    async def get_by_company(self, user_id: int, company_name: str) -> List[Interview]:
        """Get interviews by company."""
        result = await self.session.execute(
            select(Interview)
            .where(
                and_(
                    Interview.user_id == user_id,
                    Interview.company_name == company_name,
                )
            )
            .order_by(Interview.interview_date)
        )
        return list(result.scalars().all())
    
    async def get_pipeline(self, parent_interview_id: int) -> List[Interview]:
        """Get interview pipeline (all stages)."""
        result = await self.session.execute(
            select(Interview)
            .where(
                or_(
                    Interview.id == parent_interview_id,
                    Interview.parent_interview_id == parent_interview_id,
                )
            )
            .order_by(Interview.stage_number)
        )
        return list(result.scalars().all())
    
    async def delete(self, interview_id: int) -> bool:
        """Delete interview."""
        result = await self.session.execute(
            delete(Interview).where(Interview.id == interview_id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def get_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user statistics."""
        # Total count
        total_result = await self.session.execute(
            select(func.count(Interview.id)).where(Interview.user_id == user_id)
        )
        total = total_result.scalar()
        
        # By status
        status_result = await self.session.execute(
            select(
                Interview.status,
                func.count(Interview.id)
            )
            .where(Interview.user_id == user_id)
            .group_by(Interview.status)
        )
        by_status = {status.value: count for status, count in status_result.all()}
        
        # By type
        type_result = await self.session.execute(
            select(
                Interview.interview_type,
                func.count(Interview.id)
            )
            .where(Interview.user_id == user_id)
            .group_by(Interview.interview_type)
        )
        by_type = {itype.value: count for itype, count in type_result.all()}
        
        # Success rate
        completed = by_status.get(InterviewStatus.COMPLETED.value, 0)
        offers = by_status.get(InterviewStatus.OFFER.value, 0)
        rejected = by_status.get(InterviewStatus.REJECTED.value, 0)
        
        success_rate = 0
        if completed + offers + rejected > 0:
            success_rate = (offers / (completed + offers + rejected)) * 100
        
        return {
            "total": total,
            "by_status": by_status,
            "by_type": by_type,
            "success_rate": round(success_rate, 1),
        }


class InterviewStatusHistoryRepository:
    """Repository for status history."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        interview_id: int,
        old_status: Optional[InterviewStatus],
        new_status: InterviewStatus,
        notes: Optional[str] = None,
    ) -> InterviewStatusHistory:
        """Create status history record."""
        history = InterviewStatusHistory(
            interview_id=interview_id,
            old_status=old_status,
            new_status=new_status,
            notes=notes,
        )
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        return history
    
    async def get_interview_history(
        self,
        interview_id: int,
    ) -> List[InterviewStatusHistory]:
        """Get interview status history."""
        result = await self.session.execute(
            select(InterviewStatusHistory)
            .where(InterviewStatusHistory.interview_id == interview_id)
            .order_by(InterviewStatusHistory.changed_at)
        )
        return list(result.scalars().all())


class FollowUpRepository:
    """Repository for follow-ups."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        interview_id: int,
        reminder_date: datetime,
        message: str,
    ) -> FollowUp:
        """Create follow-up reminder."""
        followup = FollowUp(
            interview_id=interview_id,
            reminder_date=reminder_date,
            message=message,
        )
        self.session.add(followup)
        await self.session.commit()
        await self.session.refresh(followup)
        return followup
    
    async def get_pending(self) -> List[FollowUp]:
        """Get pending follow-ups."""
        result = await self.session.execute(
            select(FollowUp)
            .options(
                selectinload(FollowUp.interview).selectinload(Interview.user)
            )
            .where(
                and_(
                    FollowUp.sent == False,
                    FollowUp.reminder_date <= datetime.utcnow(),
                )
            )
            .order_by(FollowUp.reminder_date)
        )
        return list(result.scalars().all())
    
    async def mark_sent(self, followup_id: int) -> bool:
        """Mark follow-up as sent."""
        result = await self.session.execute(
            select(FollowUp).where(FollowUp.id == followup_id)
        )
        followup = result.scalar_one_or_none()
        
        if followup:
            followup.sent = True
            await self.session.commit()
            return True
        
        return False
    
    async def delete(self, followup_id: int) -> bool:
        """Delete follow-up."""
        result = await self.session.execute(
            delete(FollowUp).where(FollowUp.id == followup_id)
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
    
    async def set_quiet_hours(
        self,
        user_id: int,
        enabled: bool,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> NotificationSettings:
        """Set quiet hours."""
        notification_settings = await self.get_or_create(user_id)
        notification_settings.quiet_hours_enabled = enabled
        notification_settings.quiet_hours_start = start
        notification_settings.quiet_hours_end = end
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
        notification_type: str,
        notification_time_hours: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> NotificationLog:
        """Create notification log."""
        log = NotificationLog(
            interview_id=interview_id,
            notification_type=notification_type,
            notification_time_hours=notification_time_hours,
            success=success,
            error_message=error_message,
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


class TemplateRepository:
    """Repository for interview templates."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        user_id: int,
        name: str,
        platform_name: str,
        platform_url: Optional[str],
        camera_required: bool,
        interview_type: InterviewType,
        default_checklist: Optional[List[dict]] = None,
    ) -> InterviewTemplate:
        """Create template."""
        template = InterviewTemplate(
            user_id=user_id,
            name=name,
            platform_name=platform_name,
            platform_url=platform_url,
            camera_required=camera_required,
            interview_type=interview_type,
            default_checklist=default_checklist,
        )
        self.session.add(template)
        await self.session.commit()
        await self.session.refresh(template)
        return template
    
    async def get_user_templates(self, user_id: int) -> List[InterviewTemplate]:
        """Get user templates."""
        result = await self.session.execute(
            select(InterviewTemplate)
            .where(InterviewTemplate.user_id == user_id)
            .order_by(InterviewTemplate.name)
        )
        return list(result.scalars().all())
    
    async def get_by_id(self, template_id: int) -> Optional[InterviewTemplate]:
        """Get template by ID."""
        result = await self.session.execute(
            select(InterviewTemplate).where(InterviewTemplate.id == template_id)
        )
        return result.scalar_one_or_none()
    
    async def delete(self, template_id: int) -> bool:
        """Delete template."""
        result = await self.session.execute(
            delete(InterviewTemplate).where(InterviewTemplate.id == template_id)
        )
        await self.session.commit()
        return result.rowcount > 0


class BackupRepository:
    """Repository for backups."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        filename: str,
        filepath: str,
        size_bytes: int,
    ) -> Backup:
        """Create backup record."""
        backup = Backup(
            filename=filename,
            filepath=filepath,
            size_bytes=size_bytes,
        )
        self.session.add(backup)
        await self.session.commit()
        await self.session.refresh(backup)
        return backup
    
    async def get_all(self) -> List[Backup]:
        """Get all backups."""
        result = await self.session.execute(
            select(Backup).order_by(desc(Backup.created_at))
        )
        return list(result.scalars().all())
    
    async def delete_old(self, days: int = 30) -> int:
        """Delete old backups."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            delete(Backup).where(Backup.created_at < cutoff_date)
        )
        await self.session.commit()
        return result.rowcount