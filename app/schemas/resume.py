import uuid
import base64
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.sections import (
    PersonalInfoCreate, PersonalInfoResponse,
    WorkExperienceCreate, WorkExperienceResponse,
    EducationCreate, EducationResponse,
    SkillCreate, SkillResponse,
    ProjectCreate, ProjectResponse,
    CertificationCreate, CertificationResponse,
    CustomSectionCreate, CustomSectionResponse,
)


def validate_photo_url(v: Any) -> None:
    if v is None:
        return
    if not isinstance(v, str):
        raise ValueError("photo_url must be a string")
    
    if len(v) > 500_000:
        raise ValueError("photo_url payload exceeds maximum allowed size")
    
    match = re.match(r"^data:image/(jpeg|png|webp);base64,([A-Za-z0-9+/=]+)$", v)
    if not match:
        raise ValueError("photo_url must be a valid base64 data URL with JPEG, PNG, or WebP MIME type")
    
    b64_str = match.group(2)
    try:
        decoded = base64.b64decode(b64_str, validate=True)
        if len(decoded) == 0:
            raise ValueError("photo_url contains empty image payload")
    except Exception:
        raise ValueError("photo_url contains invalid base64 payload")


def validate_primary_color(color: Any) -> None:
    if color is None:
        return
    if not isinstance(color, str):
        raise ValueError("primary_color must be a string")
    
    clean_color = color.strip()
    hex_pattern = r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$"
    rgb_pattern = r"^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(?:,\s*(?:0|1|0?\.\d+)\s*)?\)$"
    hsl_pattern = r"^hsla?\(\s*\d+\s*,\s*\d+%\s*,\s*\d+%\s*(?:,\s*(?:0|1|0?\.\d+)\s*)?\)$"
    named_pattern = r"^[a-zA-Z]{3,20}$"
    
    if not (re.match(hex_pattern, clean_color) or 
            re.match(rgb_pattern, clean_color, re.IGNORECASE) or 
            re.match(hsl_pattern, clean_color, re.IGNORECASE) or 
            re.match(named_pattern, clean_color)):
        raise ValueError("primary_color must be a valid hex, RGB, HSL, or named CSS color")


class ResumeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    template_id: str = Field("modern", max_length=50)
    theme_config: Optional[Dict[str, Any]] = None

    @field_validator("theme_config", mode="after")
    @classmethod
    def validate_theme_config(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("theme_config must be a dictionary")
        if "primary_color" in v and v["primary_color"] is not None:
            validate_primary_color(v["primary_color"])
        if "photo_url" in v and v["photo_url"] is not None:
            validate_photo_url(v["photo_url"])
        return v


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

    @field_validator("theme_config", mode="after")
    @classmethod
    def validate_theme_config(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("theme_config must be a dictionary")
        if "primary_color" in v and v["primary_color"] is not None:
            validate_primary_color(v["primary_color"])
        if "photo_url" in v and v["photo_url"] is not None:
            validate_photo_url(v["photo_url"])
        return v



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
