import uuid
from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# Personal Info Schemas
class PersonalInfoBase(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=100)
    linkedin_url: Optional[str] = Field(None, max_length=255)
    github_url: Optional[str] = Field(None, max_length=255)
    portfolio_url: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None


class PersonalInfoCreate(PersonalInfoBase):
    pass


class PersonalInfoResponse(PersonalInfoBase):
    id: uuid.UUID
    resume_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# Work Experience Schemas
class WorkExperienceBase(BaseModel):
    company: str = Field(..., max_length=150)
    position: str = Field(..., max_length=150)
    location: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None
    display_order: int = 0


class WorkExperienceCreate(WorkExperienceBase):
    pass


class WorkExperienceResponse(WorkExperienceBase):
    id: uuid.UUID
    resume_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# Education Schemas
class EducationBase(BaseModel):
    institution: str = Field(..., max_length=150)
    degree: str = Field(..., max_length=150)
    field_of_study: Optional[str] = Field(None, max_length=150)
    location: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[str] = Field(None, max_length=50)
    display_order: int = 0


class EducationCreate(EducationBase):
    pass


class EducationResponse(EducationBase):
    id: uuid.UUID
    resume_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# Skill Schemas
class SkillBase(BaseModel):
    name: str = Field(..., max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    proficiency_level: Optional[str] = Field(None, max_length=50)
    display_order: int = 0


class SkillCreate(SkillBase):
    pass


class SkillResponse(SkillBase):
    id: uuid.UUID
    resume_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# Project Schemas
class ProjectBase(BaseModel):
    title: str = Field(..., max_length=150)
    description: Optional[str] = None
    tech_stack: Optional[str] = Field(None, max_length=255)
    project_url: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    display_order: int = 0


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: uuid.UUID
    resume_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# Certification Schemas
class CertificationBase(BaseModel):
    name: str = Field(..., max_length=150)
    issuing_organization: Optional[str] = Field(None, max_length=150)
    issue_date: Optional[date] = None
    credential_url: Optional[str] = Field(None, max_length=255)
    display_order: int = 0


class CertificationCreate(CertificationBase):
    pass


class CertificationResponse(CertificationBase):
    id: uuid.UUID
    resume_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# Custom Section Schemas
class CustomSectionBase(BaseModel):
    section_title: str = Field(..., max_length=150)
    content: Optional[str] = None
    display_order: int = 0


class CustomSectionCreate(CustomSectionBase):
    pass


class CustomSectionResponse(CustomSectionBase):
    id: uuid.UUID
    resume_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
