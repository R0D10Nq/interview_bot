"""Business logic for interview management."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Interview, InterviewType
from app.database.repositories import InterviewRepository, UserRepository


class InterviewService:
    """Service for interview management."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.interview_repo = InterviewRepository(session)
        self.user_repo = UserRepository(session)
    
    async def create_interview(
        self,
        telegram_id: int,
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
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise ValueError("Пользователь не найден")
        
        interview = await self.interview_repo.create(
            user_id=user.id,
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
        
        return interview
    
    async def get_user_interviews(
        self,
        telegram_id: int,
        include_past: bool = False,
    ) -> List[Interview]:
        """Get user's interviews."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return []
        
        return await self.interview_repo.get_user_interviews(
            user_id=user.id,
            include_past=include_past,
        )
    
    async def get_interview_by_id(self, interview_id: int) -> Optional[Interview]:
        """Get interview by ID."""
        return await self.interview_repo.get_by_id(interview_id)
    
    async def delete_interview(self, interview_id: int) -> bool:
        """Delete interview."""
        return await self.interview_repo.delete(interview_id)
    
    @staticmethod
    def format_interview_details(interview: Interview) -> str:
        """Format interview details for display."""
        camera_text = "✅ Да" if interview.camera_required else "❌ Нет"
        
        details = [
            f"📋 <b>Детали интервью</b>\n",
            f"🏢 <b>Компания:</b> {interview.company}",
            f"💼 <b>Позиция:</b> {interview.position}",
        ]
        
        if interview.vacancy_url:
            details.append(f"🔗 <b>Вакансия:</b> {interview.vacancy_url}")
        
        details.extend([
            f"👤 <b>Рекрутер:</b> {interview.recruiter_name}",
            f"📅 <b>Дата и время:</b> {interview.interview_date.strftime('%d.%m.%Y %H:%M')}",
            f"💻 <b>Платформа:</b> {interview.platform_name}",
        ])
        
        if interview.platform_url:
            details.append(f"🔗 <b>Ссылка:</b> {interview.platform_url}")
        
        details.extend([
            f"📹 <b>Камера:</b> {camera_text}",
            f"📝 <b>Тип:</b> {interview.interview_type.value}",
        ])
        
        return "\n".join(details)