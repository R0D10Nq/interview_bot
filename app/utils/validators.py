"""Validators for user input."""
from datetime import datetime
from typing import Optional, Tuple
import re
import pytz
from app.database.repositories import UserRepository


class ValidationError(Exception):
    """Validation error exception."""
    pass


class InputValidator:
    """Validator for user inputs."""
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Validate URL format."""
        url = url.strip()
        if not url:
            raise ValidationError("URL не может быть пустым")
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        
        if not url_pattern.match(url):
            raise ValidationError(
                "Некорректный формат URL. Пример: https://example.com"
            )
        
        return url
    
    @staticmethod
    def validate_datetime(date_str: str, user_timezone: str = "Europe/Moscow") -> datetime:
        """
        Validate and parse datetime string.
        Returns timezone-aware datetime in UTC.
        """
        date_str = date_str.strip()
        
        # Try different formats
        formats = [
            "%d.%m.%Y %H:%M",
            "%d.%m.%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d %H:%M",
            "%d.%m.%y %H:%M",
        ]
        
        dt = None
        for fmt in formats:
            try:
                # Parse as naive datetime
                dt = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if dt is None:
            raise ValidationError(
                "Некорректный формат даты. "
                "Используйте формат: ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.12.2024 14:30)"
            )
        
        # Convert to timezone-aware datetime in user's timezone
        try:
            user_tz = pytz.timezone(user_timezone)
            dt_aware = user_tz.localize(dt)
        except Exception:
            # Fallback to UTC if timezone is invalid
            dt_aware = pytz.UTC.localize(dt)
        
        # Convert to UTC for storage
        dt_utc = dt_aware.astimezone(pytz.UTC)
        
        # Check if date is in the future (in user's timezone)
        now_user_tz = datetime.now(user_tz)
        if dt_aware <= now_user_tz:
            raise ValidationError(
                "Дата интервью должна быть в будущем"
            )
        
        return dt_utc
    
    @staticmethod
    def validate_text(text: str, min_length: int = 1, max_length: int = 255) -> str:
        """Validate text length."""
        text = text.strip()
        
        if len(text) < min_length:
            raise ValidationError(
                f"Текст должен содержать минимум {min_length} символов"
            )
        
        if len(text) > max_length:
            raise ValidationError(
                f"Текст не должен превышать {max_length} символов"
            )
        
        return text
    
    @staticmethod
    def validate_notification_times(times_str: str) -> list[float]:
        """Validate custom notification times."""
        times_str = times_str.strip()
        
        try:
            # Parse comma-separated values
            times = [float(t.strip()) for t in times_str.split(',')]
            
            # Validate each time
            for time in times:
                if time <= 0:
                    raise ValidationError(
                        "Время уведомления должно быть положительным числом"
                    )
                if time > 168:  # 1 week
                    raise ValidationError(
                        "Время уведомления не должно превышать 168 часов (1 неделя)"
                    )
            
            # Remove duplicates and sort
            times = sorted(set(times), reverse=True)
            
            return times
            
        except ValueError:
            raise ValidationError(
                "Некорректный формат. Используйте числа через запятую, "
                "например: 24, 12, 6, 3, 1.5, 0.5"
            )
    
    @staticmethod
    def validate_timezone(timezone_str: str) -> str:
        """Validate timezone string."""
        timezone_str = timezone_str.strip()
        
        try:
            # Try to create timezone object
            pytz.timezone(timezone_str)
            return timezone_str
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValidationError(
                f"Неизвестный часовой пояс: {timezone_str}\n\n"
                f"Примеры: Europe/Moscow, Asia/Tomsk, Europe/London"
            )


class TimezoneHelper:
    """Helper for timezone operations."""
    
    @staticmethod
    def format_datetime(dt: datetime, user_timezone: str = "Europe/Moscow") -> str:
        """
        Format datetime for display in user's timezone.
        Input: timezone-aware datetime in UTC
        Output: formatted string in user's timezone
        """
        if dt.tzinfo is None:
            # If naive, assume UTC
            dt = pytz.UTC.localize(dt)
        
        try:
            user_tz = pytz.timezone(user_timezone)
            dt_local = dt.astimezone(user_tz)
            return dt_local.strftime("%d.%m.%Y %H:%M")
        except Exception:
            # Fallback to UTC
            return dt.strftime("%d.%m.%Y %H:%M UTC")
    
    @staticmethod
    def get_popular_timezones() -> list[tuple[str, str]]:
        """Get list of popular timezones with descriptions."""
        return [
            ("Europe/Kaliningrad", "Калининград (UTC+2)"),
            ("Europe/Moscow", "Москва (UTC+3)"),
            ("Europe/Samara", "Самара (UTC+4)"),
            ("Asia/Yekaterinburg", "Екатеринбург (UTC+5)"),
            ("Asia/Omsk", "Омск (UTC+6)"),
            ("Asia/Novosibirsk", "Новосибирск (UTC+7)"),
            ("Asia/Krasnoyarsk", "Красноярск (UTC+7)"),
            ("Asia/Irkutsk", "Иркутск (UTC+8)"),
            ("Asia/Yakutsk", "Якутск (UTC+9)"),
            ("Asia/Vladivostok", "Владивосток (UTC+10)"),
            ("Asia/Magadan", "Магадан (UTC+11)"),
            ("Asia/Kamchatka", "Камчатка (UTC+12)"),
        ]