import uuid
import re
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db, get_current_user, verify_resume_owner
from app.models.user import User
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
from app.schemas.resume import (
    ResumeCreate,
    ResumeUpdate,
    ResumeSummaryResponse,
    ResumeDetailResponse,
)
from app.services.resume import update_resume_full_payload

router = APIRouter()


def sanitize_filename(name: str) -> str:
    """Sanitizes string for use in HTTP Content-Disposition filename headers."""
    clean = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
    return clean or "Resume"


def generate_resume_print_html(resume: Resume) -> str:
    template_id = resume.template_id or "modern"
    theme = resume.theme_config or {}
    primary_color = theme.get("primary_color", "#4f46e5")
    
    p = resume.personal_info
    full_name = p.full_name if (p and p.full_name) else "Your Name"
    email = p.email if (p and p.email) else ""
    phone = p.phone if (p and p.phone) else ""
    location = p.location if (p and p.location) else ""
    linkedin = p.linkedin_url if (p and p.linkedin_url) else ""
    github = p.github_url if (p and p.github_url) else ""
    portfolio = p.portfolio_url if (p and p.portfolio_url) else ""
    summary = p.summary if (p and p.summary) else ""

    contact_items = [item for item in [email, phone, location, linkedin, github, portfolio] if item]
    contact_str = " &bull; ".join(contact_items)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{resume.title} - Print View</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 12mm;
    }}
    @media print {{
      body {{
        background: #ffffff !important;
        color: #000000 !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }}
      .no-print {{ display: none !important; }}
      .print-container {{ padding: 0 !important; box-shadow: none !important; width: 100% !important; }}
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 10.5pt;
      line-height: 1.45;
      color: #1e293b;
      background: #f1f5f9;
      padding: 20px;
    }}
    .print-container {{
      max-width: 210mm;
      margin: 0 auto;
      background: #ffffff;
      padding: 20mm;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .no-print-bar {{
      max-width: 210mm;
      margin: 0 auto 20px auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #1e293b;
      color: #ffffff;
      padding: 12px 20px;
      border-radius: 8px;
    }}
    .btn-print {{
      background: #4f46e5;
      color: #ffffff;
      border: none;
      padding: 8px 16px;
      font-size: 14px;
      font-weight: 600;
      border-radius: 4px;
      cursor: pointer;
    }}
    .preview-name {{
      font-size: 24pt;
      font-weight: 800;
      color: {primary_color};
      margin-bottom: 4px;
    }}
    .preview-contact {{
      font-size: 9.5pt;
      color: #475569;
      margin-bottom: 16px;
    }}
    .preview-section {{
      margin-bottom: 16px;
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    .preview-section-heading {{
      font-size: 12pt;
      font-weight: 700;
      text-transform: uppercase;
      color: {primary_color};
      border-bottom: 2px solid {primary_color};
      padding-bottom: 3px;
      margin-top: 14px;
      margin-bottom: 8px;
    }}
    .preview-item {{
      margin-bottom: 10px;
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    .preview-item-header {{
      display: flex;
      justify-content: space-between;
      font-weight: 700;
      font-size: 10.5pt;
    }}
    .preview-item-sub {{
      display: flex;
      justify-content: space-between;
      font-style: italic;
      font-size: 9.5pt;
      color: #475569;
      margin-bottom: 3px;
    }}
    .preview-item-desc {{
      font-size: 9.5pt;
      white-space: pre-line;
    }}
  </style>
</head>
<body>
  <div class="no-print-bar no-print">
    <div><strong>Print Mode:</strong> Press Download PDF / Print to save as A4 PDF</div>
    <button onclick="window.print()" class="btn-print">🖨️ Print / Save as PDF</button>
  </div>

  <div class="print-container template-{template_id}">
    <div class="preview-name">{full_name}</div>
    <div class="preview-contact">{contact_str}</div>
"""
    if summary:
        html += f"""
    <div class="preview-section">
      <div class="preview-section-heading">Professional Summary</div>
      <div class="preview-item-desc">{summary}</div>
    </div>
"""
    if resume.work_experiences:
        html += '<div class="preview-section"><div class="preview-section-heading">Work Experience</div>'
        for w in resume.work_experiences:
            html += f"""
      <div class="preview-item">
        <div class="preview-item-header">
          <span>{w.company}</span>
          <span>{w.location or ''}</span>
        </div>
        <div class="preview-item-sub">
          <span>{w.position}</span>
          <span></span>
        </div>
        {f'<div class="preview-item-desc">{w.description}</div>' if w.description else ''}
      </div>
"""
        html += '</div>'

    if resume.education:
        html += '<div class="preview-section"><div class="preview-section-heading">Education</div>'
        for e in resume.education:
            html += f"""
      <div class="preview-item">
        <div class="preview-item-header">
          <span>{e.institution}</span>
          <span>{e.location or ''}</span>
        </div>
        <div class="preview-item-sub">
          <span>{e.degree}{f' in {e.field_of_study}' if e.field_of_study else ''}</span>
          <span>{f'GPA: {e.gpa}' if e.gpa else ''}</span>
        </div>
      </div>
"""
        html += '</div>'

    if resume.skills:
        html += '<div class="preview-section"><div class="preview-section-heading">Skills</div><div class="preview-item-desc">'
        skill_strs = [f"<strong>{s.name}</strong>" + (f" ({s.category})" if s.category else "") for s in resume.skills]
        html += " &bull; ".join(skill_strs)
        html += '</div></div>'

    if resume.projects:
        html += '<div class="preview-section"><div class="preview-section-heading">Projects</div>'
        for proj in resume.projects:
            html += f"""
      <div class="preview-item">
        <div class="preview-item-header">
          <span>{proj.title}</span>
          <span style="font-weight:normal; font-size:9pt;">{proj.tech_stack or ''}</span>
        </div>
        {f'<div class="preview-item-desc">{proj.description}</div>' if proj.description else ''}
      </div>
"""
        html += '</div>'

    if resume.certifications:
        html += '<div class="preview-section"><div class="preview-section-heading">Certifications</div>'
        for c in resume.certifications:
            html += f"""
      <div class="preview-item">
        <div class="preview-item-header">
          <span>{c.name}</span>
          <span style="font-weight:normal;">{c.issuing_organization or ''}</span>
        </div>
      </div>
"""
        html += '</div>'

    if resume.custom_sections:
        for cs in resume.custom_sections:
            html += f"""
    <div class="preview-section">
      <div class="preview-section-heading">{cs.section_title}</div>
      <div class="preview-item-desc">{cs.content or ''}</div>
    </div>
"""

    html += """
  </div>
</body>
</html>"""
    return html


@router.post("/", response_model=ResumeDetailResponse, status_code=status.HTTP_201_CREATED)
def create_resume(
    resume_in: ResumeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    default_theme = resume_in.theme_config or {
        "primary_color": "#4f46e5",
        "font_family": "Inter",
        "section_order": [
            "personal_info",
            "work_experiences",
            "education",
            "skills",
            "projects",
            "certifications",
            "custom_sections",
        ],
    }
    
    resume = Resume(
        user_id=current_user.id,
        title=resume_in.title,
        template_id=resume_in.template_id,
        theme_config=default_theme,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.post("/import", response_model=ResumeDetailResponse, status_code=status.HTTP_201_CREATED)
def import_resume_json(
    import_payload: ResumeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Imports a JSON resume payload to create a new resume document owned strictly by current_user.
    Ignores any imported owner/user IDs.
    """
    title = import_payload.title or "Imported Resume"
    template_id = import_payload.template_id or "modern"
    theme_config = import_payload.theme_config or {"primary_color": "#4f46e5"}

    new_resume = Resume(
        user_id=current_user.id,
        title=title,
        template_id=template_id,
        theme_config=theme_config,
    )
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)

    # Synchronize all child sections using the full payload service
    imported_resume = update_resume_full_payload(db, new_resume, import_payload)
    return imported_resume


@router.get("/", response_model=List[ResumeSummaryResponse])
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    resumes = db.execute(
        select(Resume)
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.updated_at.desc())
    ).scalars().all()
    return resumes


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
def get_resume(
    resume: Resume = Depends(verify_resume_owner),
) -> Any:
    return resume


@router.put("/{resume_id}", response_model=ResumeDetailResponse)
def update_resume(
    resume_in: ResumeUpdate,
    resume: Resume = Depends(verify_resume_owner),
    db: Session = Depends(get_db),
) -> Any:
    updated_resume = update_resume_full_payload(db, resume, resume_in)
    return updated_resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume: Resume = Depends(verify_resume_owner),
    db: Session = Depends(get_db),
) -> None:
    db.delete(resume)
    db.commit()


@router.get("/{resume_id}/print", response_class=HTMLResponse)
def print_resume_view(
    resume: Resume = Depends(verify_resume_owner),
) -> Any:
    """
    Serves a standalone HTML document optimized for browser print-to-PDF (@media print).
    """
    html_content = generate_resume_print_html(resume)
    return HTMLResponse(content=html_content)


@router.get("/{resume_id}/export/json")
def export_resume_json(
    resume: Resume = Depends(verify_resume_owner),
) -> Any:
    """
    Exports full resume structure as a downloadable JSON backup file.
    """
    resume_schema = ResumeDetailResponse.model_validate(resume)
    data = resume_schema.model_dump(mode="json")
    
    clean_filename = sanitize_filename(resume.title)
    headers = {
        "Content-Disposition": f'attachment; filename="{clean_filename}_backup.json"'
    }
    return JSONResponse(content=data, headers=headers)


@router.post("/{resume_id}/duplicate", response_model=ResumeDetailResponse, status_code=status.HTTP_201_CREATED)
def duplicate_resume(
    resume: Resume = Depends(verify_resume_owner),
    db: Session = Depends(get_db),
) -> Any:
    cloned_resume = Resume(
        user_id=resume.user_id,
        title=f"{resume.title} (Copy)",
        template_id=resume.template_id,
        theme_config=resume.theme_config,
    )
    db.add(cloned_resume)
    db.commit()
    db.refresh(cloned_resume)

    if resume.personal_info:
        p_data = {
            "full_name": resume.personal_info.full_name,
            "email": resume.personal_info.email,
            "phone": resume.personal_info.phone,
            "location": resume.personal_info.location,
            "linkedin_url": resume.personal_info.linkedin_url,
            "github_url": resume.personal_info.github_url,
            "portfolio_url": resume.personal_info.portfolio_url,
            "summary": resume.personal_info.summary,
        }
        cloned_resume.personal_info = PersonalInfo(resume_id=cloned_resume.id, **p_data)

    for item in resume.work_experiences:
        cloned_resume.work_experiences.append(
            WorkExperience(
                resume_id=cloned_resume.id,
                company=item.company,
                position=item.position,
                location=item.location,
                start_date=item.start_date,
                end_date=item.end_date,
                is_current=item.is_current,
                description=item.description,
                display_order=item.display_order,
            )
        )

    for item in resume.education:
        cloned_resume.education.append(
            Education(
                resume_id=cloned_resume.id,
                institution=item.institution,
                degree=item.degree,
                field_of_study=item.field_of_study,
                location=item.location,
                start_date=item.start_date,
                end_date=item.end_date,
                gpa=item.gpa,
                display_order=item.display_order,
            )
        )

    for item in resume.skills:
        cloned_resume.skills.append(
            Skill(
                resume_id=cloned_resume.id,
                name=item.name,
                category=item.category,
                proficiency_level=item.proficiency_level,
                display_order=item.display_order,
            )
        )

    for item in resume.projects:
        cloned_resume.projects.append(
            Project(
                resume_id=cloned_resume.id,
                title=item.title,
                description=item.description,
                tech_stack=item.tech_stack,
                project_url=item.project_url,
                start_date=item.start_date,
                end_date=item.end_date,
                display_order=item.display_order,
            )
        )

    for item in resume.certifications:
        cloned_resume.certifications.append(
            Certification(
                resume_id=cloned_resume.id,
                name=item.name,
                issuing_organization=item.issuing_organization,
                issue_date=item.issue_date,
                credential_url=item.credential_url,
                display_order=item.display_order,
            )
        )

    for item in resume.custom_sections:
        cloned_resume.custom_sections.append(
            CustomSection(
                resume_id=cloned_resume.id,
                section_title=item.section_title,
                content=item.content,
                display_order=item.display_order,
            )
        )

    db.add(cloned_resume)
    db.commit()
    db.refresh(cloned_resume)
    return cloned_resume
