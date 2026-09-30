import uuid
import re
import html
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


def safe_html(val: Any) -> str:
    """Safely HTML-escapes user-controlled strings for print HTML template generation."""
    if val is None:
        return ""
    return html.escape(str(val), quote=True)


def generate_resume_print_html(resume: Resume) -> str:
    template_id = (resume.template_id or "modern").lower().replace("-", "_")
    theme = resume.theme_config or {}
    primary_color = theme.get("primary_color", "#2563eb")

    p = resume.personal_info
    full_name = safe_html(p.full_name) if (p and p.full_name) else "Your Name"
    email = safe_html(p.email) if (p and p.email) else ""
    phone = safe_html(p.phone) if (p and p.phone) else ""
    location = safe_html(p.location) if (p and p.location) else ""
    linkedin = safe_html(p.linkedin_url) if (p and p.linkedin_url) else ""
    github = safe_html(p.github_url) if (p and p.github_url) else ""
    portfolio = safe_html(p.portfolio_url) if (p and p.portfolio_url) else ""
    summary = safe_html(p.summary) if (p and p.summary) else ""

    contact_items = [item for item in [email, phone, location, linkedin, github, portfolio] if item]
    contact_str = " &bull; ".join(contact_items)

    photo_url = theme.get("photo_url") if isinstance(theme, dict) else None
    photo_html = ""
    if photo_url and isinstance(photo_url, str):
        if re.match(r"^data:image/(jpeg|png|webp);base64,([A-Za-z0-9+/=]+)$", photo_url):
            photo_html = f'<img src="{photo_url}" alt="Profile Photo" class="preview-avatar">'

    css_styles = f"""
    @page {{
      size: A4 portrait;
      margin: 12mm;
    }}
    @media print {{
      html, body {{
        background: #ffffff !important;
        color: #000000 !important;
        padding: 0 !important;
        margin: 0 !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }}
      .no-print {{ display: none !important; }}
      .print-container {{
        padding: 0 !important;
        margin: 0 !important;
        box-shadow: none !important;
        width: 100% !important;
        max-width: 100% !important;
      }}
      .template-executive .preview-header {{
        margin: 0 0 16px 0 !important;
        border-radius: 0 !important;
      }}
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --theme-color: {primary_color};
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 10pt;
      line-height: 1.45;
      color: #1e293b;
      background: #f1f5f9;
      padding: 20px;
    }}
    .print-container {{
      max-width: 210mm;
      margin: 0 auto;
      background: #ffffff;
      padding: 16mm;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      box-sizing: border-box;
      --theme-color: {primary_color};
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
      background: {primary_color};
      color: #ffffff;
      border: none;
      padding: 8px 16px;
      font-size: 14px;
      font-weight: 600;
      border-radius: 4px;
      cursor: pointer;
    }}

    .preview-avatar {{
      width: 70px;
      height: 70px;
      border-radius: 50%;
      object-fit: cover;
      border: 2px solid {primary_color};
      margin-bottom: 8px;
    }}
    .template-professional .preview-avatar,
    .template-elegant .preview-avatar {{
      display: block;
      margin-left: auto;
      margin-right: auto;
    }}

    .preview-section {{ margin-bottom: 14px; break-inside: avoid; page-break-inside: avoid; }}
    .preview-item {{ margin-bottom: 8px; break-inside: avoid; page-break-inside: avoid; }}
    .preview-item-header {{ display: flex; justify-content: space-between; align-items: baseline; font-weight: 700; font-size: 10.5pt; }}
    .preview-item-sub {{ display: flex; justify-content: space-between; align-items: baseline; font-style: italic; font-size: 9.5pt; color: #475569; margin-bottom: 3px; }}
    .preview-item-desc {{ font-size: 9.5pt; white-space: pre-line; color: #334155; }}

    /* 1. MODERN */
    .template-modern {{ font-family: 'Inter', -apple-system, sans-serif; }}
    .template-modern .preview-header {{ border-bottom: 2px solid {primary_color}; padding-bottom: 10px; margin-bottom: 14px; }}
    .template-modern .preview-name {{ font-size: 24pt; font-weight: 800; color: {primary_color}; letter-spacing: -0.5px; }}
    .template-modern .preview-contact {{ font-size: 9pt; color: #64748b; margin-top: 4px; }}
    .template-modern .preview-section-heading {{ font-size: 11pt; font-weight: 700; text-transform: uppercase; color: {primary_color}; border-bottom: 1.5px solid {primary_color}; padding-bottom: 2px; margin-top: 12px; margin-bottom: 8px; }}

    /* 2. PROFESSIONAL */
    .template-professional {{ font-family: 'Segoe UI', Arial, sans-serif; }}
    .template-professional .preview-header {{ text-align: center; border-top: 2px solid {primary_color}; border-bottom: 2px solid {primary_color}; padding: 10px 0; margin-bottom: 16px; }}
    .template-professional .preview-name {{ font-size: 22pt; font-weight: 700; color: {primary_color}; letter-spacing: 1px; }}
    .template-professional .preview-contact {{ font-size: 9pt; color: #475569; margin-top: 4px; }}
    .template-professional .preview-section-heading {{ font-size: 11pt; font-weight: 700; color: {primary_color}; text-transform: uppercase; border-bottom: 1px solid #cbd5e1; padding-bottom: 3px; margin-top: 14px; margin-bottom: 8px; }}

    /* 3. MINIMAL */
    .template-minimal {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #27272a; }}
    .template-minimal .preview-header {{ margin-bottom: 18px; }}
    .template-minimal .preview-name {{ font-size: 20pt; font-weight: 400; letter-spacing: 1px; color: #18181b; }}
    .template-minimal .preview-contact {{ font-size: 8.5pt; color: #71717a; margin-top: 4px; }}
    .template-minimal .preview-section-heading {{ font-size: 10pt; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; color: #52525b; margin-top: 14px; margin-bottom: 6px; }}

    /* 4. ATS */
    .template-ats {{ font-family: Arial, Helvetica, sans-serif; color: #000000; }}
    .template-ats .preview-header {{ margin-bottom: 12px; }}
    .template-ats .preview-name {{ font-size: 22pt; font-weight: bold; color: #000000; text-transform: uppercase; }}
    .template-ats .preview-contact {{ font-size: 9.5pt; color: #000000; margin-top: 2px; }}
    .template-ats .preview-section-heading {{ font-size: 11pt; font-weight: bold; text-transform: uppercase; color: #000000; border-bottom: 1px solid #000000; padding-bottom: 2px; margin-top: 12px; margin-bottom: 6px; }}

    /* 5. CREATIVE */
    .template-creative {{ font-family: 'Inter', sans-serif; }}
    .template-creative .preview-header {{ background: {primary_color}; color: #ffffff; padding: 14px; border-radius: 6px; margin-bottom: 16px; }}
    .template-creative .preview-name {{ font-size: 22pt; font-weight: 800; color: #ffffff; }}
    .template-creative .preview-contact {{ font-size: 9pt; color: rgba(255, 255, 255, 0.9); margin-top: 4px; }}
    .template-creative .preview-section-heading {{ font-size: 11pt; font-weight: 700; color: {primary_color}; display: flex; align-items: center; gap: 8px; margin-top: 14px; margin-bottom: 8px; }}
    .template-creative .skill-badge {{ display: inline-block; padding: 2px 8px; margin: 2px 4px; background: rgba(124, 58, 237, 0.1); color: {primary_color}; border: 1px solid {primary_color}; border-radius: 12px; font-size: 8.5pt; }}

    /* 6. CORPORATE */
    .template-corporate {{ font-family: Arial, Helvetica, sans-serif; }}
    .template-corporate .preview-header {{ background: #f1f5f9; border-left: 6px solid {primary_color}; padding: 12px 16px; margin-bottom: 16px; }}
    .template-corporate .preview-name {{ font-size: 22pt; font-weight: 800; color: {primary_color}; }}
    .template-corporate .preview-contact {{ font-size: 9pt; color: #475569; margin-top: 4px; }}
    .template-corporate .preview-section-heading {{ font-size: 11pt; font-weight: 700; background: #f1f5f9; color: {primary_color}; padding: 4px 8px; border-left: 3px solid {primary_color}; margin-top: 14px; margin-bottom: 8px; text-transform: uppercase; }}

    /* 7. EXECUTIVE */
    .template-executive {{ font-family: Georgia, 'Times New Roman', serif; }}
    .template-executive .preview-header {{ background: #0f172a; color: #ffffff; padding: 16px; margin: -16mm -16mm 16px -16mm; }}
    .template-executive .preview-name {{ font-size: 24pt; font-weight: 700; color: #ffffff; letter-spacing: 0.5px; }}
    .template-executive .preview-contact {{ font-size: 9pt; color: #94a3b8; font-family: -apple-system, sans-serif; margin-top: 4px; }}
    .template-executive .preview-section-heading {{ font-size: 12pt; font-weight: 700; color: {primary_color}; border-bottom: 2px solid {primary_color}; padding-bottom: 2px; margin-top: 14px; margin-bottom: 8px; text-transform: uppercase; }}

    /* 8. STUDENT */
    .template-student {{ font-family: 'Segoe UI', Tahoma, sans-serif; }}
    .template-student .preview-header {{ border-bottom: 3px solid {primary_color}; padding-bottom: 10px; margin-bottom: 16px; }}
    .template-student .preview-name {{ font-size: 22pt; font-weight: 800; color: {primary_color}; }}
    .template-student .preview-contact {{ font-size: 9pt; color: #475569; margin-top: 4px; }}
    .template-student .preview-section-heading {{ font-size: 11pt; font-weight: 700; color: {primary_color}; background: rgba(13, 148, 136, 0.08); padding: 4px 8px; border-radius: 4px; margin-top: 14px; margin-bottom: 8px; text-transform: uppercase; }}

    /* 9. TWO-COLUMN */
    .template-two-column {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    .template-two-column .two-column-wrapper {{ display: flex; gap: 16px; }}
    .template-two-column .sidebar-col {{ width: 32%; background: #f8fafc; padding: 12px; border-radius: 6px; border-right: 1px solid #e2e8f0; }}
    .template-two-column .main-col {{ width: 68%; }}
    .template-two-column .preview-name {{ font-size: 20pt; font-weight: 800; color: {primary_color}; margin-bottom: 6px; }}
    .template-two-column .sidebar-col .preview-section-heading {{ font-size: 10pt; font-weight: 700; text-transform: uppercase; color: {primary_color}; border-bottom: 1px solid #cbd5e1; padding-bottom: 2px; margin-top: 12px; margin-bottom: 6px; }}
    .template-two-column .main-col .preview-section-heading {{ font-size: 11pt; font-weight: 700; text-transform: uppercase; color: {primary_color}; border-bottom: 2px solid {primary_color}; padding-bottom: 2px; margin-top: 12px; margin-bottom: 6px; }}

    /* 10. ELEGANT */
    .template-elegant {{ font-family: Georgia, 'Times New Roman', serif; color: #1c1917; }}
    .template-elegant .preview-header {{ text-align: center; margin-bottom: 16px; }}
    .template-elegant .preview-name {{ font-size: 24pt; font-weight: 400; color: {primary_color}; letter-spacing: 2px; font-style: italic; }}
    .template-elegant .preview-contact {{ font-size: 9pt; color: #57534e; border-top: 1px solid #e7e5e4; border-bottom: 1px solid #e7e5e4; padding: 4px 0; margin-top: 8px; font-family: -apple-system, sans-serif; }}
    .template-elegant .preview-section-heading {{ font-size: 12pt; font-weight: 700; text-align: center; color: {primary_color}; letter-spacing: 1px; margin-top: 16px; margin-bottom: 8px; }}
    """

    # Helpers for rendering section HTML strings
    def build_summary_html():
        if not summary: return ""
        return f'<div class="preview-section"><div class="preview-section-heading">Professional Summary</div><div class="preview-item-desc">{summary}</div></div>'

    def build_experience_html():
        if not resume.work_experiences: return ""
        res = '<div class="preview-section"><div class="preview-section-heading">Work Experience</div>'
        for w in resume.work_experiences:
            date_str = ""
            if w.start_date and w.end_date:
                date_str = f"{safe_html(w.start_date)} - {safe_html(w.end_date)}"
            elif w.start_date:
                date_str = f"{safe_html(w.start_date)} - {'Present' if w.is_current else ''}"
            elif w.end_date:
                date_str = f"Until {safe_html(w.end_date)}"
            
            comp = safe_html(w.company)
            loc = safe_html(w.location)
            pos = safe_html(w.position)
            desc = safe_html(w.description) if w.description else ""
            res += f'<div class="preview-item"><div class="preview-item-header"><span>{comp}</span><span>{loc}</span></div><div class="preview-item-sub"><span>{pos}</span><span>{date_str}</span></div>{f"<div class=\\'preview-item-desc\\'>{desc}</div>" if desc else ""}</div>'
        res += '</div>'
        return res

    def build_education_html():
        if not resume.education: return ""
        res = '<div class="preview-section"><div class="preview-section-heading">Education</div>'
        for e in resume.education:
            date_str = ""
            if e.start_date and e.end_date: date_str = f"{safe_html(e.start_date)} - {safe_html(e.end_date)}"
            elif e.start_date: date_str = safe_html(e.start_date)
            elif e.end_date: date_str = f"Until {safe_html(e.end_date)}"
            
            inst = safe_html(e.institution)
            loc = safe_html(e.location)
            deg = safe_html(e.degree)
            field = safe_html(e.field_of_study)
            gpa = safe_html(e.gpa)
            field_str = f" in {field}" if field else ""
            gpa_str = f"GPA: {gpa}" if gpa else ""
            date_paren = f" ({date_str})" if date_str else ""
            res += f'<div class="preview-item"><div class="preview-item-header"><span>{inst}</span><span>{loc}</span></div><div class="preview-item-sub"><span>{deg}{field_str}</span><span>{gpa_str}{date_paren}</span></div></div>'
        res += '</div>'
        return res

    def build_skills_html():
        if not resume.skills: return ""
        res = '<div class="preview-section"><div class="preview-section-heading">Skills</div><div class="preview-item-desc">'
        if template_id == "creative":
            skill_strs = [f'<span class="skill-badge">{safe_html(s.name)}</span>' for s in resume.skills]
            res += "".join(skill_strs)
        else:
            skill_strs = [f"<strong>{safe_html(s.name)}</strong>" + (f" ({safe_html(s.category)})" if s.category else "") for s in resume.skills]
            res += " &bull; ".join(skill_strs)
        res += '</div></div>'
        return res

    def build_projects_html():
        if not resume.projects: return ""
        res = '<div class="preview-section"><div class="preview-section-heading">Projects</div>'
        for proj in resume.projects:
            date_str = ""
            if proj.start_date and proj.end_date: date_str = f"{safe_html(proj.start_date)} - {safe_html(proj.end_date)}"
            elif proj.start_date: date_str = safe_html(proj.start_date)
            
            title = safe_html(proj.title)
            tech = safe_html(proj.tech_stack)
            desc = safe_html(proj.description) if proj.description else ""
            tech_date = f"{tech}{f' | {date_str}' if date_str else ''}"
            res += f'<div class="preview-item"><div class="preview-item-header"><span>{title}</span><span style="font-weight:normal; font-size:9pt;">{tech_date}</span></div>{f"<div class=\\'preview-item-desc\\'>{desc}</div>" if desc else ""}</div>'
        res += '</div>'
        return res

    def build_certifications_html():
        if not resume.certifications: return ""
        res = '<div class="preview-section"><div class="preview-section-heading">Certifications</div>'
        for c in resume.certifications:
            date_str = f" ({safe_html(c.issue_date)})" if c.issue_date else ""
            c_name = safe_html(c.name)
            c_org = safe_html(c.issuing_organization)
            res += f'<div class="preview-item"><div class="preview-item-header"><span>{c_name}</span><span style="font-weight:normal;">{c_org}{date_str}</span></div></div>'
        res += '</div>'
        return res

    def build_custom_html():
        if not resume.custom_sections: return ""
        res = ""
        for cs in resume.custom_sections:
            title = safe_html(cs.section_title)
            content = safe_html(cs.content)
            res += f'<div class="preview-section"><div class="preview-section-heading">{title}</div><div class="preview-item-desc">{content}</div></div>'
        return res

    # Layout assembly
    if template_id == "two_column":
        inner_content = f"""
      <div class="two-column-wrapper">
        <div class="sidebar-col">
          {photo_html}
          <div class="preview-name">{full_name}</div>
          <div class="preview-contact" style="margin-bottom: 12px;">{contact_str}</div>
          {build_skills_html()}
          {build_certifications_html()}
          {build_custom_html()}
        </div>
        <div class="main-col">
          {build_summary_html()}
          {build_experience_html()}
          {build_education_html()}
          {build_projects_html()}
        </div>
      </div>
    """
    elif template_id == "student":
        inner_content = f"""
      <div class="preview-header">
        {photo_html}
        <div class="preview-name">{full_name}</div>
        <div class="preview-contact">{contact_str}</div>
      </div>
      {build_summary_html()}
      {build_education_html()}
      {build_projects_html()}
      {build_skills_html()}
      {build_experience_html()}
      {build_certifications_html()}
      {build_custom_html()}
    """
    else:
        inner_content = f"""
      <div class="preview-header">
        {photo_html}
        <div class="preview-name">{full_name}</div>
        <div class="preview-contact">{contact_str}</div>
      </div>
      {build_summary_html()}
      {build_experience_html()}
      {build_education_html()}
      {build_skills_html()}
      {build_projects_html()}
      {build_certifications_html()}
      {build_custom_html()}
    """

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{safe_html(resume.title)} - Print View</title>
  <style>
{css_styles}
  </style>
</head>
<body>
  <div class="no-print-bar no-print">
    <div><strong>Print Mode:</strong> Press Download PDF / Print to save as A4 PDF</div>
    <button onclick="window.print()" class="btn-print">🖨️ Print / Save as PDF</button>
  </div>

  <div class="print-container template-{template_id}">
{inner_content}
  </div>
</body>
</html>"""
    return html_doc


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
        theme_config=dict(resume.theme_config) if resume.theme_config else None,
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
