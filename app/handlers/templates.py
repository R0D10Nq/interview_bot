"""Template management handlers."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.states.interview_states import TemplateStates, UseTemplateStates
from app.keyboards.inline import (
    get_templates_keyboard,
    get_template_detail_keyboard,
    get_cancel_keyboard,
    get_skip_keyboard,
    get_camera_keyboard,
    get_interview_type_keyboard,
    get_confirm_keyboard,
    get_main_menu_keyboard,
)
from app.database.models import InterviewType
from app.database.repositories import TemplateRepository, UserRepository
from app.services.interview_service import InterviewService
from app.utils.validators import InputValidator, ValidationError
from app.utils.validators import TimezoneHelper  # где используется

router = Router()


@router.callback_query(F.data == "templates_list")
async def show_templates(callback: CallbackQuery, session: AsyncSession):
    """Show templates list."""
    user_repo = UserRepository(session)
    template_repo = TemplateRepository(session)
    
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    templates = await template_repo.get_user_templates(user.id)
    
    if not templates:
        await callback.message.edit_text(
            "📝 <b>Список шаблонов пуст</b>\n\n"
            "Создайте шаблоны для быстрого добавления интервью",
            reply_markup=get_templates_keyboard([]),
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            f"📝 <b>Ваши шаблоны</b> ({len(templates)}):\n\n"
            "Выберите шаблон:",
            reply_markup=get_templates_keyboard(templates),
            parse_mode="HTML",
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("view_template_"))
async def view_template(callback: CallbackQuery, session: AsyncSession):
    """View template details."""
    template_id = int(callback.data.replace("view_template_", ""))
    
    template_repo = TemplateRepository(session)
    template = await template_repo.get_by_id(template_id)
    
    if not template:
        await callback.answer("❌ Шаблон не найден", show_alert=True)
        return
    
    camera_text = "✅ Да" if template.camera_required else "❌ Нет"
    
    details = [
        f"📝 <b>{template.name}</b>\n",
        f"💻 <b>Платформа:</b> {template.platform_name}",
    ]
    
    if template.platform_url:
        details.append(f"🔗 <b>Ссылка:</b> {template.platform_url}")
    
    details.extend([
        f"📹 <b>Камера:</b> {camera_text}",
        f"📋 <b>Тип:</b> {template.interview_type.value}",
    ])
    
    await callback.message.edit_text(
        "\n".join(details),
        reply_markup=get_template_detail_keyboard(template_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "add_template")
async def start_add_template(callback: CallbackQuery, state: FSMContext):
    """Start adding template."""
    await state.set_state(TemplateStates.waiting_for_name)
    
    await callback.message.edit_text(
        "➕ <b>Создание шаблона</b>\n\n"
        "Введите название шаблона:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(TemplateStates.waiting_for_name)
async def process_template_name(message: Message, state: FSMContext):
    """Process template name."""
    try:
        name = InputValidator.validate_text(message.text, max_length=255)
        await state.update_data(name=name)
        await state.set_state(TemplateStates.waiting_for_platform_name)
        
        await message.answer(
            f"✅ Название: <b>{name}</b>\n\n"
            "💻 Введите название платформы:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.message(TemplateStates.waiting_for_platform_name)
async def process_template_platform_name(message: Message, state: FSMContext):
    """Process template platform name."""
    try:
        platform_name = InputValidator.validate_text(message.text, max_length=255)
        await state.update_data(platform_name=platform_name)
        await state.set_state(TemplateStates.waiting_for_platform_url)
        
        await message.answer(
            f"✅ Платформа: <b>{platform_name}</b>\n\n"
            "🔗 Введите ссылку (или пропустите):",
            reply_markup=get_skip_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(F.data == "skip", TemplateStates.waiting_for_platform_url)
async def skip_template_platform_url(callback: CallbackQuery, state: FSMContext):
    """Skip template platform URL."""
    await state.update_data(platform_url=None)
    await state.set_state(TemplateStates.waiting_for_camera)
    
    await callback.message.edit_text(
        "📹 Требуется ли камера?",
        reply_markup=get_camera_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(TemplateStates.waiting_for_platform_url)
async def process_template_platform_url(message: Message, state: FSMContext):
    """Process template platform URL."""
    try:
        platform_url = InputValidator.validate_url(message.text)
        await state.update_data(platform_url=platform_url)
        await state.set_state(TemplateStates.waiting_for_camera)
        
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


@router.callback_query(F.data.in_(["camera_yes", "camera_no"]), TemplateStates.waiting_for_camera)
async def process_template_camera(callback: CallbackQuery, state: FSMContext):
    """Process template camera requirement."""
    camera_required = callback.data == "camera_yes"
    await state.update_data(camera_required=camera_required)
    await state.set_state(TemplateStates.waiting_for_type)
    
    await callback.message.edit_text(
        "📝 Выберите тип интервью:",
        reply_markup=get_interview_type_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("type_"), TemplateStates.waiting_for_type)
async def process_template_type(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Process template type and save."""
    type_name = callback.data.replace("type_", "")
    interview_type = InterviewType[type_name]
    
    data = await state.get_data()
    
    user_repo = UserRepository(session)
    template_repo = TemplateRepository(session)
    
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("❌ Ошибка", show_alert=True)
        await state.clear()
        return
    
    template = await template_repo.create(
        user_id=user.id,
        name=data["name"],
        platform_name=data["platform_name"],
        platform_url=data.get("platform_url"),
        camera_required=data["camera_required"],
        interview_type=interview_type,
    )
    
    await state.clear()
    
    await callback.message.edit_text(
        f"✅ Шаблон <b>{template.name}</b> успешно создан!",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer("✅ Шаблон создан")


@router.callback_query(F.data.startswith("use_template_"))
async def start_use_template(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start using template."""
    template_id = int(callback.data.replace("use_template_", ""))
    
    template_repo = TemplateRepository(session)
    template = await template_repo.get_by_id(template_id)
    
    if not template:
        await callback.answer("❌ Шаблон не найден", show_alert=True)
        return
    
    await state.update_data(template_id=template_id)
    await state.set_state(UseTemplateStates.waiting_for_company)
    
    await callback.message.edit_text(
        f"📝 <b>Использование шаблона: {template.name}</b>\n\n"
        "🏢 Введите название компании:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(UseTemplateStates.waiting_for_company)
async def process_use_template_company(message: Message, state: FSMContext):
    """Process company for template."""
    try:
        company = InputValidator.validate_text(message.text, max_length=255)
        await state.update_data(company=company)
        await state.set_state(UseTemplateStates.waiting_for_position)
        
        await message.answer(
            f"✅ Компания: <b>{company}</b>\n\n"
            "💼 Введите позицию:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.message(UseTemplateStates.waiting_for_position)
async def process_use_template_position(message: Message, state: FSMContext):
    """Process position for template."""
    try:
        position = InputValidator.validate_text(message.text, max_length=255)
        await state.update_data(position=position)
        await state.set_state(UseTemplateStates.waiting_for_recruiter)
        
        await message.answer(
            f"✅ Позиция: <b>{position}</b>\n\n"
            "👤 Введите имя рекрутера:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.message(UseTemplateStates.waiting_for_recruiter)
async def process_use_template_recruiter(message: Message, state: FSMContext):
    """Process recruiter for template."""
    try:
        recruiter_name = InputValidator.validate_text(message.text, max_length=255)
        await state.update_data(recruiter_name=recruiter_name)
        await state.set_state(UseTemplateStates.waiting_for_date)
        
        await message.answer(
            f"✅ Рекрутер: <b>{recruiter_name}</b>\n\n"
            "📅 Введите дату и время интервью:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.message(UseTemplateStates.waiting_for_date)
async def process_use_template_date(message: Message, state: FSMContext, session: AsyncSession):
    """Process date for template."""
    try:
        # Получаем timezone пользователя
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        user_timezone = user.timezone if user else "Europe/Moscow"
        
        interview_date = InputValidator.validate_datetime(message.text, user_timezone)
        await state.update_data(interview_date=interview_date)
        await state.set_state(UseTemplateStates.waiting_for_vacancy_url)
        
        from app.utils.validators import TimezoneHelper
        date_str = TimezoneHelper.format_datetime(interview_date, user_timezone)
        
        await message.answer(
            f"✅ Дата: <b>{date_str}</b>\n\n"
            "🔗 Введите ссылку на вакансию (или пропустите):",
            reply_markup=get_skip_keyboard(),
            parse_mode="HTML",
        )
    except ValidationError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\nПопробуйте снова:",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(F.data == "skip", UseTemplateStates.waiting_for_vacancy_url)
async def skip_use_template_vacancy_url(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Skip vacancy URL and create interview from template."""
    await state.update_data(vacancy_url=None)
    await create_from_template(callback.message, state, session)
    await callback.answer()


@router.message(UseTemplateStates.waiting_for_vacancy_url)
async def process_use_template_vacancy_url(message: Message, state: FSMContext, session: AsyncSession):
    """Process vacancy URL and create interview from template."""
    try:
        vacancy_url = InputValidator.validate_url(message.text)
        await state.update_data(vacancy_url=vacancy_url)
    except ValidationError:
        await state.update_data(vacancy_url=None)
    
    await create_from_template(message, state, session)


async def create_from_template(message: Message, state: FSMContext, session: AsyncSession):
    """Create interview from template."""
    data = await state.get_data()
    
    try:
        service = InterviewService(session)
        interview = await service.create_from_template(
            telegram_id=message.from_user.id if hasattr(message, 'from_user') else message.chat.id,
            template_id=data["template_id"],
            company_name=data["company"],
            position=data["position"],
            recruiter_name=data["recruiter_name"],
            interview_date=data["interview_date"],
            vacancy_url=data.get("vacancy_url"),
        )
        
        await state.clear()
        
        await message.answer(
            "✅ <b>Интервью создано из шаблона!</b>",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu_keyboard(),
        )
        await state.clear()


@router.callback_query(F.data.startswith("delete_template_"))
async def delete_template(callback: CallbackQuery, session: AsyncSession):
    """Delete template."""
    template_id = int(callback.data.replace("delete_template_", ""))
    
    template_repo = TemplateRepository(session)
    success = await template_repo.delete(template_id)
    
    if success:
        await callback.message.edit_text(
            "✅ Шаблон удален",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer("✅ Удалено")
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)