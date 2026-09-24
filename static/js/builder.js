/**
 * ResumeForge Builder & Live Preview Script
 */

let resumeState = {
  id: null,
  title: "Untitled Resume",
  template_id: "modern",
  theme_config: {
    primary_color: "#4f46e5",
    font_family: "Inter",
    section_order: [
      "personal_info",
      "work_experiences",
      "education",
      "skills",
      "projects",
      "certifications",
      "custom_sections",
    ],
  },
  personal_info: {
    full_name: "",
    email: "",
    phone: "",
    location: "",
    linkedin_url: "",
    github_url: "",
    portfolio_url: "",
    summary: "",
  },
  work_experiences: [],
  education: [],
  skills: [],
  projects: [],
  certifications: [],
  custom_sections: [],
};

let autosaveTimer = null;
let saveStatus = "saved"; // "saved" | "saving" | "unsaved"

function setSaveStatus(status) {
  saveStatus = status;
  const badge = document.getElementById("save-status-indicator");
  if (!badge) return;

  if (status === "saved") {
    badge.className = "status-indicator status-saved";
    badge.textContent = "✓ All changes saved";
  } else if (status === "saving") {
    badge.className = "status-indicator status-saving";
    badge.textContent = "⏳ Saving changes...";
  } else if (status === "unsaved") {
    badge.className = "status-indicator status-unsaved";
    badge.textContent = "● Unsaved changes";
  }
}

function triggerAutosave() {
  setSaveStatus("unsaved");
  if (autosaveTimer) clearTimeout(autosaveTimer);
  autosaveTimer = setTimeout(async () => {
    await saveResume();
  }, 1500);
}

async function saveResume() {
  if (!resumeState.id) return;
  setSaveStatus("saving");

  try {
    const payload = {
      title: resumeState.title,
      template_id: resumeState.template_id,
      theme_config: resumeState.theme_config,
      personal_info: resumeState.personal_info,
      work_experiences: resumeState.work_experiences,
      education: resumeState.education,
      skills: resumeState.skills,
      projects: resumeState.projects,
      certifications: resumeState.certifications,
      custom_sections: resumeState.custom_sections,
    };

    await api.request(`/resumes/${resumeState.id}`, {
      method: "PUT",
      body: payload,
    });
    setSaveStatus("saved");
  } catch (err) {
    setSaveStatus("unsaved");
    console.error("Autosave failed:", err);
  }
}

// -------------------------------------------------------------
// Form Binding & Editing Logic
// -------------------------------------------------------------

function bindFormInputs() {
  // Title & Metadata
  const titleInput = document.getElementById("resume-title-input");
  if (titleInput) {
    titleInput.value = resumeState.title || "";
    titleInput.oninput = (e) => {
      resumeState.title = e.target.value;
      updateLivePreview();
      triggerAutosave();
    };
  }

  const templateSelect = document.getElementById("template-select");
  if (templateSelect) {
    templateSelect.value = resumeState.template_id || "modern";
    templateSelect.onchange = (e) => {
      resumeState.template_id = e.target.value;
      updateLivePreview();
      triggerAutosave();
    };
  }

  const colorInput = document.getElementById("theme-color-input");
  if (colorInput) {
    colorInput.value = resumeState.theme_config?.primary_color || "#4f46e5";
    colorInput.oninput = (e) => {
      if (!resumeState.theme_config) resumeState.theme_config = {};
      resumeState.theme_config.primary_color = e.target.value;
      updateLivePreview();
      triggerAutosave();
    };
  }

  // Personal Info Inputs
  const p = resumeState.personal_info || {};
  const fields = [
    "full_name",
    "email",
    "phone",
    "location",
    "linkedin_url",
    "github_url",
    "portfolio_url",
    "summary",
  ];

  fields.forEach((field) => {
    const input = document.getElementById(`personal-${field}`);
    if (input) {
      input.value = p[field] || "";
      input.oninput = (e) => {
        if (!resumeState.personal_info) resumeState.personal_info = {};
        resumeState.personal_info[field] = e.target.value;
        updateLivePreview();
        triggerAutosave();
      };
    }
  });

  // Render Section Items
  renderWorkExperiencesForm();
  renderEducationForm();
  renderSkillsForm();
  renderProjectsForm();
  renderCertificationsForm();
  renderCustomSectionsForm();

  updateLivePreview();
}

// Section Item Renderers
function renderWorkExperiencesForm() {
  const container = document.getElementById("work-experiences-list");
  if (!container) return;

  container.innerHTML = (resumeState.work_experiences || [])
    .map(
      (item, idx) => `
    <div class="item-card">
      <div class="item-card-header">
        <span class="item-card-title">${escapeHTML(item.company || "New Work Experience")}</span>
        <button onclick="removeWorkExperience(${idx})" class="btn-remove-item">Remove</button>
      </div>
      <div class="form-grid-2">
        <div class="form-group">
          <label class="form-label">Company</label>
          <input type="text" class="form-control" value="${escapeHTML(item.company || "")}" oninput="updateWorkExperience(${idx}, 'company', this.value)">
        </div>
        <div class="form-group">
          <label class="form-label">Position</label>
          <input type="text" class="form-control" value="${escapeHTML(item.position || "")}" oninput="updateWorkExperience(${idx}, 'position', this.value)">
        </div>
      </div>
      <div class="form-grid-2">
        <div class="form-group">
          <label class="form-label">Location</label>
          <input type="text" class="form-control" value="${escapeHTML(item.location || "")}" oninput="updateWorkExperience(${idx}, 'location', this.value)">
        </div>
        <div class="form-group">
          <label class="form-label">Dates (e.g. 2021 - Present)</label>
          <input type="text" class="form-control" value="${escapeHTML(item.description_dates || "")}" placeholder="2021 - Present" oninput="updateWorkExperience(${idx}, 'description_dates', this.value)">
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Description / Bullet Points</label>
        <textarea class="form-control" rows="3" oninput="updateWorkExperience(${idx}, 'description', this.value)">${escapeHTML(item.description || "")}</textarea>
      </div>
    </div>
  `
    )
    .join("");
}

function addWorkExperience() {
  if (!resumeState.work_experiences) resumeState.work_experiences = [];
  resumeState.work_experiences.push({
    company: "Company Name",
    position: "Position Title",
    location: "",
    description: "",
    display_order: resumeState.work_experiences.length,
  });
  renderWorkExperiencesForm();
  updateLivePreview();
  triggerAutosave();
}

function removeWorkExperience(idx) {
  resumeState.work_experiences.splice(idx, 1);
  renderWorkExperiencesForm();
  updateLivePreview();
  triggerAutosave();
}

function updateWorkExperience(idx, field, val) {
  resumeState.work_experiences[idx][field] = val;
  updateLivePreview();
  triggerAutosave();
}

// Education Form Handler
function renderEducationForm() {
  const container = document.getElementById("education-list");
  if (!container) return;

  container.innerHTML = (resumeState.education || [])
    .map(
      (item, idx) => `
    <div class="item-card">
      <div class="item-card-header">
        <span class="item-card-title">${escapeHTML(item.institution || "New Education")}</span>
        <button onclick="removeEducation(${idx})" class="btn-remove-item">Remove</button>
      </div>
      <div class="form-grid-2">
        <div class="form-group">
          <label class="form-label">Institution</label>
          <input type="text" class="form-control" value="${escapeHTML(item.institution || "")}" oninput="updateEducation(${idx}, 'institution', this.value)">
        </div>
        <div class="form-group">
          <label class="form-label">Degree</label>
          <input type="text" class="form-control" value="${escapeHTML(item.degree || "")}" oninput="updateEducation(${idx}, 'degree', this.value)">
        </div>
      </div>
      <div class="form-grid-2">
        <div class="form-group">
          <label class="form-label">Field of Study</label>
          <input type="text" class="form-control" value="${escapeHTML(item.field_of_study || "")}" oninput="updateEducation(${idx}, 'field_of_study', this.value)">
        </div>
        <div class="form-group">
          <label class="form-label">GPA / Honors</label>
          <input type="text" class="form-control" value="${escapeHTML(item.gpa || "")}" oninput="updateEducation(${idx}, 'gpa', this.value)">
        </div>
      </div>
    </div>
  `
    )
    .join("");
}

function addEducation() {
  if (!resumeState.education) resumeState.education = [];
  resumeState.education.push({
    institution: "University / School",
    degree: "Bachelor of Science",
    field_of_study: "Computer Science",
    display_order: resumeState.education.length,
  });
  renderEducationForm();
  updateLivePreview();
  triggerAutosave();
}

function removeEducation(idx) {
  resumeState.education.splice(idx, 1);
  renderEducationForm();
  updateLivePreview();
  triggerAutosave();
}

function updateEducation(idx, field, val) {
  resumeState.education[idx][field] = val;
  updateLivePreview();
  triggerAutosave();
}

// Skills Form Handler
function renderSkillsForm() {
  const container = document.getElementById("skills-list");
  if (!container) return;

  container.innerHTML = (resumeState.skills || [])
    .map(
      (item, idx) => `
    <div class="item-card">
      <div class="item-card-header">
        <span class="item-card-title">${escapeHTML(item.name || "New Skill")}</span>
        <button onclick="removeSkill(${idx})" class="btn-remove-item">Remove</button>
      </div>
      <div class="form-grid-2">
        <div class="form-group">
          <label class="form-label">Skill Name</label>
          <input type="text" class="form-control" value="${escapeHTML(item.name || "")}" oninput="updateSkill(${idx}, 'name', this.value)">
        </div>
        <div class="form-group">
          <label class="form-label">Category (e.g. Languages)</label>
          <input type="text" class="form-control" value="${escapeHTML(item.category || "")}" oninput="updateSkill(${idx}, 'category', this.value)">
        </div>
      </div>
    </div>
  `
    )
    .join("");
}

function addSkill() {
  if (!resumeState.skills) resumeState.skills = [];
  resumeState.skills.push({
    name: "Skill Name",
    category: "Technical Skills",
    display_order: resumeState.skills.length,
  });
  renderSkillsForm();
  updateLivePreview();
  triggerAutosave();
}

function removeSkill(idx) {
  resumeState.skills.splice(idx, 1);
  renderSkillsForm();
  updateLivePreview();
  triggerAutosave();
}

function updateSkill(idx, field, val) {
  resumeState.skills[idx][field] = val;
  updateLivePreview();
  triggerAutosave();
}

// Projects Form Handler
function renderProjectsForm() {
  const container = document.getElementById("projects-list");
  if (!container) return;

  container.innerHTML = (resumeState.projects || [])
    .map(
      (item, idx) => `
    <div class="item-card">
      <div class="item-card-header">
        <span class="item-card-title">${escapeHTML(item.title || "New Project")}</span>
        <button onclick="removeProject(${idx})" class="btn-remove-item">Remove</button>
      </div>
      <div class="form-grid-2">
        <div class="form-group">
          <label class="form-label">Project Title</label>
          <input type="text" class="form-control" value="${escapeHTML(item.title || "")}" oninput="updateProject(${idx}, 'title', this.value)">
        </div>
        <div class="form-group">
          <label class="form-label">Tech Stack</label>
          <input type="text" class="form-control" value="${escapeHTML(item.tech_stack || "")}" oninput="updateProject(${idx}, 'tech_stack', this.value)">
        </div>
      </div>
      <div class="form-group">
        <label class="form-label">Description</label>
        <textarea class="form-control" rows="2" oninput="updateProject(${idx}, 'description', this.value)">${escapeHTML(item.description || "")}</textarea>
      </div>
    </div>
  `
    )
    .join("");
}

function addProject() {
  if (!resumeState.projects) resumeState.projects = [];
  resumeState.projects.push({
    title: "Project Title",
    tech_stack: "Python, FastAPI",
    description: "",
    display_order: resumeState.projects.length,
  });
  renderProjectsForm();
  updateLivePreview();
  triggerAutosave();
}

function removeProject(idx) {
  resumeState.projects.splice(idx, 1);
  renderProjectsForm();
  updateLivePreview();
  triggerAutosave();
}

function updateProject(idx, field, val) {
  resumeState.projects[idx][field] = val;
  updateLivePreview();
  triggerAutosave();
}

// Certifications & Custom Sections Handlers
function renderCertificationsForm() {
  const container = document.getElementById("certifications-list");
  if (!container) return;

  container.innerHTML = (resumeState.certifications || [])
    .map(
      (item, idx) => `
    <div class="item-card">
      <div class="item-card-header">
        <span class="item-card-title">${escapeHTML(item.name || "New Certification")}</span>
        <button onclick="removeCertification(${idx})" class="btn-remove-item">Remove</button>
      </div>
      <div class="form-grid-2">
        <div class="form-group">
          <label class="form-label">Certification Name</label>
          <input type="text" class="form-control" value="${escapeHTML(item.name || "")}" oninput="updateCertification(${idx}, 'name', this.value)">
        </div>
        <div class="form-group">
          <label class="form-label">Issuing Organization</label>
          <input type="text" class="form-control" value="${escapeHTML(item.issuing_organization || "")}" oninput="updateCertification(${idx}, 'issuing_organization', this.value)">
        </div>
      </div>
    </div>
  `
    )
    .join("");
}

function addCertification() {
  if (!resumeState.certifications) resumeState.certifications = [];
  resumeState.certifications.push({
    name: "AWS Certified Developer",
    issuing_organization: "Amazon Web Services",
    display_order: resumeState.certifications.length,
  });
  renderCertificationsForm();
  updateLivePreview();
  triggerAutosave();
}

function removeCertification(idx) {
  resumeState.certifications.splice(idx, 1);
  renderCertificationsForm();
  updateLivePreview();
  triggerAutosave();
}

function updateCertification(idx, field, val) {
  resumeState.certifications[idx][field] = val;
  updateLivePreview();
  triggerAutosave();
}

function renderCustomSectionsForm() {
  const container = document.getElementById("custom-sections-list");
  if (!container) return;

  container.innerHTML = (resumeState.custom_sections || [])
    .map(
      (item, idx) => `
    <div class="item-card">
      <div class="item-card-header">
        <span class="item-card-title">${escapeHTML(item.section_title || "New Section")}</span>
        <button onclick="removeCustomSection(${idx})" class="btn-remove-item">Remove</button>
      </div>
      <div class="form-group">
        <label class="form-label">Section Title</label>
        <input type="text" class="form-control" value="${escapeHTML(item.section_title || "")}" oninput="updateCustomSection(${idx}, 'section_title', this.value)">
      </div>
      <div class="form-group">
        <label class="form-label">Content</label>
        <textarea class="form-control" rows="3" oninput="updateCustomSection(${idx}, 'content', this.value)">${escapeHTML(item.content || "")}</textarea>
      </div>
    </div>
  `
    )
    .join("");
}

function addCustomSection() {
  if (!resumeState.custom_sections) resumeState.custom_sections = [];
  resumeState.custom_sections.push({
    section_title: "Languages",
    content: "English (Native), Spanish (Intermediate)",
    display_order: resumeState.custom_sections.length,
  });
  renderCustomSectionsForm();
  updateLivePreview();
  triggerAutosave();
}

function removeCustomSection(idx) {
  resumeState.custom_sections.splice(idx, 1);
  renderCustomSectionsForm();
  updateLivePreview();
  triggerAutosave();
}

function updateCustomSection(idx, field, val) {
  resumeState.custom_sections[idx][field] = val;
  updateLivePreview();
  triggerAutosave();
}

// -------------------------------------------------------------
// Real-Time Live Preview Engine
// -------------------------------------------------------------

function updateLivePreview() {
  const paper = document.getElementById("resume-paper");
  if (!paper) return;

  const tId = resumeState.template_id || "modern";
  const primaryColor = resumeState.theme_config?.primary_color || "#4f46e5";

  paper.className = `resume-paper template-${tId}`;
  paper.style.setProperty("--theme-color", primaryColor);

  const p = resumeState.personal_info || {};

  // Build Contact Line
  const contactParts = [];
  if (p.email) contactParts.push(`📧 ${escapeHTML(p.email)}`);
  if (p.phone) contactParts.push(`📞 ${escapeHTML(p.phone)}`);
  if (p.location) contactParts.push(`📍 ${escapeHTML(p.location)}`);
  if (p.linkedin_url) contactParts.push(`🔗 ${escapeHTML(p.linkedin_url)}`);
  if (p.github_url) contactParts.push(`💻 ${escapeHTML(p.github_url)}`);
  if (p.portfolio_url) contactParts.push(`🌐 ${escapeHTML(p.portfolio_url)}`);

  let html = `
    <div class="preview-header">
      <div class="preview-name">${escapeHTML(p.full_name || "Your Name")}</div>
      <div class="preview-contact">${contactParts.join(" &bull; ")}</div>
    </div>
  `;

  // Summary Section
  if (p.summary) {
    html += `
      <div class="preview-section">
        <div class="preview-section-heading">Professional Summary</div>
        <div class="preview-item-desc">${escapeHTML(p.summary)}</div>
      </div>
    `;
  }

  // Work Experiences
  if (resumeState.work_experiences && resumeState.work_experiences.length > 0) {
    html += `<div class="preview-section"><div class="preview-section-heading">Work Experience</div>`;
    resumeState.work_experiences.forEach((w) => {
      html += `
        <div class="preview-item">
          <div class="preview-item-header">
            <span>${escapeHTML(w.company)}</span>
            <span>${escapeHTML(w.location || "")}</span>
          </div>
          <div class="preview-item-sub">
            <span>${escapeHTML(w.position)}</span>
            <span>${escapeHTML(w.description_dates || "")}</span>
          </div>
          ${w.description ? `<div class="preview-item-desc">${escapeHTML(w.description)}</div>` : ""}
        </div>
      `;
    });
    html += `</div>`;
  }

  // Education
  if (resumeState.education && resumeState.education.length > 0) {
    html += `<div class="preview-section"><div class="preview-section-heading">Education</div>`;
    resumeState.education.forEach((e) => {
      html += `
        <div class="preview-item">
          <div class="preview-item-header">
            <span>${escapeHTML(e.institution)}</span>
            <span>${escapeHTML(e.location || "")}</span>
          </div>
          <div class="preview-item-sub">
            <span>${escapeHTML(e.degree)}${e.field_of_study ? ` in ${escapeHTML(e.field_of_study)}` : ""}</span>
            <span>${escapeHTML(e.gpa ? `GPA: ${e.gpa}` : "")}</span>
          </div>
        </div>
      `;
    });
    html += `</div>`;
  }

  // Skills
  if (resumeState.skills && resumeState.skills.length > 0) {
    html += `<div class="preview-section"><div class="preview-section-heading">Skills</div><div class="preview-item-desc">`;
    const skillStrings = resumeState.skills.map(
      (s) => `<strong>${escapeHTML(s.name)}</strong>${s.category ? ` (${escapeHTML(s.category)})` : ""}`
    );
    html += skillStrings.join(" &bull; ");
    html += `</div></div>`;
  }

  // Projects
  if (resumeState.projects && resumeState.projects.length > 0) {
    html += `<div class="preview-section"><div class="preview-section-heading">Projects</div>`;
    resumeState.projects.forEach((proj) => {
      html += `
        <div class="preview-item">
          <div class="preview-item-header">
            <span>${escapeHTML(proj.title)}</span>
            <span style="font-weight:normal; font-size:9pt; color:#64748b;">${escapeHTML(proj.tech_stack || "")}</span>
          </div>
          ${proj.description ? `<div class="preview-item-desc">${escapeHTML(proj.description)}</div>` : ""}
        </div>
      `;
    });
    html += `</div>`;
  }

  // Certifications
  if (resumeState.certifications && resumeState.certifications.length > 0) {
    html += `<div class="preview-section"><div class="preview-section-heading">Certifications</div>`;
    resumeState.certifications.forEach((c) => {
      html += `
        <div class="preview-item">
          <div class="preview-item-header">
            <span>${escapeHTML(c.name)}</span>
            <span style="font-weight:normal; color:#64748b;">${escapeHTML(c.issuing_organization || "")}</span>
          </div>
        </div>
      `;
    });
    html += `</div>`;
  }

  // Custom Sections
  if (resumeState.custom_sections && resumeState.custom_sections.length > 0) {
    resumeState.custom_sections.forEach((cs) => {
      html += `
        <div class="preview-section">
          <div class="preview-section-heading">${escapeHTML(cs.section_title)}</div>
          <div class="preview-item-desc">${escapeHTML(cs.content || "")}</div>
        </div>
      `;
    });
  }

  paper.innerHTML = html;
}

function escapeHTML(str) {
  return String(str || "").replace(
    /[&<>"']/g,
    (match) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[match])
  );
}

// Initialize Builder Data from Query String
document.addEventListener("DOMContentLoaded", async () => {
  requireAuth();

  const urlParams = new URLSearchParams(window.location.search);
  const resumeId = urlParams.get("id");

  if (!resumeId) {
    alert("No resume specified.");
    window.location.href = "/dashboard";
    return;
  }

  try {
    const data = await api.request(`/resumes/${resumeId}`);
    resumeState = {
      ...resumeState,
      ...data,
      personal_info: data.personal_info || resumeState.personal_info,
      work_experiences: data.work_experiences || [],
      education: data.education || [],
      skills: data.skills || [],
      projects: data.projects || [],
      certifications: data.certifications || [],
      custom_sections: data.custom_sections || [],
    };
    bindFormInputs();
    setSaveStatus("saved");
  } catch (err) {
    alert(err.message || "Could not load resume.");
    window.location.href = "/dashboard";
  }
});
