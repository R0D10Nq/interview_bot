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
    Float,
    Integer,
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
    SYSTEM_DESIGN = "System Design"
    CULTURAL = "Культурное"
    FINAL = "Финальное"


class InterviewStatus(enum.Enum):
    """Interview status enumeration."""
    SCHEDULED = "Запланировано"
    COMPLETED = "Прошло"
    CANCELLED = "Отменено"
    RESCHEDULED = "Перенесено"
    OFFER = "Получен оффер 🎉"
    REJECTED = "Отказ"
    WAITING_FEEDBACK = "Жду ответа"


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    locale: Mapped[str] = mapped_column(String(10), default="ru")
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Moscow")
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
    recruiters: Mapped[List["Recruiter"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    templates: Mapped[List["InterviewTemplate"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Company(Base):
    """Company model for grouping interviews."""
    
    __tablename__ = "companies"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), index=True)
    website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interviews: Mapped[List["Interview"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )


class Recruiter(Base):
    """Recruiter contact model."""
    
    __tablename__ = "recruiters"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    telegram: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="recruiters")
    interviews: Mapped[List["Interview"]] = relationship(back_populates="recruiter")


class Interview(Base):
    """Interview model."""
    
    __tablename__ = "interviews"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    company_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
    )
    recruiter_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("recruiters.id", ondelete="SET NULL"),
        nullable=True,
    )
    parent_interview_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("interviews.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Basic info
    company_name: Mapped[str] = mapped_column(String(255))
    position: Mapped[str] = mapped_column(String(255))
    vacancy_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recruiter_name: Mapped[str] = mapped_column(String(255))
    
    # Interview details
    interview_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    original_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    platform_name: Mapped[str] = mapped_column(String(255))
    platform_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    camera_required: Mapped[bool] = mapped_column(Boolean, default=False)
    interview_type: Mapped[InterviewType] = mapped_column(
        SQLEnum(InterviewType),
        default=InterviewType.SCREENING,
    )
    status: Mapped[InterviewStatus] = mapped_column(
        SQLEnum(InterviewStatus),
        default=InterviewStatus.SCHEDULED,
        index=True,
    )
    
    # Notes and feedback
    preparation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    post_interview_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    
    # Checklist (JSON array of items)
    checklist: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    
    # Metadata
    stage_number: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="interviews")
    company: Mapped[Optional["Company"]] = relationship(back_populates="interviews")
    recruiter: Mapped[Optional["Recruiter"]] = relationship(back_populates="interviews")
    notification_logs: Mapped[List["NotificationLog"]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
    )
    followups: Mapped[List["FollowUp"]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
    )
    status_history: Mapped[List["InterviewStatusHistory"]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
    )
    
    # Self-referential relationship for pipeline
    parent_interview: Mapped[Optional["Interview"]] = relationship(
        remote_side=[id],
        backref="child_interviews",
    )


class InterviewStatusHistory(Base):
    """Interview status change history."""
    
    __tablename__ = "interview_status_history"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE")
    )
    old_status: Mapped[Optional[InterviewStatus]] = mapped_column(
        SQLEnum(InterviewStatus),
        nullable=True,
    )
    new_status: Mapped[InterviewStatus] = mapped_column(SQLEnum(InterviewStatus))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interview: Mapped["Interview"] = relationship(back_populates="status_history")


class FollowUp(Base):
    """Follow-up reminder model."""
    
    __tablename__ = "followups"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE")
    )
    reminder_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    message: Mapped[str] = mapped_column(Text)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interview: Mapped["Interview"] = relationship(back_populates="followups")


class NotificationSettings(Base):
    """Notification settings model."""
    
    __tablename__ = "notification_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )
    
    # Notification times in hours before interview (stored as JSON)
    notification_times: Mapped[List[float]] = mapped_column(JSON, default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Quiet hours
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # HH:MM
    
    # Grouping
    group_notifications: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="notification_settings")


class NotificationLog(Base):
    """Notification log model."""
    
    __tablename__ = "notification_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE")
    )
    
    notification_type: Mapped[str] = mapped_column(String(50))  # interview, followup, etc.
    notification_time_hours: Mapped[Optional[float]] = mapped_column(nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    interview: Mapped["Interview"] = relationship(back_populates="notification_logs")


class InterviewTemplate(Base):
    """Interview template model."""
    
    __tablename__ = "interview_templates"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    
    name: Mapped[str] = mapped_column(String(255))
    platform_name: Mapped[str] = mapped_column(String(255))
    platform_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    camera_required: Mapped[bool] = mapped_column(Boolean, default=False)
    interview_type: Mapped[InterviewType] = mapped_column(SQLEnum(InterviewType))
    default_checklist: Mapped[Optional[List[dict]]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="templates")


class Backup(Base):
    """Backup metadata model."""
    
    __tablename__ = "backups"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    filepath: Mapped[str] = mapped_column(Text)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)