"""User settings handlers."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories import UserRepository
from app.utils.validators import TimezoneHelper, InputValidator, ValidationError
from app.keyboards.inline import get_main_menu_keyboard, get_cancel_keyboard
from aiogram.fsm.state import State, StatesGroup

router = Router()


class SettingsStates(StatesGroup):
    """States for settings."""
    waiting_for_timezone = State()


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Get settings keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🌍 Часовой пояс",
            callback_data="settings_timezone",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔔 Уведомления",
            callback_data="notification_settings",
        )
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()


def get_timezone_keyboard() -> InlineKeyboardMarkup:
    """Get timezone selection keyboard."""
    builder = InlineKeyboardBuilder()
    
    timezones = TimezoneHelper.get_popular_timezones()
    
    for tz_name, tz_desc in timezones:
        builder.row(
            InlineKeyboardButton(
                text=tz_desc,
                callback_data=f"set_tz_{tz_name}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="✍️ Ввести вручную",
            callback_data="timezone_manual",
        )
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="settings_menu")
    )
    return builder.as_markup()


@router.callback_query(F.data == "settings_menu")
async def show_settings(callback: CallbackQuery, session: AsyncSession):
    """Show settings menu."""
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"⚙️ <b>Настройки</b>\n\n"
        f"🌍 <b>Часовой пояс:</b> {user.timezone}\n"
        f"🗣 <b>Язык:</b> {user.locale.upper()}",
        reply_markup=get_settings_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "settings_timezone")
async def show_timezone_settings(callback: CallbackQuery):
    """Show timezone settings."""
    await callback.message.edit_text(
        "🌍 <b>Выбор часового пояса</b>\n\n"
        "Выберите ваш часовой пояс из списка или введите вручную:",
        reply_markup=get_timezone_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_tz_"))
async def set_timezone(callback: CallbackQuery, session: AsyncSession):
    """Set timezone from button."""
    timezone = callback.data.replace("set_tz_", "")
    
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    await user_repo.update_timezone(user.id, timezone)
    
    await callback.message.edit_text(
        f"✅ Часовой пояс изменен на: <b>{timezone}</b>\n\n"
        f"Теперь все даты и время будут отображаться в вашем часовом поясе.",
        reply_markup=get_settings_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer(f"✅ Установлен {timezone}")


@router.callback_query(F.data == "timezone_manual")
async def start_manual_timezone(callback: CallbackQuery, state: FSMContext):
    """Start manual timezone input."""
    await state.set_state(SettingsStates.waiting_for_timezone)
    
    await callback.message.edit_text(
        "🌍 <b>Ввод часового пояса вручную</b>\n\n"
        "Введите название часового пояса в формате: <code>Регион/Город</code>\n\n"
        "Примеры:\n"
        "• <code>Europe/Kaliningrad</code>\n"
        "• <code>Asia/Yekaterinburg</code>\n",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SettingsStates.waiting_for_timezone)
async def process_manual_timezone(message: Message, state: FSMContext, session: AsyncSession):
    """Process manual timezone input."""
    try:
        timezone = InputValidator.validate_timezone(message.text)
        
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        
        if not user:
            await message.answer("❌ Ошибка")
            await state.clear()
            return
        
        await user_repo.update_timezone(user.id, timezone)
        await state.clear()
        
        await message.answer(
            f"✅ Часовой пояс установлен: <b>{timezone}</b>",
            reply_markup=get_settings_keyboard(),
            parse_mode="HTML",
        )
        
    except ValidationError as e:
        await message.answer(
            f"❌ {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )