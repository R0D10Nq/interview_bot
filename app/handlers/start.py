"""Start and main menu handlers."""
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards.inline import get_main_menu_keyboard
from app.database.repositories import UserRepository

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession):
    """Handle /start command."""
    # Create or get user
    user_repo = UserRepository(session)
    await user_repo.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
    )
    
    await message.answer(
        "👋 <b>Добро пожаловать в бот для управления собеседованиями!</b>\n\n"
        "Я помогу вам:\n"
        "• 📝 Сохранять информацию о предстоящих интервью\n"
        "• 🔔 Получать своевременные напоминания\n"
        "• 📋 Управлять списком собеседований\n\n"
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("menu"))
@router.callback_query(F.data == "main_menu")
async def show_main_menu(event: Message | CallbackQuery, state: FSMContext):
    """Show main menu."""
    # Clear any active state
    await state.clear()
    
    text = "📱 <b>Главное меню</b>\n\nВыберите действие:"
    
    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
    else:
        await event.message.edit_text(
            text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
        await event.answer()


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Cancel current action."""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Действие отменено.\n\n📱 <b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()