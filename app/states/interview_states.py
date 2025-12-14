"""FSM states for interview creation."""
from aiogram.fsm.state import State, StatesGroup


class InterviewStates(StatesGroup):
    """States for interview creation process."""
    
    waiting_for_company = State()
    waiting_for_position = State()
    waiting_for_vacancy_url = State()
    waiting_for_recruiter_name = State()
    waiting_for_interview_date = State()
    waiting_for_platform_name = State()
    waiting_for_platform_url = State()
    waiting_for_camera = State()
    waiting_for_interview_type = State()
    waiting_for_preparation_notes = State()
    confirm = State()


class QuickAddStates(StatesGroup):
    """States for quick add."""
    
    waiting_for_input = State()


class EditInterviewStates(StatesGroup):
    """States for editing interview."""
    
    waiting_for_date = State()
    waiting_for_platform_url = State()
    waiting_for_recruiter = State()
    waiting_for_position = State()


class NotesStates(StatesGroup):
    """States for notes."""
    
    waiting_for_prep_notes = State()
    waiting_for_post_notes = State()


class NotificationSettingsStates(StatesGroup):
    """States for notification settings."""
    
    waiting_for_custom_times = State()
    waiting_for_quiet_hours = State()


class SearchStates(StatesGroup):
    """States for search."""
    
    waiting_for_query = State()


class RecruiterStates(StatesGroup):
    """States for recruiter management."""
    
    waiting_for_name = State()
    waiting_for_company = State()
    waiting_for_email = State()
    waiting_for_phone = State()
    waiting_for_telegram = State()
    waiting_for_notes = State()


class TemplateStates(StatesGroup):
    """States for template creation."""
    
    waiting_for_name = State()
    waiting_for_platform_name = State()
    waiting_for_platform_url = State()
    waiting_for_camera = State()
    waiting_for_type = State()


class UseTemplateStates(StatesGroup):
    """States for using template."""
    
    waiting_for_company = State()
    waiting_for_position = State()
    waiting_for_recruiter = State()
    waiting_for_date = State()
    waiting_for_vacancy_url = State()
    confirm = State()


class ChecklistStates(StatesGroup):
    """States for checklist."""
    
    waiting_for_item = State()


class StatusChangeStates(StatesGroup):
    """States for status change."""
    
    waiting_for_notes = State()


class UserSettingsStates(StatesGroup):
    """States for user settings."""
    
    waiting_for_timezone = State()