"""Interview management handlers."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.states.interview_states import InterviewStates
from app.keyboards.inline import (
    get_cancel_keyboard,
    get_skip_keyboard,
    get_camera_keyboard,
    get_interview_type_keyboard,
    get_confirm_keyboard,
    get_interviews_keyboard,
    get_interview_detail_keyboard,
    get_main_menu_keyboard,
)
from app.database.models import InterviewType
from app.services.interview_service import InterviewService
from app.utils.validators import InputValidator, ValidationError

router = Router()


@router.callback_query(F.data == "add_interview")
async def start_add_interview(callback: CallbackQuery, state: FSMContext):
    """Start interview creation process."""
    await state.set_state(InterviewStates.waiting_for_company)
    
    await callback.message.edit_text(
        "🏢 <b>Добавление нового интервью</b>\n\n"
        "Введите название компании:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(InterviewStates.waiting_for_company)
async def process_company(message: Message, state: FSMContext):
    """Process company name."""
    try:
        company = InputValidator.validate_text(message.text, max_length=255)
        await state.update_data(company=company)
        await state.set_state(InterviewStates.waiting_for_position)
        
        await message.answer(
            f"✅ Компания: <b>{company}</b>\n\n"
            "💼 Введите позицию/роль:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.message(InterviewStates.waiting_for_position)
async def process_position(message: Message, state: FSMContext):
    """Process position."""
    try:
        position = InputValidator.validate_text(message.text, max_length=255)
        await state.update_data(position=position)
        await state.set_state(InterviewStates.waiting_for_vacancy_url)
        
        await message.answer(
            f"✅ Позиция: <b>{position}</b>\n\n"
            "🔗 Введите ссылку на вакансию:",
            reply_markup=get_skip_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(F.data == "skip", InterviewStates.waiting_for_vacancy_url)
async def skip_vacancy_url(callback: CallbackQuery, state: FSMContext):
    """Skip vacancy URL."""
    await state.update_data(vacancy_url=None)
    await state.set_state(InterviewStates.waiting_for_recruiter_name)
    
    await callback.message.edit_text(
        "👤 Введите имя рекрутера:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(InterviewStates.waiting_for_vacancy_url)
async def process_vacancy_url(message: Message, state: FSMContext):
    """Process vacancy URL."""
    try:
        vacancy_url = InputValidator.validate_url(message.text)
        await state.update_data(vacancy_url=vacancy_url)
        await state.set_state(InterviewStates.waiting_for_recruiter_name)
        
        await message.answer(
            "✅ Ссылка сохранена\n\n"
            "👤 Введите имя рекрутера:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_skip_keyboard(),
        )


@router.message(InterviewStates.waiting_for_recruiter_name)
async def process_recruiter_name(message: Message, state: FSMContext):
    """Process recruiter name."""
    try:
        recruiter_name = InputValidator.validate_text(message.text, max_length=255)
        await state.update_data(recruiter_name=recruiter_name)
        await state.set_state(InterviewStates.waiting_for_interview_date)
        
        await message.answer(
            f"✅ Рекрутер: <b>{recruiter_name}</b>\n\n"
            "📅 Введите дату и время интервью\n"
            "(формат: ДД.ММ.ГГГГ ЧЧ:ММ, например: 25.12.2024 14:30):",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.message(InterviewStates.waiting_for_interview_date)
async def process_interview_date(message: Message, state: FSMContext):
    """Process interview date."""
    try:
        interview_date = InputValidator.validate_datetime(message.text)
        await state.update_data(interview_date=interview_date)
        await state.set_state(InterviewStates.waiting_for_platform_name)
        
        date_str = interview_date.strftime("%d.%m.%Y %H:%M")
        await message.answer(
            f"✅ Дата: <b>{date_str}</b>\n\n"
            "💻 Введите название платформы (например: Zoom, Google Meet, Teams):",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.message(InterviewStates.waiting_for_platform_name)
async def process_platform_name(message: Message, state: FSMContext):
    """Process platform name."""
    try:
        platform_name = InputValidator.validate_text(message.text, max_length=255)
        await state.update_data(platform_name=platform_name)
        await state.set_state(InterviewStates.waiting_for_platform_url)
        
        await message.answer(
            f"✅ Платформа: <b>{platform_name}</b>\n\n"
            "🔗 Введите ссылку на встречу:",
            reply_markup=get_skip_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(F.data == "skip", InterviewStates.waiting_for_platform_url)
async def skip_platform_url(callback: CallbackQuery, state: FSMContext):
    """Skip platform URL."""
    await state.update_data(platform_url=None)
    await state.set_state(InterviewStates.waiting_for_camera)
    
    await callback.message.edit_text(
        "📹 Требуется ли камера?",
        reply_markup=get_camera_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(InterviewStates.waiting_for_platform_url)
async def process_platform_url(message: Message, state: FSMContext):
    """Process platform URL."""
    try:
        platform_url = InputValidator.validate_url(message.text)
        await state.update_data(platform_url=platform_url)
        await state.set_state(InterviewStates.waiting_for_camera)
        
        await message.answer(
            "✅ Ссылка сохранена\n\n"
            "📹 Требуется ли камера?",
            reply_markup=get_camera_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_skip_keyboard(),
        )


@router.callback_query(F.data.in_(["camera_yes", "camera_no"]), InterviewStates.waiting_for_camera)
async def process_camera(callback: CallbackQuery, state: FSMContext):
    """Process camera requirement."""
    camera_required = callback.data == "camera_yes"
    await state.update_data(camera_required=camera_required)
    await state.set_state(InterviewStates.waiting_for_interview_type)
    
    camera_text = "Да" if camera_required else "Нет"
    await callback.message.edit_text(
        f"✅ Камера: <b>{camera_text}</b>\n\n"
        "📝 Выберите тип интервью:",
        reply_markup=get_interview_type_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("type_"), InterviewStates.waiting_for_interview_type)
async def process_interview_type(callback: CallbackQuery, state: FSMContext):
    """Process interview type."""
    type_name = callback.data.replace("type_", "")
    interview_type = InterviewType[type_name]
    
    await state.update_data(interview_type=interview_type)
    await state.set_state(InterviewStates.confirm)
    
    # Show confirmation
    data = await state.get_data()
    
    camera_text = "✅ Да" if data["camera_required"] else "❌ Нет"
    date_str = data["interview_date"].strftime("%d.%m.%Y %H:%M")
    
    confirmation_text = [
        "📋 <b>Проверьте данные интервью:</b>\n",
        f"🏢 <b>Компания:</b> {data['company']}",
        f"💼 <b>Позиция:</b> {data['position']}",
    ]
    
    if data.get("vacancy_url"):
        confirmation_text.append(f"🔗 <b>Вакансия:</b> {data['vacancy_url']}")
    
    confirmation_text.extend([
        f"👤 <b>Рекрутер:</b> {data['recruiter_name']}",
        f"📅 <b>Дата и время:</b> {date_str}",
        f"💻 <b>Платформа:</b> {data['platform_name']}",
    ])
    
    if data.get("platform_url"):
        confirmation_text.append(f"🔗 <b>Ссылка:</b> {data['platform_url']}")
    
    confirmation_text.extend([
        f"📹 <b>Камера:</b> {camera_text}",
        f"📝 <b>Тип:</b> {interview_type.value}",
    ])
    
    await callback.message.edit_text(
        "\n".join(confirmation_text),
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_yes", InterviewStates.confirm)
async def confirm_interview(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Confirm and save interview."""
    data = await state.get_data()
    
    try:
        service = InterviewService(session)
        interview = await service.create_interview(
            telegram_id=callback.from_user.id,
            company=data["company"],
            position=data["position"],
            vacancy_url=data.get("vacancy_url"),
            recruiter_name=data["recruiter_name"],
            interview_date=data["interview_date"],
            platform_name=data["platform_name"],
            platform_url=data.get("platform_url"),
            camera_required=data["camera_required"],
            interview_type=data["interview_type"],
        )
        
        await state.clear()
        
        await callback.message.edit_text(
            "✅ <b>Интервью успешно добавлено!</b>\n\n"
            "Вы будете получать уведомления:\n"
            "• За 24 часа\n"
            "• За 12 часов\n"
            "• За 6 часов\n"
            "• За 3 часа\n"
            "• За 1.5 часа\n"
            "• За 30 минут\n\n"
            "Настроить время уведомлений можно в меню настроек.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer("✅ Интервью добавлено!")
        
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при сохранении: {str(e)}\n\n"
            "Попробуйте снова.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer("❌ Ошибка")
        await state.clear()


@router.callback_query(F.data == "my_interviews")
async def show_interviews(callback: CallbackQuery, session: AsyncSession):
    """Show user's interviews."""
    service = InterviewService(session)
    interviews = await service.get_user_interviews(callback.from_user.id)
    
    if not interviews:
        await callback.message.edit_text(
            "📋 <b>Список интервью пуст</b>\n\n"
            "Добавьте первое интервью, чтобы начать!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            f"📋 <b>Ваши предстоящие интервью</b> ({len(interviews)}):\n\n"
            "Выберите интервью для просмотра:",
            reply_markup=get_interviews_keyboard(interviews),
            parse_mode="HTML",
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("view_interview_"))
async def view_interview(callback: CallbackQuery, session: AsyncSession):
    """View interview details."""
    interview_id = int(callback.data.replace("view_interview_", ""))
    
    service = InterviewService(session)
    interview = await service.get_interview_by_id(interview_id)
    
    if not interview:
        await callback.answer("❌ Интервью не найдено", show_alert=True)
        return
    
    details = service.format_interview_details(interview)
    
    await callback.message.edit_text(
        details,
        reply_markup=get_interview_detail_keyboard(interview_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_interview_"))
async def delete_interview(callback: CallbackQuery, session: AsyncSession):
    """Delete interview."""
    interview_id = int(callback.data.replace("delete_interview_", ""))
    
    service = InterviewService(session)
    success = await service.delete_interview(interview_id)
    
    if success:
        await callback.message.edit_text(
            "✅ Интервью успешно удалено!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer("✅ Удалено")
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)