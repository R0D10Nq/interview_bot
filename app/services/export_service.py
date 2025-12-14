"""Export service for calendar and backup."""
import os
import json
import shutil
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
from icalendar import Calendar, Event
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
import logging

from app.database.models import Interview
from app.database.repositories import InterviewRepository, UserRepository, BackupRepository
from app.config import settings, DATA_DIR, BACKUP_DIR

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting data."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.interview_repo = InterviewRepository(session)
        self.user_repo = UserRepository(session)
        self.backup_repo = BackupRepository(session)
    
    async def export_to_ics(
        self,
        telegram_id: int,
        interview_ids: Optional[List[int]] = None,
    ) -> Optional[str]:
        """Export interviews to iCalendar format."""
        import pytz
        
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return None
        
        # Get user timezone
        try:
            user_tz = pytz.timezone(user.timezone)
        except:
            user_tz = pytz.UTC
        
        # Get interviews
        if interview_ids:
            interviews = []
            for interview_id in interview_ids:
                interview = await self.interview_repo.get_by_id(interview_id)
                if interview:
                    interviews.append(interview)
        else:
            interviews = await self.interview_repo.get_user_interviews(
                user_id=user.id,
                include_past=False,
            )
        
        if not interviews:
            return None
        
        # Create calendar
        cal = Calendar()
        cal.add('prodid', '-//Interview Bot//Interview Calendar//EN')
        cal.add('version', '2.0')
        
        for interview in interviews:
            event = Event()
            event.add('summary', f'Интервью: {interview.company_name} - {interview.position}')
            
            # Convert UTC to user timezone for calendar
            if interview.interview_date.tzinfo is None:
                interview_dt = pytz.UTC.localize(interview.interview_date)
            else:
                interview_dt = interview.interview_date
            
            event.add('dtstart', interview_dt)
            event.add('dtend', interview_dt + timedelta(hours=1))
            
            description_parts = [
                f"Компания: {interview.company_name}",
                f"Позиция: {interview.position}",
                f"Рекрутер: {interview.recruiter_name}",
                f"Платформа: {interview.platform_name}",
            ]
            
            if interview.platform_url:
                description_parts.append(f"Ссылка: {interview.platform_url}")
            
            event.add('description', '\n'.join(description_parts))
            
            if interview.platform_url:
                event.add('url', interview.platform_url)
            
            event.add('location', interview.platform_name)
            
            cal.add_component(event)
        
        # Save to file
        filename = f"interviews_{telegram_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
        filepath = DATA_DIR / filename
        
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(cal.to_ical())
        
        return str(filepath)
    
    async def export_to_json(self, telegram_id: int) -> Optional[str]:
        """Export all user data to JSON."""
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return None
        
        interviews = await self.interview_repo.get_user_interviews(
            user_id=user.id,
            include_past=True,
        )
        
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "user": {
                "telegram_id": user.telegram_id,
                "username": user.username,
            },
            "interviews": [
                {
                    "company": i.company_name,
                    "position": i.position,
                    "vacancy_url": i.vacancy_url,
                    "recruiter_name": i.recruiter_name,
                    "interview_date": i.interview_date.isoformat(),
                    "platform_name": i.platform_name,
                    "platform_url": i.platform_url,
                    "camera_required": i.camera_required,
                    "interview_type": i.interview_type.value,
                    "status": i.status.value,
                    "preparation_notes": i.preparation_notes,
                    "post_interview_notes": i.post_interview_notes,
                    "rating": i.rating,
                }
                for i in interviews
            ],
        }
        
        filename = f"interviews_export_{telegram_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = DATA_DIR / filename
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
        
        return str(filepath)
    
    async def create_backup(self) -> Optional[str]:
        """Create database backup."""
        if not settings.backup_enabled:
            return None
        
        try:
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backup_{timestamp}.db"
            filepath = BACKUP_DIR / filename
            
            # Get database file path
            # Extract path from database URL
            db_url = settings.database_url
            if "sqlite" in db_url:
                # Format: sqlite+aiosqlite:///path/to/db.db
                db_path = db_url.split("///")[-1]
                db_path = Path(db_path)
                
                if db_path.exists():
                    # Copy database file
                    shutil.copy2(db_path, filepath)
                    
                    # Get file size
                    size_bytes = os.path.getsize(filepath)
                    
                    # Save backup metadata
                    await self.backup_repo.create(
                        filename=filename,
                        filepath=str(filepath),
                        size_bytes=size_bytes,
                    )
                    
                    # Clean old backups
                    await self.backup_repo.delete_old(days=30)
                    
                    logger.info(f"Резервная копия создана: {filepath}")
                    return str(filepath)
                else:
                    logger.error(f"Файл базы данных не найден: {db_path}")
                    return None
            else:
                logger.warning("Резервные копии поддерживаются только для базы данных SQLite")
                return None
            
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return None