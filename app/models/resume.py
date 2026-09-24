import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List, Dict, Any
from sqlalchemy import String, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.sections import (
        PersonalInfo,
        WorkExperience,
        Education,
        Skill,
        Project,
        Certification,
        CustomSection,
    )


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    template_id: Mapped[str] = mapped_column(String(50), default="modern", nullable=False)
    theme_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="resumes")

    personal_info: Mapped[Optional["PersonalInfo"]] = relationship(
        "PersonalInfo", back_populates="resume", uselist=False, cascade="all, delete-orphan"
    )
    work_experiences: Mapped[List["WorkExperience"]] = relationship(
        "WorkExperience", back_populates="resume", cascade="all, delete-orphan", order_by="WorkExperience.display_order"
    )
    education: Mapped[List["Education"]] = relationship(
        "Education", back_populates="resume", cascade="all, delete-orphan", order_by="Education.display_order"
    )
    skills: Mapped[List["Skill"]] = relationship(
        "Skill", back_populates="resume", cascade="all, delete-orphan", order_by="Skill.display_order"
    )
    projects: Mapped[List["Project"]] = relationship(
        "Project", back_populates="resume", cascade="all, delete-orphan", order_by="Project.display_order"
    )
    certifications: Mapped[List["Certification"]] = relationship(
        "Certification", back_populates="resume", cascade="all, delete-orphan", order_by="Certification.display_order"
    )
    custom_sections: Mapped[List["CustomSection"]] = relationship(
        "CustomSection", back_populates="resume", cascade="all, delete-orphan", order_by="CustomSection.display_order"
    )
