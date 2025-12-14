"""Inline keyboards for the bot."""
from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

from app.database.models import (
    Interview, 
    InterviewType, 
    InterviewStatus,
    Recruiter, 
    InterviewTemplate
)
# TimezoneHelper будет импортироваться внутри функций

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить интервью",
            callback_data="add_interview",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⚡️ Быстрое добавление",
            callback_data="quick_add",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📋 Мои интервью",
            callback_data="my_interviews",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔍 Поиск",
            callback_data="search_interviews",
        ),
        InlineKeyboardButton(
            text="📊 Статистика",
            callback_data="statistics",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👥 Рекрутеры",
            callback_data="recruiters_list",
        ),
        InlineKeyboardButton(
            text="📝 Шаблоны",
            callback_data="templates_list",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📤 Экспорт",
            callback_data="export_menu",
        ),
        InlineKeyboardButton(
            text="⚙️ Настройки",  # Изменено
            callback_data="settings_menu",  # Изменено
        )
    )
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Get cancel keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_skip_keyboard() -> InlineKeyboardMarkup:
    """Get skip keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_camera_keyboard() -> InlineKeyboardMarkup:
    """Get camera required keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data="camera_yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data="camera_no"),
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_interview_type_keyboard() -> InlineKeyboardMarkup:
    """Get interview type keyboard."""
    builder = InlineKeyboardBuilder()
    for interview_type in InterviewType:
        builder.row(
            InlineKeyboardButton(
                text=interview_type.value,
                callback_data=f"type_{interview_type.name}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_yes"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
    )
    return builder.as_markup()


def get_interviews_keyboard(
    interviews: List[Interview], 
    user_timezone: str = "Europe/Moscow"
) -> InlineKeyboardMarkup:
    """Get interviews list keyboard."""
    from app.utils.validators import TimezoneHelper
    
    builder = InlineKeyboardBuilder()
    
    for interview in interviews:
        # Форматируем дату с учетом timezone пользователя
        date_str = TimezoneHelper.format_datetime(interview.interview_date, user_timezone)
        # Берем только дату и время без года для компактности
        date_parts = date_str.split()
        if len(date_parts) >= 2:
            # Формат: "15.12.2024 17:00" -> "15.12 17:00"
            date_short = f"{date_parts[0].rsplit('.', 1)[0]} {date_parts[1]}"
        else:
            date_short = date_str
        
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
        
        # Короткое название для кнопки (максимум 20 символов от названия компании)
        company_short = interview.company_name[:20]
        button_text = f"{emoji} {company_short} ({date_short})"
        
        builder.row(
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"view_interview_{interview.id}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="↩️ Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()



def get_interview_detail_keyboard(interview_id: int, has_pipeline: bool = False) -> InlineKeyboardMarkup:
    """Get interview detail keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Редактировать",
            callback_data=f"edit_interview_{interview_id}",
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📊 Изменить статус",
            callback_data=f"change_status_{interview_id}",
        ),
        InlineKeyboardButton(
            text="⭐️ Оценить",
            callback_data=f"rate_interview_{interview_id}",
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Чек-лист",
            callback_data=f"checklist_{interview_id}",
        ),
        InlineKeyboardButton(
            text="💭 Заметки",
            callback_data=f"notes_menu_{interview_id}",
        )
    )
    
    if has_pipeline:
        builder.row(
            InlineKeyboardButton(
                text="🔄 Показать все этапы",
                callback_data=f"pipeline_{interview_id}",
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="➕ Добавить следующий этап",
                callback_data=f"add_next_stage_{interview_id}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"delete_interview_{interview_id}",
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="my_interviews")
    )
    return builder.as_markup()


def get_edit_menu_keyboard(interview_id: int) -> InlineKeyboardMarkup:
    """Get edit menu keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📅 Дата и время",
            callback_data=f"edit_date_{interview_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔗 Ссылка на встречу",
            callback_data=f"edit_platform_url_{interview_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👤 Рекрутер",
            callback_data=f"edit_recruiter_{interview_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💼 Позиция",
            callback_data=f"edit_position_{interview_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="↩️ Назад",
            callback_data=f"view_interview_{interview_id}",
        )
    )
    return builder.as_markup()


def get_status_keyboard(interview_id: int) -> InlineKeyboardMarkup:
    """Get status change keyboard."""
    builder = InlineKeyboardBuilder()
    
    statuses = [
        (InterviewStatus.SCHEDULED, "📅"),
        (InterviewStatus.COMPLETED, "✅"),
        (InterviewStatus.WAITING_FEEDBACK, "⏳"),
        (InterviewStatus.OFFER, "🎉"),
        (InterviewStatus.REJECTED, "😞"),
        (InterviewStatus.CANCELLED, "❌"),
        (InterviewStatus.RESCHEDULED, "🔄"),
    ]
    
    for status, emoji in statuses:
        builder.row(
            InlineKeyboardButton(
                text=f"{emoji} {status.value}",
                callback_data=f"set_status_{interview_id}_{status.name}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="↩️ Назад",
            callback_data=f"view_interview_{interview_id}",
        )
    )
    return builder.as_markup()


def get_rating_keyboard(interview_id: int) -> InlineKeyboardMarkup:
    """Get rating keyboard."""
    builder = InlineKeyboardBuilder()
    
    for i in range(1, 6):
        builder.add(
            InlineKeyboardButton(
                text="⭐️" * i,
                callback_data=f"rate_{interview_id}_{i}",
            )
        )
    
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(
            text="↩️ Назад",
            callback_data=f"view_interview_{interview_id}",
        )
    )
    return builder.as_markup()


def get_checklist_keyboard(interview_id: int, checklist: List[dict]) -> InlineKeyboardMarkup:
    """Get checklist keyboard."""
    builder = InlineKeyboardBuilder()
    
    for i, item in enumerate(checklist):
        checkbox = "☑️" if item["checked"] else "⬜️"
        builder.row(
            InlineKeyboardButton(
                text=f"{checkbox} {item['text']}",
                callback_data=f"toggle_check_{interview_id}_{i}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить пункт",
            callback_data=f"add_checklist_{interview_id}",
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="↩️ Назад",
            callback_data=f"view_interview_{interview_id}",
        )
    )
    return builder.as_markup()


def get_notes_menu_keyboard(interview_id: int) -> InlineKeyboardMarkup:
    """Get notes menu keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Заметки для подготовки",
            callback_data=f"edit_prep_notes_{interview_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💭 Заметки после интервью",
            callback_data=f"edit_post_notes_{interview_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="↩️ Назад",
            callback_data=f"view_interview_{interview_id}",
        )
    )
    return builder.as_markup()


def get_notification_settings_keyboard(enabled: bool, quiet_hours_enabled: bool = False) -> InlineKeyboardMarkup:
    """Get notification settings keyboard."""
    builder = InlineKeyboardBuilder()
    
    toggle_text = "🔕 Выключить уведомления" if enabled else "🔔 Включить уведомления"
    builder.row(
        InlineKeyboardButton(
            text=toggle_text,
            callback_data="toggle_notifications",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⏰ Изменить время уведомлений",
            callback_data="change_notification_times",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔄 Сбросить на стандартные",
            callback_data="reset_notification_times",
        )
    )
    
    quiet_text = "🔕 Тихие часы: вкл" if quiet_hours_enabled else "🔔 Тихие часы: выкл"
    builder.row(
        InlineKeyboardButton(
            text=quiet_text,
            callback_data="quiet_hours_settings",
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="↩️ Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()


def get_recruiters_keyboard(recruiters: List[Recruiter]) -> InlineKeyboardMarkup:
    """Get recruiters list keyboard."""
    builder = InlineKeyboardBuilder()
    
    for recruiter in recruiters:
        company = f" ({recruiter.company_name})" if recruiter.company_name else ""
        builder.row(
            InlineKeyboardButton(
                text=f"👤 {recruiter.name}{company}",
                callback_data=f"view_recruiter_{recruiter.id}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="➕ Добавить рекрутера",
            callback_data="add_recruiter",
        )
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()


def get_recruiter_detail_keyboard(recruiter_id: int) -> InlineKeyboardMarkup:
    """Get recruiter detail keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"delete_recruiter_{recruiter_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="recruiters_list")
    )
    return builder.as_markup()


def get_templates_keyboard(templates: List[InterviewTemplate]) -> InlineKeyboardMarkup:
    """Get templates list keyboard."""
    builder = InlineKeyboardBuilder()
    
    for template in templates:
        builder.row(
            InlineKeyboardButton(
                text=f"📝 {template.name}",
                callback_data=f"view_template_{template.id}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="➕ Создать шаблон",
            callback_data="add_template",
        )
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()


def get_template_detail_keyboard(template_id: int) -> InlineKeyboardMarkup:
    """Get template detail keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Использовать шаблон",
            callback_data=f"use_template_{template_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"delete_template_{template_id}",
        )
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="templates_list")
    )
    return builder.as_markup()


def get_export_menu_keyboard() -> InlineKeyboardMarkup:
    """Get export menu keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📅 Экспорт в календарь (.ics)",
            callback_data="export_ics",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📄 Экспорт в JSON",
            callback_data="export_json",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="💾 Создать резервную копию",
            callback_data="create_backup",
        )
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()


def get_pipeline_keyboard(
    interviews: List[Interview],
    user_timezone: str = "Europe/Moscow"
) -> InlineKeyboardMarkup:
    """Get pipeline keyboard."""
    from app.utils.validators import TimezoneHelper
    
    builder = InlineKeyboardBuilder()
    
    for interview in sorted(interviews, key=lambda x: x.stage_number):
        date_str = TimezoneHelper.format_datetime(interview.interview_date, user_timezone)
        # Короткий формат для кнопки
        date_parts = date_str.split()
        if len(date_parts) >= 2:
            date_short = f"{date_parts[0].rsplit('.', 1)[0]} {date_parts[1]}"
        else:
            date_short = date_str
            
        builder.row(
            InlineKeyboardButton(
                text=f"Этап {interview.stage_number}: {interview.interview_type.value} ({date_short})",
                callback_data=f"view_interview_{interview.id}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="↩️ Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()


def get_quiet_hours_keyboard() -> InlineKeyboardMarkup:
    """Get quiet hours keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="✅ Включить",
            callback_data="quiet_hours_enable",
        ),
        InlineKeyboardButton(
            text="❌ Выключить",
            callback_data="quiet_hours_disable",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⏰ Настроить время",
            callback_data="quiet_hours_set_time",
        )
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="notification_settings")
    )
    return builder.as_markup()