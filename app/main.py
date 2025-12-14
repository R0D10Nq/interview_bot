"""Main application entry point."""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.database import init_db, async_session_maker
from app.handlers import start, interview, notifications
from app.services.notification_service import NotificationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


async def inject_dependencies(handler, event, data):
    """Inject dependencies into handlers."""
    async with async_session_maker() as session:
        data['session'] = session
        data['bot'] = data.get('bot')
        return await handler(event, data)


async def check_notifications(bot: Bot):
    """Check and send notifications."""
    async with async_session_maker() as session:
        service = NotificationService(session, bot)
        await service.check_and_send_notifications()


async def main():
    """Main application function."""
    # Initialize database
    logger.info("Инициализация БД...")
    await init_db()
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register routers
    dp.include_router(start.router)
    dp.include_router(interview.router)
    dp.include_router(notifications.router)
    
    # Middleware to inject session
    @dp.update.outer_middleware()
    async def session_middleware(handler, event, data):
        async with async_session_maker() as session:
            data['session'] = session
            data['bot'] = bot
            return await handler(event, data)
    
    # Initialize scheduler
    scheduler = AsyncIOScheduler(timezone=settings.tz)
    scheduler.add_job(
        check_notifications,
        'interval',
        minutes=1,
        args=[bot],
    )
    scheduler.start()
    
    logger.info("Бот запущен!")
    
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