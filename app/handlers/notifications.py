"""Notification settings handlers."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.inline import (
    get_notification_settings_keyboard,
    get_cancel_keyboard,
    get_main_menu_keyboard,
)
from app.services.notification_service import NotificationService
from app.states.interview_states import NotificationSettingsStates
from app.utils.validators import InputValidator, ValidationError
from app.config import settings

router = Router()


@router.callback_query(F.data == "notification_settings")
async def show_notification_settings(
    callback: CallbackQuery,
    session: AsyncSession,
    bot,
):
    """Show notification settings."""
    service = NotificationService(session, bot)
    settings_data = await service.get_user_notification_settings(callback.from_user.id)
    
    if not settings_data:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    status = "🔔 Включены" if settings_data["enabled"] else "🔕 Выключены"
    times_text = ", ".join([f"{t}ч" for t in sorted(settings_data["times"], reverse=True)])
    
    text = [
        "⚙️ <b>Настройки уведомлений</b>\n",
        f"<b>Статус:</b> {status}",
        f"<b>Время уведомлений:</b> {times_text}",
        "\n<i>Уведомления будут отправляться за указанное время до начала интервью.</i>",
    ]
    
    await callback.message.edit_text(
        "\n".join(text),
        reply_markup=get_notification_settings_keyboard(settings_data["enabled"]),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "toggle_notifications")
async def toggle_notifications(
    callback: CallbackQuery,
    session: AsyncSession,
    bot,
):
    """Toggle notifications on/off."""
    service = NotificationService(session, bot)
    enabled = await service.toggle_notifications(callback.from_user.id)
    
    status = "включены" if enabled else "выключены"
    await callback.answer(f"✅ Уведомления {status}", show_alert=True)
    
    # Refresh settings view
    await show_notification_settings(callback, session, bot)


@router.callback_query(F.data == "change_notification_times")
async def start_change_notification_times(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Start changing notification times."""
    await state.set_state(NotificationSettingsStates.waiting_for_custom_times)
    
    await callback.message.edit_text(
        "⏰ <b>Настройка времени уведомлений</b>\n\n"
        "Введите время уведомлений в часах через запятую.\n"
        "Например: <code>24, 12, 6, 3, 1.5, 0.5</code>\n\n"
        "<i>Можно использовать дробные числа (например, 0.5 = 30 минут)</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(NotificationSettingsStates.waiting_for_custom_times)
async def process_custom_times(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    bot,
):
    """Process custom notification times."""
    try:
        times = InputValidator.validate_notification_times(message.text)
        
        service = NotificationService(session, bot)
        await service.update_notification_times(message.from_user.id, times)
        
        await state.clear()
        
        times_text = ", ".join([f"{t}ч" for t in times])
        await message.answer(
            f"✅ <b>Время уведомлений обновлено!</b>\n\n"
            f"Новые значения: {times_text}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
        
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(F.data == "reset_notification_times")
async def reset_notification_times(
    callback: CallbackQuery,
    session: AsyncSession,
    bot,
):
    """Reset notification times to default."""
    service = NotificationService(session, bot)
    await service.update_notification_times(
        callback.from_user.id,
        settings.default_notification_times,
    )
    
    await callback.answer("✅ Настройки сброшены на стандартные", show_alert=True)
    
    # Refresh settings view
    await show_notification_settings(callback, session, bot)