import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.sections import (
    PersonalInfoCreate, PersonalInfoResponse,
    WorkExperienceCreate, WorkExperienceResponse,
    EducationCreate, EducationResponse,
    SkillCreate, SkillResponse,
    ProjectCreate, ProjectResponse,
    CertificationCreate, CertificationResponse,
    CustomSectionCreate, CustomSectionResponse,
)


class ResumeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    template_id: str = Field("modern", max_length=50)
    theme_config: Optional[Dict[str, Any]] = None


class ResumeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    template_id: Optional[str] = Field(None, max_length=50)
    theme_config: Optional[Dict[str, Any]] = None
    personal_info: Optional[PersonalInfoCreate] = None
    work_experiences: Optional[List[WorkExperienceCreate]] = None
    education: Optional[List[EducationCreate]] = None
    skills: Optional[List[SkillCreate]] = None
    projects: Optional[List[ProjectCreate]] = None
    certifications: Optional[List[CertificationCreate]] = None
    custom_sections: Optional[List[CustomSectionCreate]] = None


class ResumeSummaryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    template_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeDetailResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    template_id: str
    theme_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    personal_info: Optional[PersonalInfoResponse] = None
    work_experiences: List[WorkExperienceResponse] = []
    education: List[EducationResponse] = []
    skills: List[SkillResponse] = []
    projects: List[ProjectResponse] = []
    certifications: List[CertificationResponse] = []
    custom_sections: List[CustomSectionResponse] = []

    model_config = ConfigDict(from_attributes=True)
