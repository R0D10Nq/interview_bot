"""Interview management handlers."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.database.repositories import UserRepository
from app.utils.validators import TimezoneHelper  # где используется

from app.states.interview_states import (
    InterviewStates,
    QuickAddStates,
    EditInterviewStates,
    NotesStates,
    SearchStates,
    ChecklistStates,
    StatusChangeStates,
)
from app.keyboards.inline import (
    get_cancel_keyboard,
    get_skip_keyboard,
    get_camera_keyboard,
    get_interview_type_keyboard,
    get_confirm_keyboard,
    get_interviews_keyboard,
    get_interview_detail_keyboard,
    get_main_menu_keyboard,
    get_edit_menu_keyboard,
    get_status_keyboard,
    get_rating_keyboard,
    get_checklist_keyboard,
    get_notes_menu_keyboard,
    get_pipeline_keyboard,
)
from app.database.models import InterviewType, InterviewStatus
from app.database.repositories import UserRepository
from app.services.interview_service import InterviewService, QuickAddParser
from app.utils.validators import InputValidator, ValidationError

router = Router()


# ==================== ADD INTERVIEW ====================

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
async def process_interview_date(message: Message, state: FSMContext, session: AsyncSession):
    """Process interview date."""
    try:
        # Получаем timezone пользователя
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        user_timezone = user.timezone if user else "Europe/Moscow"
        
        interview_date = InputValidator.validate_datetime(message.text, user_timezone)
        await state.update_data(interview_date=interview_date)
        await state.set_state(InterviewStates.waiting_for_platform_name)
        
        from app.utils.validators import TimezoneHelper
        date_str = TimezoneHelper.format_datetime(interview_date, user_timezone)
        
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
    await state.set_state(InterviewStates.waiting_for_preparation_notes)
    
    await callback.message.edit_text(
        f"✅ Тип: <b>{interview_type.value}</b>\n\n"
        "📝 Введите заметки для подготовки (или пропустите):",
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "skip", InterviewStates.waiting_for_preparation_notes)
async def skip_preparation_notes(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Skip preparation notes."""
    await state.update_data(preparation_notes=None)
    await show_confirmation(callback, state, session)


@router.message(InterviewStates.waiting_for_preparation_notes)
async def process_preparation_notes(message: Message, state: FSMContext, session: AsyncSession):
    """Process preparation notes."""
    await state.update_data(preparation_notes=message.text)
    await state.set_state(InterviewStates.confirm)
    
    # Show confirmation
    await show_confirmation_message(message, state, session)


async def show_confirmation(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show confirmation message."""
    await state.set_state(InterviewStates.confirm)
    data = await state.get_data()
    
    # Получаем timezone пользователя
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    user_timezone = user.timezone if user else "Europe/Moscow"
    
    confirmation_text = build_confirmation_text(data, user_timezone)
    
    await callback.message.edit_text(
        confirmation_text,
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


async def show_confirmation_message(message: Message, state: FSMContext, session: AsyncSession):
    """Show confirmation message."""
    data = await state.get_data()
    
    # Получаем timezone пользователя
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    user_timezone = user.timezone if user else "Europe/Moscow"
    
    confirmation_text = build_confirmation_text(data, user_timezone)
    
    await message.answer(
        confirmation_text,
        reply_markup=get_confirm_keyboard(),
        parse_mode="HTML",
    )


def build_confirmation_text(data: dict, user_timezone: str = "Europe/Moscow") -> str:
    """Build confirmation text."""
    from app.utils.validators import TimezoneHelper
    
    camera_text = "✅ Да" if data["camera_required"] else "❌ Нет"
    date_str = TimezoneHelper.format_datetime(data["interview_date"], user_timezone)
    
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
        f"📝 <b>Тип:</b> {data['interview_type'].value}",
    ])
    
    if data.get("preparation_notes"):
        confirmation_text.append(f"\n💭 <b>Заметки:</b>\n{data['preparation_notes']}")
    
    return "\n".join(confirmation_text)


@router.callback_query(F.data == "confirm_yes", InterviewStates.confirm)
async def confirm_interview(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Confirm and save interview."""
    data = await state.get_data()
    
    try:
        service = InterviewService(session)
        interview = await service.create_interview(
            telegram_id=callback.from_user.id,
            company_name=data["company"],
            position=data["position"],
            vacancy_url=data.get("vacancy_url"),
            recruiter_name=data["recruiter_name"],
            interview_date=data["interview_date"],
            platform_name=data["platform_name"],
            platform_url=data.get("platform_url"),
            camera_required=data["camera_required"],
            interview_type=data["interview_type"],
            preparation_notes=data.get("preparation_notes"),
        )
        
        await state.clear()
        
        await callback.message.edit_text(
            "✅ <b>Интервью успешно добавлено!</b>\n\n"
            "📋 Создан чек-лист подготовки\n"
            "🔔 Настроены уведомления\n"
            "⏰ Создано напоминание для follow-up\n\n"
            "Вы можете просмотреть интервью в разделе 'Мои интервью'",
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


# ==================== QUICK ADD ====================

@router.callback_query(F.data == "quick_add")
async def start_quick_add(callback: CallbackQuery, state: FSMContext):
    """Start quick add."""
    await state.set_state(QuickAddStates.waiting_for_input)
    
    await callback.message.edit_text(
        "⚡️ <b>Быстрое добавление</b>\n\n"
        "Введите данные в формате:\n"
        "<code>Компания | Позиция | Дата Время | Платформа Ссылка</code>\n\n"
        "Пример:\n"
        "<code>Google | Senior Python Dev | 25.12.2024 15:00 | Zoom https://zoom.us/j/123</code>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(QuickAddStates.waiting_for_input)
async def process_quick_add(message: Message, state: FSMContext, session: AsyncSession):
    """Process quick add input."""
    parsed = QuickAddParser.parse(message.text)
    
    if not parsed:
        await message.answer(
            "❌ Не удалось распознать формат.\n\n"
            "Используйте формат:\n"
            "<code>Компания | Позиция | Дата Время | Платформа Ссылка</code>",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return
    
    try:
        service = InterviewService(session)
        interview = await service.create_interview(
            telegram_id=message.from_user.id,
            **parsed,
        )
        
        await state.clear()
        
        await message.answer(
            "✅ <b>Интервью добавлено!</b>\n\n"
            f"🏢 {parsed['company']}\n"
            f"💼 {parsed['position']}\n"
            f"📅 {parsed['interview_date'].strftime('%d.%m.%Y %H:%M')}",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_cancel_keyboard(),
        )


# ==================== VIEW INTERVIEWS ====================

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
        # Получаем timezone пользователя для правильного отображения дат
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        user_timezone = user.timezone if user else "Europe/Moscow"
        
        # Форматируем список с учетом часового пояса
        from app.utils.validators import TimezoneHelper
        
        interview_list = []
        for interview in interviews:
            date_str = TimezoneHelper.format_datetime(interview.interview_date, user_timezone)
            status_emoji = {
                InterviewStatus.SCHEDULED: "📅",
                InterviewStatus.COMPLETED: "✅",
                InterviewStatus.CANCELLED: "❌",
                InterviewStatus.RESCHEDULED: "🔄",
                InterviewStatus.OFFER: "🎉",
                InterviewStatus.REJECTED: "😞",
                InterviewStatus.WAITING_FEEDBACK: "⏳",
            }
            emoji = status_emoji.get(interview.status, "📋")
            
            interview_list.append(
                f"{emoji} <b>{interview.company_name}</b> - {interview.position}\n"
                f"   📅 {date_str}"
            )
        
        await callback.message.edit_text(
            f"📋 <b>Ваши предстоящие интервью</b> ({len(interviews)}):\n\n"
            + "\n\n".join(interview_list) +
            "\n\n<i>Нажмите на кнопку ниже, чтобы просмотреть детали</i>",
            reply_markup=get_interviews_keyboard(interviews, user_timezone),  # ПЕРЕДАЕМ timezone!
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
    
    # Получаем timezone пользователя
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    user_timezone = user.timezone if user else "Europe/Moscow"
    
    # Check if part of pipeline
    pipeline = await service.get_pipeline(interview.parent_interview_id or interview.id)
    has_pipeline = len(pipeline) > 1
    
    details = service.format_interview_details(
        interview, 
        include_history=True, 
        user_timezone=user_timezone
    )
    
    await callback.message.edit_text(
        details,
        reply_markup=get_interview_detail_keyboard(interview_id, has_pipeline),
        parse_mode="HTML",
    )
    await callback.answer()


    # ==================== EDIT INTERVIEW ====================

@router.callback_query(F.data.startswith("edit_interview_"))
async def show_edit_menu(callback: CallbackQuery, session: AsyncSession):
    """Show edit menu."""
    interview_id = int(callback.data.replace("edit_interview_", ""))
    
    await callback.message.edit_text(
        "✏️ <b>Редактирование интервью</b>\n\n"
        "Выберите, что хотите изменить:",
        reply_markup=get_edit_menu_keyboard(interview_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_date_"))
async def start_edit_date(callback: CallbackQuery, state: FSMContext):
    """Start editing date."""
    interview_id = int(callback.data.replace("edit_date_", ""))
    await state.update_data(interview_id=interview_id)
    await state.set_state(EditInterviewStates.waiting_for_date)
    
    await callback.message.edit_text(
        "📅 Введите новую дату и время\n"
        "(формат: ДД.ММ.ГГГГ ЧЧ:ММ):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(EditInterviewStates.waiting_for_date)
async def process_edit_date(message: Message, state: FSMContext, session: AsyncSession):
    """Process edited date."""
    try:
        # Получаем timezone пользователя
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        user_timezone = user.timezone if user else "Europe/Moscow"
        
        new_date = InputValidator.validate_datetime(message.text, user_timezone)
        data = await state.get_data()
        interview_id = data["interview_id"]
        
        service = InterviewService(session)
        await service.update_interview(interview_id, interview_date=new_date)
        
        await state.clear()
        
        from app.utils.validators import TimezoneHelper
        date_str = TimezoneHelper.format_datetime(new_date, user_timezone)
        
        await message.answer(
            f"✅ Дата изменена на {date_str}",
            reply_markup=get_interview_detail_keyboard(interview_id),
            parse_mode="HTML",
        )
        
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(F.data.startswith("edit_platform_url_"))
async def start_edit_platform_url(callback: CallbackQuery, state: FSMContext):
    """Start editing platform URL."""
    interview_id = int(callback.data.replace("edit_platform_url_", ""))
    await state.update_data(interview_id=interview_id)
    await state.set_state(EditInterviewStates.waiting_for_platform_url)
    
    await callback.message.edit_text(
        "🔗 Введите новую ссылку на встречу:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(EditInterviewStates.waiting_for_platform_url)
async def process_edit_platform_url(message: Message, state: FSMContext, session: AsyncSession):
    """Process edited platform URL."""
    try:
        new_url = InputValidator.validate_url(message.text)
        data = await state.get_data()
        interview_id = data["interview_id"]
        
        service = InterviewService(session)
        await service.update_interview(interview_id, platform_url=new_url)
        
        await state.clear()
        
        await message.answer(
            "✅ Ссылка обновлена",
            reply_markup=get_interview_detail_keyboard(interview_id),
            parse_mode="HTML",
        )
        
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(F.data.startswith("edit_position_"))
async def start_edit_position(callback: CallbackQuery, state: FSMContext):
    """Start editing position."""
    interview_id = int(callback.data.replace("edit_position_", ""))
    await state.update_data(interview_id=interview_id)
    await state.set_state(EditInterviewStates.waiting_for_position)
    
    await callback.message.edit_text(
        "💼 Введите новую позицию:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(EditInterviewStates.waiting_for_position)
async def process_edit_position(message: Message, state: FSMContext, session: AsyncSession):
    """Process edited position."""
    try:
        new_position = InputValidator.validate_text(message.text, max_length=255)
        data = await state.get_data()
        interview_id = data["interview_id"]
        
        service = InterviewService(session)
        await service.update_interview(interview_id, position=new_position)
        
        await state.clear()
        
        await message.answer(
            f"✅ Позиция изменена на: {new_position}",
            reply_markup=get_interview_detail_keyboard(interview_id),
            parse_mode="HTML",
        )
        
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


# ==================== STATUS CHANGE ====================

@router.callback_query(F.data.startswith("change_status_"))
async def show_status_menu(callback: CallbackQuery):
    """Show status change menu."""
    interview_id = int(callback.data.replace("change_status_", ""))
    
    await callback.message.edit_text(
        "📊 <b>Изменение статуса</b>\n\n"
        "Выберите новый статус:",
        reply_markup=get_status_keyboard(interview_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_status_"))
async def process_status_change(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Process status change."""
    parts = callback.data.replace("set_status_", "").split("_")
    interview_id = int(parts[0])
    status_name = parts[1]
    new_status = InterviewStatus[status_name]
    
    # Ask for notes
    await state.update_data(interview_id=interview_id, new_status=new_status)
    await state.set_state(StatusChangeStates.waiting_for_notes)
    
    await callback.message.edit_text(
        f"📊 Меняем статус на: <b>{new_status.value}</b>\n\n"
        "💭 Добавьте комментарий (или пропустите):",
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "skip", StatusChangeStates.waiting_for_notes)
async def skip_status_notes(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Skip status notes."""
    data = await state.get_data()
    await complete_status_change(data["interview_id"], data["new_status"], None, session, callback.message, state)
    await callback.answer()


@router.message(StatusChangeStates.waiting_for_notes)
async def process_status_notes(message: Message, state: FSMContext, session: AsyncSession):
    """Process status notes."""
    data = await state.get_data()
    await complete_status_change(data["interview_id"], data["new_status"], message.text, session, message, state)


async def complete_status_change(
    interview_id: int,
    new_status: InterviewStatus,
    notes: str,
    session: AsyncSession,
    message: Message,
    state: FSMContext,
):
    """Complete status change."""
    try:
        service = InterviewService(session)
        await service.change_status(interview_id, new_status, notes)
        
        await state.clear()
        
        await message.answer(
            f"✅ Статус изменен на: <b>{new_status.value}</b>",
            reply_markup=get_interview_detail_keyboard(interview_id),
            parse_mode="HTML",
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu_keyboard(),
        )
        await state.clear()


# ==================== RATING ====================

@router.callback_query(F.data.startswith("rate_interview_"))
async def show_rating_menu(callback: CallbackQuery):
    """Show rating menu."""
    interview_id = int(callback.data.replace("rate_interview_", ""))
    
    await callback.message.edit_text(
        "⭐️ <b>Оценка интервью</b>\n\n"
        "Как бы вы оценили это интервью?",
        reply_markup=get_rating_keyboard(interview_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("rate_"))
async def process_rating(callback: CallbackQuery, session: AsyncSession):
    """Process rating."""
    parts = callback.data.replace("rate_", "").split("_")
    interview_id = int(parts[0])
    rating = int(parts[1])
    
    service = InterviewService(session)
    await service.update_interview(interview_id, rating=rating)
    
    await callback.message.edit_text(
        f"✅ Оценка сохранена: {'⭐️' * rating}",
        reply_markup=get_interview_detail_keyboard(interview_id),
        parse_mode="HTML",
    )
    await callback.answer("✅ Оценка сохранена")


# ==================== CHECKLIST ====================

@router.callback_query(F.data.startswith("checklist_"))
async def show_checklist(callback: CallbackQuery, session: AsyncSession):
    """Show checklist."""
    interview_id = int(callback.data.replace("checklist_", ""))
    
    service = InterviewService(session)
    interview = await service.get_interview_by_id(interview_id)
    
    if not interview:
        await callback.answer("❌ Интервью не найдено", show_alert=True)
        return
    
    checklist_text = service.format_checklist(interview)
    
    await callback.message.edit_text(
        checklist_text,
        reply_markup=get_checklist_keyboard(interview_id, interview.checklist or []),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_check_"))
async def toggle_checklist_item(callback: CallbackQuery, session: AsyncSession):
    """Toggle checklist item."""
    parts = callback.data.replace("toggle_check_", "").split("_")
    interview_id = int(parts[0])
    item_index = int(parts[1])
    
    service = InterviewService(session)
    interview = await service.get_interview_by_id(interview_id)
    
    if interview and interview.checklist:
        current_state = interview.checklist[item_index]["checked"]
        await service.update_checklist(interview_id, item_index, not current_state)
        
        # Refresh checklist view
        interview = await service.get_interview_by_id(interview_id)
        checklist_text = service.format_checklist(interview)
        
        await callback.message.edit_text(
            checklist_text,
            reply_markup=get_checklist_keyboard(interview_id, interview.checklist),
            parse_mode="HTML",
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("add_checklist_"))
async def start_add_checklist_item(callback: CallbackQuery, state: FSMContext):
    """Start adding checklist item."""
    interview_id = int(callback.data.replace("add_checklist_", ""))
    await state.update_data(interview_id=interview_id)
    await state.set_state(ChecklistStates.waiting_for_item)
    
    await callback.message.edit_text(
        "📝 Введите текст нового пункта чек-листа:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(ChecklistStates.waiting_for_item)
async def process_add_checklist_item(message: Message, state: FSMContext, session: AsyncSession):
    """Process new checklist item."""
    data = await state.get_data()
    interview_id = data["interview_id"]
    
    service = InterviewService(session)
    await service.add_checklist_item(interview_id, message.text)
    
    await state.clear()
    
    # Show updated checklist
    interview = await service.get_interview_by_id(interview_id)
    checklist_text = service.format_checklist(interview)
    
    await message.answer(
        f"✅ Пункт добавлен\n\n{checklist_text}",
        reply_markup=get_checklist_keyboard(interview_id, interview.checklist),
        parse_mode="HTML",
    )


# ==================== NOTES ====================

@router.callback_query(F.data.startswith("notes_menu_"))
async def show_notes_menu(callback: CallbackQuery):
    """Show notes menu."""
    interview_id = int(callback.data.replace("notes_menu_", ""))
    
    await callback.message.edit_text(
        "📝 <b>Управление заметками</b>\n\n"
        "Выберите тип заметок:",
        reply_markup=get_notes_menu_keyboard(interview_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_prep_notes_"))
async def start_edit_prep_notes(callback: CallbackQuery, state: FSMContext):
    """Start editing preparation notes."""
    interview_id = int(callback.data.replace("edit_prep_notes_", ""))
    await state.update_data(interview_id=interview_id)
    await state.set_state(NotesStates.waiting_for_prep_notes)
    
    await callback.message.edit_text(
        "📝 <b>Заметки для подготовки</b>\n\n"
        "Введите заметки (что нужно подготовить, изучить и т.д.):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(NotesStates.waiting_for_prep_notes)
async def process_prep_notes(message: Message, state: FSMContext, session: AsyncSession):
    """Process preparation notes."""
    data = await state.get_data()
    interview_id = data["interview_id"]
    
    service = InterviewService(session)
    await service.update_interview(interview_id, preparation_notes=message.text)
    
    await state.clear()
    
    await message.answer(
        "✅ Заметки для подготовки сохранены",
        reply_markup=get_interview_detail_keyboard(interview_id),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("edit_post_notes_"))
async def start_edit_post_notes(callback: CallbackQuery, state: FSMContext):
    """Start editing post-interview notes."""
    interview_id = int(callback.data.replace("edit_post_notes_", ""))
    await state.update_data(interview_id=interview_id)
    await state.set_state(NotesStates.waiting_for_post_notes)
    
    await callback.message.edit_text(
        "💭 <b>Заметки после интервью</b>\n\n"
        "Введите заметки (как прошло, что спрашивали, впечатления):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(NotesStates.waiting_for_post_notes)
async def process_post_notes(message: Message, state: FSMContext, session: AsyncSession):
    """Process post-interview notes."""
    data = await state.get_data()
    interview_id = data["interview_id"]
    
    service = InterviewService(session)
    await service.update_interview(interview_id, post_interview_notes=message.text)
    
    await state.clear()
    
    await message.answer(
        "✅ Заметки после интервью сохранены",
        reply_markup=get_interview_detail_keyboard(interview_id),
        parse_mode="HTML",
    )


# ==================== PIPELINE ====================

@router.callback_query(F.data.startswith("pipeline_"))
async def show_pipeline(callback: CallbackQuery, session: AsyncSession):
    """Show interview pipeline."""
    interview_id = int(callback.data.replace("pipeline_", ""))
    
    service = InterviewService(session)
    pipeline = await service.get_pipeline(interview_id)
    
    if not pipeline:
        await callback.answer("❌ Этапы не найдены", show_alert=True)
        return
    
    # Получаем timezone пользователя
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    user_timezone = user.timezone if user else "Europe/Moscow"
    
    pipeline_text = service.format_pipeline(pipeline, user_timezone)
    
    await callback.message.edit_text(
        pipeline_text,
        reply_markup=get_pipeline_keyboard(pipeline, user_timezone),  # ПЕРЕДАЕМ timezone!
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add_next_stage_"))
async def add_next_stage(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Add next interview stage."""
    parent_id = int(callback.data.replace("add_next_stage_", ""))
    
    service = InterviewService(session)
    parent = await service.get_interview_by_id(parent_id)
    
    if not parent:
        await callback.answer("❌ Интервью не найдено", show_alert=True)
        return
    
    # Pre-fill data from parent
    await state.update_data(
        parent_interview_id=parent_id,
        company=parent.company_name,
        position=parent.position,
        vacancy_url=parent.vacancy_url,
        recruiter_name=parent.recruiter_name,
        platform_name=parent.platform_name,
        platform_url=parent.platform_url,
        camera_required=parent.camera_required,
    )
    
    await state.set_state(InterviewStates.waiting_for_interview_date)
    
    await callback.message.edit_text(
        f"➕ <b>Добавление следующего этапа</b>\n\n"
        f"🏢 Компания: {parent.company_name}\n"
        f"💼 Позиция: {parent.position}\n\n"
        "📅 Введите дату и время следующего этапа:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ==================== DELETE ====================

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


# ==================== SEARCH ====================

@router.callback_query(F.data == "search_interviews")
async def start_search(callback: CallbackQuery, state: FSMContext):
    """Start search."""
    await state.set_state(SearchStates.waiting_for_query)
    
    await callback.message.edit_text(
        "🔍 <b>Поиск интервью</b>\n\n"
        "Введите название компании, позицию или имя рекрутера:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(SearchStates.waiting_for_query)
async def process_search(message: Message, state: FSMContext, session: AsyncSession):
    """Process search query."""
    query = message.text
    
    service = InterviewService(session)
    results = await service.search_interviews(message.from_user.id, query)
    
    await state.clear()
    
    if not results:
        await message.answer(
            f"🔍 По запросу '<b>{query}</b>' ничего не найдено",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        # Получаем timezone пользователя
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        user_timezone = user.timezone if user else "Europe/Moscow"
        
        await message.answer(
            f"🔍 Найдено интервью: <b>{len(results)}</b>\n\n"
            f"По запросу: '{query}'",
            reply_markup=get_interviews_keyboard(results, user_timezone),  # ПЕРЕДАЕМ timezone!
            parse_mode="HTML",
        )


# ==================== STATISTICS ====================

@router.callback_query(F.data == "statistics")
async def show_statistics(callback: CallbackQuery, session: AsyncSession):
    """Show statistics."""
    service = InterviewService(session)
    stats = await service.get_statistics(callback.from_user.id)
    
    if not stats or stats["total"] == 0:
        await callback.message.edit_text(
            "📊 <b>Статистика</b>\n\n"
            "Пока нет данных для статистики.\n"
            "Добавьте интервью, чтобы увидеть статистику!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
    else:
        stats_text = service.format_statistics(stats)
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
    
    await callback.answer()