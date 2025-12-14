"""Export handlers."""
import os
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.inline import get_export_menu_keyboard, get_main_menu_keyboard
from app.services.export_service import ExportService

router = Router()


@router.callback_query(F.data == "export_menu")
async def show_export_menu(callback: CallbackQuery):
    """Show export menu."""
    await callback.message.edit_text(
        "📤 <b>Экспорт данных</b>\n\n"
        "Выберите формат экспорта:",
        reply_markup=get_export_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "export_ics")
async def export_ics(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Export to ICS calendar format."""
    await callback.answer("⏳ Создаю файл...")
    
    service = ExportService(session)
    filepath = await service.export_to_ics(callback.from_user.id)
    
    if not filepath:
        await callback.message.edit_text(
            "❌ Нет интервью для экспорта",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
        return
    
    try:
        # Send file
        document = FSInputFile(filepath)
        await bot.send_document(
            chat_id=callback.from_user.id,
            document=document,
            caption="📅 <b>Ваши интервью в формате календаря</b>\n\n"
                    "Откройте этот файл в Google Calendar, Apple Calendar или другом календарном приложении.",
            parse_mode="HTML",
        )
        
        await callback.message.edit_text(
            "✅ Файл календаря отправлен!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
        
        # Clean up
        os.remove(filepath)
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при отправке файла: {str(e)}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "export_json")
async def export_json(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Export to JSON format."""
    await callback.answer("⏳ Создаю файл...")
    
    service = ExportService(session)
    filepath = await service.export_to_json(callback.from_user.id)
    
    if not filepath:
        await callback.message.edit_text(
            "❌ Нет данных для экспорта",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
        return
    
    try:
        # Send file
        document = FSInputFile(filepath)
        await bot.send_document(
            chat_id=callback.from_user.id,
            document=document,
            caption="📄 <b>Экспорт всех данных в JSON</b>\n\n"
                    "Этот файл содержит все ваши интервью и можно использовать для резервного копирования.",
            parse_mode="HTML",
        )
        
        await callback.message.edit_text(
            "✅ JSON файл отправлен!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
        
        # Clean up
        os.remove(filepath)
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при отправке файла: {str(e)}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "create_backup")
async def create_backup(callback: CallbackQuery, session: AsyncSession):
    """Create database backup."""
    from app.config import settings
    
    if callback.from_user.id not in settings.admin_list:
        await callback.answer("❌ Доступно только администраторам", show_alert=True)
        return
    
    await callback.answer("⏳ Создаю резервную копию...")
    
    service = ExportService(session)
    filepath = await service.create_backup()
    
    if filepath:
        await callback.message.edit_text(
            f"✅ <b>Резервная копия создана!</b>\n\n"
            f"📁 Путь: <code>{filepath}</code>",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка при создании резервной копии",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )