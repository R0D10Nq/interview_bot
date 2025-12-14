"""Business logic for interview management."""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.database.models import (
    Interview,
    InterviewType,
    InterviewStatus,
)
from app.database.repositories import (
    InterviewRepository,
    UserRepository,
    CompanyRepository,
    RecruiterRepository,
    InterviewStatusHistoryRepository,
    FollowUpRepository,
    TemplateRepository,
)
from app.config import settings


class InterviewService:
    """Service for interview management."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.interview_repo = InterviewRepository(session)
        self.user_repo = UserRepository(session)
        self.company_repo = CompanyRepository(session)
        self.recruiter_repo = RecruiterRepository(session)
        self.status_history_repo = InterviewStatusHistoryRepository(session)
        self.followup_repo = FollowUpRepository(session)
        self.template_repo = TemplateRepository(session)
    
    async def create_interview(
        self,
        telegram_id: int,
        company_name: str,
        position: str,
        vacancy_url: Optional[str],
        recruiter_name: str,
        interview_date: datetime,
        platform_name: str,
        platform_url: Optional[str],
        camera_required: bool,
        interview_type: InterviewType,
        preparation_notes: Optional[str] = None,
        parent_interview_id: Optional[int] = None,
    ) -> Interview:
        """Create new interview."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("User not found")
        
        # Get or create company
        company = await self.company_repo.get_or_create(
            user_id=user.id,
            name=company_name,
        )
        
        # Calculate stage number for pipeline
        stage_number = 1
        if parent_interview_id:
            pipeline = await self.interview_repo.get_pipeline(parent_interview_id)
            stage_number = len(pipeline) + 1
        
        # Create default checklist
        default_checklist = self._get_default_checklist(interview_type)
        
        interview = await self.interview_repo.create(
            user_id=user.id,
            company_id=company.id,
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
            parent_interview_id=parent_interview_id,
            checklist=default_checklist,
        )
        
        # Update stage number
        await self.interview_repo.update(interview.id, stage_number=stage_number)
        
        # Create status history
        await self.status_history_repo.create(
            interview_id=interview.id,
            old_status=None,
            new_status=InterviewStatus.SCHEDULED,
            notes="Интервью создано",
        )
        
        # Create default follow-up
        followup_date = interview_date + timedelta(days=settings.default_followup_days)
        await self.followup_repo.create(
            interview_id=interview.id,
            reminder_date=followup_date,
            message=f"Узнать результат интервью в {company_name}",
        )
        
        return interview
    
    async def create_from_template(
        self,
        telegram_id: int,
        template_id: int,
        company_name: str,
        position: str,
        recruiter_name: str,
        interview_date: datetime,
        vacancy_url: Optional[str] = None,
    ) -> Interview:
        """Create interview from template."""
        template = await self.template_repo.get_by_id(template_id)
        if not template:
            raise ValueError("Template not found")
        
        return await self.create_interview(
            telegram_id=telegram_id,
            company_name=company_name,
            position=position,
            vacancy_url=vacancy_url,
            recruiter_name=recruiter_name,
            interview_date=interview_date,
            platform_name=template.platform_name,
            platform_url=template.platform_url,
            camera_required=template.camera_required,
            interview_type=template.interview_type,
        )
    
    async def update_interview(
        self,
        interview_id: int,
        **kwargs,
    ) -> Optional[Interview]:
        """Update interview."""
        # If date is being changed, save original
        if "interview_date" in kwargs:
            interview = await self.interview_repo.get_by_id(interview_id)
            if interview and not interview.original_date:
                kwargs["original_date"] = interview.interview_date
        
        return await self.interview_repo.update(interview_id, **kwargs)
    
    async def change_status(
        self,
        interview_id: int,
        new_status: InterviewStatus,
        notes: Optional[str] = None,
    ) -> Interview:
        """Change interview status."""
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError("Interview not found")
        
        old_status = interview.status
        
        # Update status
        await self.interview_repo.update(interview_id, status=new_status)
        
        # If completed, set completed_at
        if new_status in [
            InterviewStatus.COMPLETED,
            InterviewStatus.OFFER,
            InterviewStatus.REJECTED,
        ]:
            await self.interview_repo.update(
                interview_id,
                completed_at=datetime.utcnow(),
            )
        
        # Create history record
        await self.status_history_repo.create(
            interview_id=interview_id,
            old_status=old_status,
            new_status=new_status,
            notes=notes,
        )
        
        # Get updated interview
        return await self.interview_repo.get_by_id(interview_id)
    
    async def update_checklist(
        self,
        interview_id: int,
        item_index: int,
        checked: bool,
    ) -> Interview:
        """Update checklist item."""
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview or not interview.checklist:
            raise ValueError("Interview or checklist not found")
        
        if 0 <= item_index < len(interview.checklist):
            interview.checklist[item_index]["checked"] = checked
            await self.interview_repo.update(
                interview_id,
                checklist=interview.checklist,
            )
        
        return await self.interview_repo.get_by_id(interview_id)
    
    async def add_checklist_item(
        self,
        interview_id: int,
        text: str,
    ) -> Interview:
        """Add checklist item."""
        interview = await self.interview_repo.get_by_id(interview_id)
        if not interview:
            raise ValueError("Interview not found")
        
        if not interview.checklist:
            interview.checklist = []
        
        interview.checklist.append({
            "text": text,
            "checked": False,
        })
        
        await self.interview_repo.update(
            interview_id,
            checklist=interview.checklist,
        )
        
        return await self.interview_repo.get_by_id(interview_id)
    
    async def get_user_interviews(
        self,
        telegram_id: int,
        include_past: bool = False,
        status: Optional[InterviewStatus] = None,
    ) -> List[Interview]:
        """Get user's interviews."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return []
        
        return await self.interview_repo.get_user_interviews(
            user_id=user.id,
            include_past=include_past,
            status=status,
        )
    
    async def search_interviews(
        self,
        telegram_id: int,
        query: str,
    ) -> List[Interview]:
        """Search interviews."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return []
        
        return await self.interview_repo.search(user.id, query)
    
    async def get_interview_by_id(self, interview_id: int) -> Optional[Interview]:
        """Get interview by ID."""
        return await self.interview_repo.get_by_id(interview_id)
    
    async def get_pipeline(self, interview_id: int) -> List[Interview]:
        """Get interview pipeline."""
        return await self.interview_repo.get_pipeline(interview_id)
    
    async def delete_interview(self, interview_id: int) -> bool:
        """Delete interview."""
        return await self.interview_repo.delete(interview_id)
    
    async def get_statistics(self, telegram_id: int) -> Dict[str, Any]:
        """Get user statistics."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return {}
        
        return await self.interview_repo.get_statistics(user.id)
    
    @staticmethod
    def _get_default_checklist(interview_type: InterviewType) -> List[dict]:
        """Get default checklist based on interview type."""
        common_items = [
            {"text": "Изучить компанию", "checked": False},
            {"text": "Подготовить вопросы работодателю", "checked": False},
            {"text": "Проверить резюме", "checked": False},
            {"text": "Проверить камеру и микрофон", "checked": False},
            {"text": "Проверить интернет-соединение", "checked": False},
            {"text": "Открыть ссылку на встречу за 5 минут", "checked": False},
        ]
        
        type_specific = {
            InterviewType.TECHNICAL: [
                {"text": "Повторить алгоритмы и структуры данных", "checked": False},
                {"text": "Подготовить примеры кода", "checked": False},
            ],
            InterviewType.LIVE_CODING: [
                {"text": "Настроить среду разработки", "checked": False},
                {"text": "Проверить возможность шарить экран", "checked": False},
            ],
            InterviewType.SYSTEM_DESIGN: [
                {"text": "Повторить паттерны проектирования", "checked": False},
                {"text": "Подготовить примеры архитектур", "checked": False},
            ],
        }
        
        checklist = common_items.copy()
        if interview_type in type_specific:
            checklist.extend(type_specific[interview_type])
        
        return checklist
    
    @staticmethod
    def format_interview_details(interview: Interview, include_history: bool = False, user_timezone: str = "Europe/Moscow") -> str:
        """Format interview details for display."""
        from app.utils.validators import TimezoneHelper
        
        camera_text = "✅ Да" if interview.camera_required else "❌ Нет"
        
        status_emoji = {
            InterviewStatus.SCHEDULED: "📅",
            InterviewStatus.COMPLETED: "✅",
            InterviewStatus.CANCELLED: "❌",
            InterviewStatus.RESCHEDULED: "🔄",
            InterviewStatus.OFFER: "🎉",
            InterviewStatus.REJECTED: "😞",
            InterviewStatus.WAITING_FEEDBACK: "⏳",
        }
        
        emoji = status_emoji.get(interview.status, "📋")
        
        details = [
            f"{emoji} <b>Детали интервью</b>\n",
            f"🏢 <b>Компания:</b> {interview.company_name}",
            f"💼 <b>Позиция:</b> {interview.position}",
        ]
        
        if interview.vacancy_url:
            details.append(f"🔗 <b>Вакансия:</b> {interview.vacancy_url}")
        
        # Format dates with timezone
        date_str = TimezoneHelper.format_datetime(interview.interview_date, user_timezone)
        
        details.extend([
            f"👤 <b>Рекрутер:</b> {interview.recruiter_name}",
            f"📅 <b>Дата и время:</b> {date_str}",
        ])
        
        if interview.original_date:
            original_date_str = TimezoneHelper.format_datetime(interview.original_date, user_timezone)
            details.append(f"🔄 <b>Исходная дата:</b> {original_date_str}")
        
        details.extend([
            f"💻 <b>Платформа:</b> {interview.platform_name}",
        ])
        
        if interview.platform_url:
            details.append(f"🔗 <b>Ссылка:</b> {interview.platform_url}")
        
        details.extend([
            f"📹 <b>Камера:</b> {camera_text}",
            f"📝 <b>Тип:</b> {interview.interview_type.value}",
            f"📊 <b>Статус:</b> {interview.status.value}",
            f"🎯 <b>Этап:</b> {interview.stage_number}",
        ])
        
        if interview.rating:
            details.append(f"⭐️ <b>Оценка:</b> {'⭐️' * interview.rating}")
        
        if interview.preparation_notes:
            details.append(f"\n📝 <b>Заметки для подготовки:</b>\n{interview.preparation_notes}")
        
        if interview.post_interview_notes:
            details.append(f"\n💭 <b>Заметки после интервью:</b>\n{interview.post_interview_notes}")
        
        if include_history and interview.status_history:
            details.append("\n📜 <b>История изменений:</b>")
            for h in interview.status_history[-3:]:  # Last 3 changes
                date_str = TimezoneHelper.format_datetime(h.changed_at, user_timezone)
                details.append(f"• {date_str}: {h.new_status.value}")
        
        return "\n".join(details)
    
    @staticmethod
    def format_checklist(interview: Interview) -> str:
        """Format checklist for display."""
        if not interview.checklist:
            return "Чек-лист пуст"
        
        lines = ["📋 <b>Чек-лист подготовки:</b>\n"]
        
        for i, item in enumerate(interview.checklist):
            checkbox = "☑️" if item["checked"] else "⬜️"
            lines.append(f"{checkbox} {item['text']}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_pipeline(interviews: List[Interview], user_timezone: str = "Europe/Moscow") -> str:
        """Format interview pipeline."""
        from app.utils.validators import TimezoneHelper
        
        if not interviews:
            return "Нет этапов"
        
        lines = ["🔄 <b>Этапы собеседования:</b>\n"]
        
        for interview in sorted(interviews, key=lambda x: x.stage_number):
            status_emoji = {
                InterviewStatus.SCHEDULED: "📅",
                InterviewStatus.COMPLETED: "✅",
                InterviewStatus.CANCELLED: "❌",
                InterviewStatus.OFFER: "🎉",
                InterviewStatus.REJECTED: "😞",
            }
            emoji = status_emoji.get(interview.status, "📋")
            
            date_str = TimezoneHelper.format_datetime(interview.interview_date, user_timezone)
            lines.append(
                f"{emoji} <b>Этап {interview.stage_number}:</b> {interview.interview_type.value} "
                f"({date_str})"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def format_statistics(stats: Dict[str, Any]) -> str:
        """Format statistics for display."""
        lines = [
            "📊 <b>Ваша статистика:</b>\n",
            f"📈 <b>Всего интервью:</b> {stats['total']}",
        ]
        
        if stats['by_status']:
            lines.append("\n<b>По статусам:</b>")
            for status, count in stats['by_status'].items():
                lines.append(f"• {status}: {count}")
        
        if stats.get('success_rate'):
            lines.append(f"\n🎯 <b>Процент офферов:</b> {stats['success_rate']}%")
        
        if stats['by_type']:
            lines.append("\n<b>По типам:</b>")
            for itype, count in sorted(
                stats['by_type'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]:
                lines.append(f"• {itype}: {count}")
        
        return "\n".join(lines)


class QuickAddParser:
    """Parser for quick interview creation."""
    
    @staticmethod
    def parse(text: str) -> Optional[Dict[str, Any]]:
        """
        Parse quick add format.
        Format: company | position | date time | platform url
        Example: Google | Senior Dev | 25.12.2024 15:00 | Zoom https://zoom.us/j/123
        """
        try:
            parts = [p.strip() for p in text.split("|")]
            
            if len(parts) < 3:
                return None
            
            company = parts[0]
            position = parts[1]
            date_time_str = parts[2]
            
            # Parse date
            from app.utils.validators import InputValidator
            interview_date = InputValidator.validate_datetime(date_time_str)
            
            platform_name = "Не указана"
            platform_url = None
            
            if len(parts) >= 4:
                platform_parts = parts[3].split()
                platform_name = platform_parts[0]
                if len(platform_parts) > 1:
                    platform_url = platform_parts[1]
            
            return {
                "company": company,
                "position": position,
                "interview_date": interview_date,
                "platform_name": platform_name,
                "platform_url": platform_url,
                "recruiter_name": "Не указан",
                "camera_required": False,
                "interview_type": InterviewType.SCREENING,
            }
            
        except Exception:
            return None