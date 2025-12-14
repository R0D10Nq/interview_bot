"""Recruiter management handlers."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.states.interview_states import RecruiterStates
from app.keyboards.inline import (
    get_recruiters_keyboard,
    get_recruiter_detail_keyboard,
    get_cancel_keyboard,
    get_skip_keyboard,
    get_main_menu_keyboard,
)
from app.database.repositories import RecruiterRepository, UserRepository
from app.utils.validators import InputValidator, ValidationError

router = Router()


@router.callback_query(F.data == "recruiters_list")
async def show_recruiters(callback: CallbackQuery, session: AsyncSession):
    """Show recruiters list."""
    user_repo = UserRepository(session)
    recruiter_repo = RecruiterRepository(session)
    
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    recruiters = await recruiter_repo.get_user_recruiters(user.id)
    
    if not recruiters:
        await callback.message.edit_text(
            "👥 <b>Список рекрутеров пуст</b>\n\n"
            "Добавьте рекрутеров для быстрого доступа к контактам",
            reply_markup=get_recruiters_keyboard([]),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            f"👥 <b>Ваши рекрутеры</b> ({len(recruiters)}):\n\n"
            "Выберите рекрутера для просмотра контактов:",
            reply_markup=get_recruiters_keyboard(recruiters),
            parse_mode="HTML",
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("view_recruiter_"))
async def view_recruiter(callback: CallbackQuery, session: AsyncSession):
    """View recruiter details."""
    recruiter_id = int(callback.data.replace("view_recruiter_", ""))
    
    recruiter_repo = RecruiterRepository(session)
    recruiter = await recruiter_repo.get_by_id(recruiter_id)
    
    if not recruiter:
        await callback.answer("❌ Рекрутер не найден", show_alert=True)
        return
    
    details = [
        f"👤 <b>{recruiter.name}</b>\n",
    ]
    
    if recruiter.company_name:
        details.append(f"🏢 <b>Компания:</b> {recruiter.company_name}")
    
    if recruiter.email:
        details.append(f"📧 <b>Email:</b> {recruiter.email}")
    
    if recruiter.phone:
        details.append(f"📞 <b>Телефон:</b> {recruiter.phone}")
    
    if recruiter.telegram:
        details.append(f"💬 <b>Telegram:</b> {recruiter.telegram}")
    
    if recruiter.notes:
        details.append(f"\n📝 <b>Заметки:</b>\n{recruiter.notes}")
    
    await callback.message.edit_text(
        "\n".join(details),
        reply_markup=get_recruiter_detail_keyboard(recruiter_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "add_recruiter")
async def start_add_recruiter(callback: CallbackQuery, state: FSMContext):
    """Start adding recruiter."""
    await state.set_state(RecruiterStates.waiting_for_name)
    
    await callback.message.edit_text(
        "➕ <b>Добавление рекрутера</b>\n\n"
        "Введите имя рекрутера:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(RecruiterStates.waiting_for_name)
async def process_recruiter_name(message: Message, state: FSMContext):
    """Process recruiter name."""
    try:
        name = InputValidator.validate_text(message.text, max_length=255)
        await state.update_data(name=name)
        await state.set_state(RecruiterStates.waiting_for_company)
        
        await message.answer(
            f"✅ Имя: <b>{name}</b>\n\n"
            "🏢 Введите название компании:",
            reply_markup=get_skip_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(F.data == "skip", RecruiterStates.waiting_for_company)
async def skip_company(callback: CallbackQuery, state: FSMContext):
    """Skip company."""
    await state.update_data(company_name=None)
    await state.set_state(RecruiterStates.waiting_for_email)
    
    await callback.message.edit_text(
        "📧 Введите email рекрутера:",
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(RecruiterStates.waiting_for_company)
async def process_recruiter_company(message: Message, state: FSMContext):
    """Process recruiter company."""
    company_name = message.text.strip()
    await state.update_data(company_name=company_name)
    await state.set_state(RecruiterStates.waiting_for_email)
    
    await message.answer(
        "📧 Введите email рекрутера:",
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "skip", RecruiterStates.waiting_for_email)
async def skip_email(callback: CallbackQuery, state: FSMContext):
    """Skip email."""
    await state.update_data(email=None)
    await state.set_state(RecruiterStates.waiting_for_phone)
    
    await callback.message.edit_text(
        "📞 Введите номер телефона:",
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(RecruiterStates.waiting_for_email)
async def process_recruiter_email(message: Message, state: FSMContext):
    """Process recruiter email."""
    email = message.text.strip()
    await state.update_data(email=email)
    await state.set_state(RecruiterStates.waiting_for_phone)
    
    await message.answer(
        "📞 Введите номер телефона:",
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "skip", RecruiterStates.waiting_for_phone)
async def skip_phone(callback: CallbackQuery, state: FSMContext):
    """Skip phone."""
    await state.update_data(phone=None)
    await state.set_state(RecruiterStates.waiting_for_telegram)
    
    await callback.message.edit_text(
        "💬 Введите Telegram username:",
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(RecruiterStates.waiting_for_phone)
async def process_recruiter_phone(message: Message, state: FSMContext):
    """Process recruiter phone."""
    phone = message.text.strip()
    await state.update_data(phone=phone)
    await state.set_state(RecruiterStates.waiting_for_telegram)
    
    await message.answer(
        "💬 Введите Telegram username:",
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "skip", RecruiterStates.waiting_for_telegram)
async def skip_telegram(callback: CallbackQuery, state: FSMContext):
    """Skip telegram."""
    await state.update_data(telegram=None)
    await state.set_state(RecruiterStates.waiting_for_notes)
    
    await callback.message.edit_text(
        "📝 Введите заметки о рекрутере:",
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(RecruiterStates.waiting_for_telegram)
async def process_recruiter_telegram(message: Message, state: FSMContext):
    """Process recruiter telegram."""
    telegram = message.text.strip()
    await state.update_data(telegram=telegram)
    await state.set_state(RecruiterStates.waiting_for_notes)
    
    await message.answer(
        "📝 Введите заметки о рекрутере:",
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "skip", RecruiterStates.waiting_for_notes)
async def skip_notes(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Skip notes and save."""
    await state.update_data(notes=None)
    await save_recruiter(callback.message, state, session)
    await callback.answer()


@router.message(RecruiterStates.waiting_for_notes)
async def process_recruiter_notes(message: Message, state: FSMContext, session: AsyncSession):
    """Process recruiter notes and save."""
    await state.update_data(notes=message.text)
    await save_recruiter(message, state, session)


async def save_recruiter(message: Message, state: FSMContext, session: AsyncSession):
    """Save recruiter."""
    data = await state.get_data()
    
    user_repo = UserRepository(session)
    recruiter_repo = RecruiterRepository(session)
    
    user = await user_repo.get_by_telegram_id(message.from_user.id if hasattr(message, 'from_user') else message.chat.id)
    
    if not user:
        await message.answer("❌ Ошибка")
        await state.clear()
        return
    
    recruiter = await recruiter_repo.create(
        user_id=user.id,
        name=data["name"],
        company_name=data.get("company_name"),
        email=data.get("email"),
        phone=data.get("phone"),
        telegram=data.get("telegram"),
        notes=data.get("notes"),
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ Рекрутер <b>{recruiter.name}</b> успешно добавлен!",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("delete_recruiter_"))
async def delete_recruiter(callback: CallbackQuery, session: AsyncSession):
    """Delete recruiter."""
    recruiter_id = int(callback.data.replace("delete_recruiter_", ""))
    
    recruiter_repo = RecruiterRepository(session)
    success = await recruiter_repo.delete(recruiter_id)
    
    if success:
        await callback.message.edit_text(
            "✅ Рекрутер удален",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer("✅ Удалено")
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)