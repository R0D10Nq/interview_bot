"""Database models."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    BigInteger,
    String,
    DateTime,
    Boolean,
    Text,
    JSON,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database.database import Base


class InterviewType(enum.Enum):
    """Interview type enumeration."""
    SCREENING = "Скрининг"
    TECHNICAL = "Техническое"
    LIVE_CODING = "Лайв-кодинг"
    HR = "HR интервью"
    FINAL = "Финальное"


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    
    # Relationships
    interviews: Mapped[List["Interview"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notification_settings: Mapped[Optional["NotificationSettings"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Interview(Base):
    """Interview model."""
    
    __tablename__ = "interviews"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    company: Mapped[str] = mapped_column(String(255))
    position: Mapped[str] = mapped_column(String(255))
    vacancy_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recruiter_name: Mapped[str] = mapped_column(String(255))
    
    interview_date: Mapped[datetime] = mapped_column(DateTime)
    
    platform_name: Mapped[str] = mapped_column(String(255))
    platform_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    camera_required: Mapped[bool] = mapped_column(Boolean, default=False)
    interview_type: Mapped[InterviewType] = mapped_column(
        SQLEnum(InterviewType),
        default=InterviewType.SCREENING,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="interviews")
    notification_logs: Mapped[List["NotificationLog"]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
    )


class NotificationSettings(Base):
    """Notification settings model."""
    
    __tablename__ = "notification_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )
    
    # Notification times in hours before interview (stored as JSON)
    notification_times: Mapped[List[float]] = mapped_column(
        JSON,
        default=list,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="notification_settings")


class NotificationLog(Base):
    """Notification log model."""
    
    __tablename__ = "notification_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE")
    )
    
    notification_time_hours: Mapped[float] = mapped_column()  # Hours before interview
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    interview: Mapped["Interview"] = relationship(back_populates="notification_logs")