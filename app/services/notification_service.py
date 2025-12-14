"""Notification service for sending scheduled notifications."""
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import (
    InterviewRepository,
    NotificationSettingsRepository,
    NotificationLogRepository,
)
from app.database.models import Interview
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
    
    async def check_and_send_notifications(self) -> None:
        """Check for interviews and send notifications if needed."""
        try:
            interviews = await self.interview_repo.get_upcoming_interviews()
            
            for interview in interviews:
                await self._process_interview_notifications(interview)
                
        except Exception as e:
            logger.error(f"Ошибка проверки и отправки уведомления: {e}")
    
    async def _process_interview_notifications(self, interview: Interview) -> None:
        """Process notifications for a single interview."""
        try:
            # Get user's notification settings
            settings = await self.notification_settings_repo.get_by_user_id(
                interview.user_id
            )
            
            if not settings or not settings.enabled:
                return
            
            # Check each notification time
            for hours_before in settings.notification_times:
                await self._send_notification_if_needed(
                    interview,
                    hours_before,
                )
                
        except Exception as e:
            logger.error(
                f"Ошибка обработки уведомления для интервью {interview.id}: {e}"
            )
    
    async def _send_notification_if_needed(
        self,
        interview: Interview,
        hours_before: float,
    ) -> None:
        """Send notification if the time has come and it wasn't sent yet."""
        try:
            # Check if already sent
            was_sent = await self.notification_log_repo.was_sent(
                interview.id,
                hours_before,
            )
            
            if was_sent:
                return
            
            # Calculate notification time
            notification_time = interview.interview_date - timedelta(hours=hours_before)
            now = datetime.utcnow()
            
            # Check if it's time to send (with 1 minute tolerance)
            time_diff = (now - notification_time).total_seconds()
            
            if -60 <= time_diff <= 60:  # Within 1 minute window
                await self._send_notification(interview, hours_before)
                
        except Exception as e:
            logger.error(
                f"Ошибка отправки уведомления для интервью {interview.id}: {e}"
            )
    
    async def _send_notification(
        self,
        interview: Interview,
        hours_before: float,
    ) -> None:
        """Send notification to user."""
        try:
            # Format time remaining
            time_text = self._format_time_remaining(hours_before)
            
            # Build notification message
            message = self._build_notification_message(interview, time_text)
            
            # Send message
            await self.bot.send_message(
                chat_id=interview.user.telegram_id,
                text=message,
                parse_mode="HTML",
            )
            
            # Log successful notification
            await self.notification_log_repo.create(
                interview_id=interview.id,
                notification_time_hours=hours_before,
                success=True,
            )
            
            logger.info(
                f"Уведомление отправлено для интервью {interview.id} "
                f"({hours_before}h before)"
            )
            
        except Exception as e:
            # Log failed notification
            await self.notification_log_repo.create(
                interview_id=interview.id,
                notification_time_hours=hours_before,
                success=False,
            )
            logger.error(f"Ошибка отправки уведомление: {e}")
    
    @staticmethod
    def _format_time_remaining(hours: float) -> str:
        """Format time remaining text."""
        if hours >= 24:
            days = int(hours / 24)
            return f"{days} дн." if days > 1 else "1 день"
        elif hours >= 1:
            return f"{int(hours)} ч."
        else:
            minutes = int(hours * 60)
            return f"{minutes} мин."
    
    @staticmethod
    def _build_notification_message(interview: Interview, time_text: str) -> str:
        """Build notification message."""
        camera_text = "✅ Да" if interview.camera_required else "❌ Нет"
        
        message = [
            f"🔔 <b>Напоминание о собеседовании!</b>",
            f"⏰ Через {time_text}\n",
            f"🏢 <b>Компания:</b> {interview.company}",
            f"💼 <b>Позиция:</b> {interview.position}",
            f"👤 <b>Рекрутер:</b> {interview.recruiter_name}",
            f"📅 <b>Дата и время:</b> {interview.interview_date.strftime('%d.%m.%Y %H:%M')}",
            f"💻 <b>Платформа:</b> {interview.platform_name}",
        ]
        
        if interview.platform_url:
            message.append(f"🔗 <b>Ссылка:</b> {interview.platform_url}")
        
        message.extend([
            f"📹 <b>Камера:</b> {camera_text}",
            f"📝 <b>Тип:</b> {interview.interview_type.value}",
        ])
        
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
        }
    
    async def toggle_notifications(self, telegram_id: int) -> bool:
        """Toggle notifications on/off."""
        from app.database.repositories import UserRepository
        
        user_repo = UserRepository(self.session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        
        if not user:
            raise ValueError("Пользователь не найден")
        
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
            raise ValueError("Пользователь не найден")
        
        await self.notification_settings_repo.update_times(user.id, times)