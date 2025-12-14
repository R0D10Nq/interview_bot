"""Validators for user input."""
from datetime import datetime
from typing import Optional, Tuple
import re


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
    def validate_datetime(date_str: str) -> datetime:
        """Validate and parse datetime string."""
        date_str = date_str.strip()
        
        # Try different formats
        formats = [
            "%d.%m.%Y %H:%M",
            "%d.%m.%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%Y-%m-%d %H:%M",
            "%d.%m.%y %H:%M",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # Check if date is in the future
                if dt <= datetime.now():
                    raise ValidationError(
                        "Дата интервью должна быть в будущем"
                    )
                return dt
            except ValueError:
                continue
        
        raise ValidationError(
            "Некорректный формат даты. "
            "Используйте формат: ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.12.2024 14:30)"
        )
    
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