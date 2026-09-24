from sqlalchemy.orm import Session
from app.models.resume import Resume
from app.models.sections import (
    PersonalInfo,
    WorkExperience,
    Education,
    Skill,
    Project,
    Certification,
    CustomSection,
)
from app.schemas.resume import ResumeUpdate


def update_resume_full_payload(db: Session, resume: Resume, resume_in: ResumeUpdate) -> Resume:
    """
    Synchronizes full resume JSON payload atomically within a single database transaction.
    """
    # Update top-level resume attributes
    if resume_in.title is not None:
        resume.title = resume_in.title
    if resume_in.template_id is not None:
        resume.template_id = resume_in.template_id
    if resume_in.theme_config is not None:
        resume.theme_config = resume_in.theme_config

    # Synchronize Personal Info (1:1 relationship)
    if resume_in.personal_info is not None:
        p_data = resume_in.personal_info.model_dump(exclude_unset=True)
        if resume.personal_info:
            for key, value in p_data.items():
                setattr(resume.personal_info, key, value)
        else:
            resume.personal_info = PersonalInfo(resume_id=resume.id, **p_data)

    # Synchronize Work Experiences (1:N relationship)
    if resume_in.work_experiences is not None:
        resume.work_experiences.clear()
        for item in resume_in.work_experiences:
            resume.work_experiences.append(WorkExperience(**item.model_dump()))

    # Synchronize Education (1:N relationship)
    if resume_in.education is not None:
        resume.education.clear()
        for item in resume_in.education:
            resume.education.append(Education(**item.model_dump()))

    # Synchronize Skills (1:N relationship)
    if resume_in.skills is not None:
        resume.skills.clear()
        for item in resume_in.skills:
            resume.skills.append(Skill(**item.model_dump()))

    # Synchronize Projects (1:N relationship)
    if resume_in.projects is not None:
        resume.projects.clear()
        for item in resume_in.projects:
            resume.projects.append(Project(**item.model_dump()))

    # Synchronize Certifications (1:N relationship)
    if resume_in.certifications is not None:
        resume.certifications.clear()
        for item in resume_in.certifications:
            resume.certifications.append(Certification(**item.model_dump()))

    # Synchronize Custom Sections (1:N relationship)
    if resume_in.custom_sections is not None:
        resume.custom_sections.clear()
        for item in resume_in.custom_sections:
            resume.custom_sections.append(CustomSection(**item.model_dump()))

    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume
