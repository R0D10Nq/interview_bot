"""Inline keyboards for the bot."""
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.models import Interview, InterviewType


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
            text="📋 Мои интервью",
            callback_data="my_interviews",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⚙️ Настройки уведомлений",
            callback_data="notification_settings",
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


def get_interviews_keyboard(interviews: List[Interview]) -> InlineKeyboardMarkup:
    """Get interviews list keyboard."""
    builder = InlineKeyboardBuilder()
    
    for interview in interviews:
        date_str = interview.interview_date.strftime("%d.%m.%Y %H:%M")
        builder.row(
            InlineKeyboardButton(
                text=f"{interview.company} - {interview.position} ({date_str})",
                callback_data=f"view_interview_{interview.id}",
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="↩️ Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()


def get_interview_detail_keyboard(interview_id: int) -> InlineKeyboardMarkup:
    """Get interview detail keyboard."""
    builder = InlineKeyboardBuilder()
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


def get_notification_settings_keyboard(enabled: bool) -> InlineKeyboardMarkup:
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
    builder.row(
        InlineKeyboardButton(text="↩️ Главное меню", callback_data="main_menu")
    )
    return builder.as_markup()