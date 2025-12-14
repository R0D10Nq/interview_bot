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
    confirm = State()


class NotificationSettingsStates(StatesGroup):
    """States for notification settings."""
    
    waiting_for_custom_times = State()