"""Notification service for sending scheduled notifications."""
from datetime import datetime, timedelta, time as dt_time
from typing import List, Optional
import logging
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import (
    InterviewRepository,
    NotificationSettingsRepository,
    NotificationLogRepository,
    FollowUpRepository,
)
from app.database.models import Interview, FollowUp
from app.services.interview_service import InterviewService

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications."""
    
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.interview_repo = InterviewRepository(session)
        self.notification_settings_repo = NotificationSettingsRepository(session)
        self.notification_log_repo = NotificationLogRepository(session)
        self.followup_repo = FollowUpRepository(session)
    
    async def check_and_send_notifications(self) -> None:
        """Check for interviews and send notifications if needed."""
        try:
            # Check interview notifications
            interviews = await self.interview_repo.get_upcoming_interviews()
            for interview in interviews:
                await self._process_interview_notifications(interview)
            
            # Check follow-up reminders
            await self._process_followup_notifications()
                
        except Exception as e:
            logger.error(f"Ошибка в check_and_send_notifications: {e}")
    
    async def _process_interview_notifications(self, interview: Interview) -> None:
        """Process notifications for a single interview."""
        try:
            settings = await self.notification_settings_repo.get_by_user_id(
                interview.user_id
            )
            
            if not settings or not settings.enabled:
                return
            
            # Check quiet hours
            if settings.quiet_hours_enabled:
                if self._is_quiet_hours(settings.quiet_hours_start, settings.quiet_hours_end):
                    return
            
            # Check each notification time
            for hours_before in settings.notification_times:
                await self._send_notification_if_needed(
                    interview,
                    hours_before,
                )
                
        except Exception as e:
            logger.error(
                f"Ошибка обработки уведомлений для собеседования {interview.id}: {e}"
            )
    
    async def _process_followup_notifications(self) -> None:
        """Process follow-up notifications."""
        try:
            followups = await self.followup_repo.get_pending()
            
            for followup in followups:
                await self._send_followup_notification(followup)
                
        except Exception as e:
            logger.error(f"Ошибка обработки follow-ups: {e}")
    
    async def _send_followup_notification(self, followup: FollowUp) -> None:
        """Send follow-up notification."""
        try:
            # Получаем timezone пользователя
            user_timezone = followup.interview.user.timezone if followup.interview.user else "Europe/Moscow"
            
            from app.utils.validators import TimezoneHelper
            date_str = TimezoneHelper.format_datetime(followup.interview.interview_date, user_timezone)
            
            message = [
                "🔔 <b>Напоминание!</b>\n",
                f"📝 {followup.message}",
                f"\n🏢 Компания: {followup.interview.company_name}",
                f"💼 Позиция: {followup.interview.position}",
                f"📅 Интервью было: {date_str}",
            ]
            
            await self.bot.send_message(
                chat_id=followup.interview.user.telegram_id,
                text="\n".join(message),
                parse_mode="HTML",
            )
            
            await self.followup_repo.mark_sent(followup.id)
            
            logger.info(f"Sent follow-up notification for interview {followup.interview_id}")
            
        except Exception as e:
            logger.error(f"Failed to send follow-up notification: {e}")
    
    @staticmethod
    def _is_quiet_hours(start: Optional[str], end: Optional[str]) -> bool:
        """Check if current time is in quiet hours."""
        if not start or not end:
            return False
        
        try:
            now = datetime.now().time()
            start_time = dt_time.fromisoformat(start)
            end_time = dt_time.fromisoformat(end)
            
            if start_time < end_time:
                return start_time <= now <= end_time
            else:  # Crosses midnight
                return now >= start_time or now <= end_time
                
        except Exception:
            return False
    
    async def _send_notification_if_needed(
        self,
        interview: Interview,
        hours_before: float,
    ) -> None:
        """Send notification if the time has come and it wasn't sent yet."""
        try:
            was_sent = await self.notification_log_repo.was_sent(
                interview.id,
                hours_before,
            )
            
            if was_sent:
                return
            
            notification_time = interview.interview_date - timedelta(hours=hours_before)
            now = datetime.utcnow()
            
            time_diff = (now - notification_time).total_seconds()
            
            if -60 <= time_diff <= 60:
                await self._send_notification(interview, hours_before)
                
        except Exception as e:
            logger.error(
                f"Ошибка отправки уведомления для собеседования {interview.id}: {e}"
            )
    
    async def _send_notification(
        self,
        interview: Interview,
        hours_before: float,
    ) -> None:
        """Send notification to user."""
        try:
            time_text = self._format_time_remaining(hours_before)
            
            # Получаем timezone пользователя
            user_timezone = interview.user.timezone if interview.user else "Europe/Moscow"
            
            message = self._build_notification_message(interview, time_text, user_timezone)
            
            await self.bot.send_message(
                chat_id=interview.user.telegram_id,
                text=message,
                parse_mode="HTML",
            )
            
            await self.notification_log_repo.create(
                interview_id=interview.id,
                notification_type="interview",
                notification_time_hours=hours_before,
                success=True,
            )
            
            logger.info(
                f"Sent notification for interview {interview.id} "
                f"({hours_before}h before)"
            )
            
        except Exception as e:
            await self.notification_log_repo.create(
                interview_id=interview.id,
                notification_type="interview",
                notification_time_hours=hours_before,
                success=False,
                error_message=str(e),
            )
            logger.error(f"Failed to send notification: {e}")
    
    @staticmethod
    def _format_time_remaining(hours: float) -> str:
        """Format time remaining text."""
        if hours >= 24:
            days = int(hours / 24)
            return f"{days} {'день' if days == 1 else 'дня' if days < 5 else 'дней'}"
        elif hours >= 1:
            return f"{int(hours)} {'час' if hours == 1 else 'часа' if hours < 5 else 'часов'}"
        else:
            minutes = int(hours * 60)
            return f"{minutes} {'минуту' if minutes == 1 else 'минуты' if minutes < 5 else 'минут'}"
    
    def _build_notification_message(self, interview: Interview, time_text: str, user_timezone: str = "Europe/Moscow") -> str:
        """Build notification message."""
        from app.utils.validators import TimezoneHelper
        
        camera_text = "✅ Да" if interview.camera_required else "❌ Нет"
        date_str = TimezoneHelper.format_datetime(interview.interview_date, user_timezone)
        
        message = [
            f"🔔 <b>Напоминание о собеседовании!</b>",
            f"⏰ Через {time_text}\n",
            f"🏢 <b>Компания:</b> {interview.company_name}",
            f"💼 <b>Позиция:</b> {interview.position}",
            f"👤 <b>Рекрутер:</b> {interview.recruiter_name}",
            f"📅 <b>Дата и время:</b> {date_str}",
            f"💻 <b>Платформа:</b> {interview.platform_name}",
        ]
        
        if interview.platform_url:
            message.append(f"🔗 <b>Ссылка:</b> {interview.platform_url}")
        
        message.extend([
            f"📹 <b>Камера:</b> {camera_text}",
            f"📝 <b>Тип:</b> {interview.interview_type.value}",
        ])
        
        # Add checklist reminder if close to interview
        if interview.checklist:
            unchecked = [item for item in interview.checklist if not item["checked"]]
            if unchecked:
                message.append(f"\n⚠️ <b>Не забудьте проверить чек-лист!</b>")
        
        return "\n".join(message)
    
    async def get_user_notification_settings(self, telegram_id: int) -> Optional[dict]:
        """Get user's notification settings."""
        from app.database.repositories import UserRepository
        
        user_repo = UserRepository(self.session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        
        if not user:
            return None
        
        settings = await self.notification_settings_repo.get_or_create(user.id)
        
        return {
            "enabled": settings.enabled,
            "times": settings.notification_times,
            "quiet_hours_enabled": settings.quiet_hours_enabled,
            "quiet_hours_start": settings.quiet_hours_start,
            "quiet_hours_end": settings.quiet_hours_end,
        }
    
    async def toggle_notifications(self, telegram_id: int) -> bool:
        """Toggle notifications on/off."""
        from app.database.repositories import UserRepository
        
        user_repo = UserRepository(self.session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        
        if not user:
            raise ValueError("User not found")
        
        settings = await self.notification_settings_repo.toggle_enabled(user.id)
        return settings.enabled
    
    async def update_notification_times(
        self,
        telegram_id: int,
        times: List[float],
    ) -> None:
        """Update notification times."""
        from app.database.repositories import UserRepository
        
        user_repo = UserRepository(self.session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        
        if not user:
            raise ValueError("User not found")
        
        await self.notification_settings_repo.update_times(user.id, times)
    
    async def set_quiet_hours(
        self,
        telegram_id: int,
        enabled: bool,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> None:
        """Set quiet hours."""
        from app.database.repositories import UserRepository
        
        user_repo = UserRepository(self.session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        
        if not user:
            raise ValueError("User not found")
        
        await self.notification_settings_repo.set_quiet_hours(
            user.id,
            enabled,
            start,
            end,
        )