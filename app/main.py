"""Main application entry point."""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.database import init_db, async_session_maker
from app.handlers import (
    start,
    interview,
    notifications,
    recruiters,
    templates,
    export,
    user_settings,  # Изменено!
)
from app.services.notification_service import NotificationService
from app.services.export_service import ExportService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


async def check_notifications(bot: Bot):
    """Check and send notifications."""
    async with async_session_maker() as session:
        service = NotificationService(session, bot)
        await service.check_and_send_notifications()


async def create_scheduled_backup(bot: Bot):
    """Create scheduled backup."""
    if not settings.backup_enabled:
        return
    
    async with async_session_maker() as session:
        service = ExportService(session)
        filepath = await service.create_backup()
        
        if filepath:
            logger.info(f"Scheduled backup created: {filepath}")
            
            # Notify admins
            for admin_id in settings.admin_list:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f"✅ Автоматическая резервная копия создана\n\n📁 {filepath}",
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")


async def main():
    """Main application function."""
    # Initialize database
    logger.info("Инициализация базы данных...")
    await init_db()
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register routers
    dp.include_router(start.router)
    dp.include_router(user_settings.router)  # Изменено!
    dp.include_router(interview.router)
    dp.include_router(notifications.router)
    dp.include_router(recruiters.router)
    dp.include_router(templates.router)
    dp.include_router(export.router)
    
    # Middleware to inject session and bot
    @dp.update.outer_middleware()
    async def session_middleware(handler, event, data):
        async with async_session_maker() as session:
            data['session'] = session
            data['bot'] = bot
            return await handler(event, data)
    
    # Initialize scheduler
    scheduler = AsyncIOScheduler(timezone=settings.tz)
    
    # Add notification check job (every minute)
    scheduler.add_job(
        check_notifications,
        'interval',
        minutes=1,
        args=[bot],
        id='check_notifications',
        replace_existing=True,
    )
    
    # Add backup job (daily at 3 AM)
    if settings.backup_enabled:
        scheduler.add_job(
            create_scheduled_backup,
            'cron',
            hour=3,
            minute=0,
            args=[bot],
            id='scheduled_backup',
            replace_existing=True,
        )
    
    scheduler.start()
    
    logger.info("Бот запущен!")
    logger.info(f"Часовой пояс: {settings.tz}")
    logger.info(f"Резервное копирование: {settings.backup_enabled}")
    logger.info(f"Администраторы: {settings.admin_list}")
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен!")