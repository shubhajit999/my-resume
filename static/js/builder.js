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
let isSaving = false;

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

function showBuilderError(msg) {
  const alertBox = document.getElementById("builder-alert");
  if (alertBox) {
    alertBox.textContent = msg;
    alertBox.className = "alert alert-error";
    alertBox.style.display = "block";
  }
}

function hideBuilderAlert() {
  const alertBox = document.getElementById("builder-alert");
  if (alertBox) {
    alertBox.style.display = "none";
    alertBox.textContent = "";
  }
}

function handleSaveError(err) {
  if (!err) return;

  if (err.status === 401) {
    showBuilderError("Your session has expired. Please log in again.");
    setTimeout(() => {
      window.location.href = "/login";
    }, 1500);
    return;
  }

  if (err.status === 403) {
    showBuilderError("Authorization Error: You do not have permission to edit this resume.");
    return;
  }

  if (err.status === 404) {
    showBuilderError("Resume Not Found: This resume no longer exists.");
    return;
  }

  if (err.status === 422) {
    let msg = "Validation Error: Please check your input fields.";
    if (err.data && err.data.detail) {
      if (Array.isArray(err.data.detail)) {
        const fieldMsgs = err.data.detail.map(d => {
          const loc = d.loc ? d.loc.filter(l => l !== 'body').join(' -> ') : '';
          return loc ? `${loc}: ${d.msg}` : d.msg;
        }).join(' | ');
        msg = `Validation Error: ${fieldMsgs}`;
      } else if (typeof err.data.detail === "string") {
        msg = `Validation Error: ${err.data.detail}`;
      }
    }
    showBuilderError(msg);
    return;
  }

  showBuilderError(err.message || "Could not save resume. Please try again.");
}

function sanitizeDate(dateStr) {
  if (!dateStr || typeof dateStr !== "string") return null;
  const trimmed = dateStr.trim();
  if (trimmed === "") return null;

  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    const parts = trimmed.split("-");
    const y = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    const d = parseInt(parts[2], 10);
    if (m >= 1 && m <= 12 && d >= 1 && d <= 31) {
      return trimmed;
    }
  }

  const parsedTimestamp = Date.parse(trimmed);
  if (!isNaN(parsedTimestamp)) {
    const dObj = new Date(parsedTimestamp);
    if (!isNaN(dObj.getTime())) {
      return dObj.toISOString().split("T")[0];
    }
  }

  return "INVALID_DATE";
}

function preparePayload(state) {
  const processDate = (val, fieldLabel) => {
    if (!val || typeof val !== "string" || val.trim() === "") {
      return null;
    }
    const clean = sanitizeDate(val);
    if (clean === "INVALID_DATE") {
      throw new Error(`Invalid date format for ${fieldLabel}: "${val}". Expected YYYY-MM-DD.`);
    }
    return clean;
  };

  const work_experiences = (state.work_experiences || []).map((w, idx) => {
    const itemLabel = `Work Experience #${idx + 1} (${w.company || 'Untitled'})`;
    const copy = { ...w };
    delete copy.description_dates;
    copy.start_date = processDate(copy.start_date, `${itemLabel} Start Date`);
    copy.end_date = processDate(copy.end_date, `${itemLabel} End Date`);
    if (!copy.company || !copy.company.trim()) {
      throw new Error(`Company name is required for Work Experience #${idx + 1}.`);
    }
    if (!copy.position || !copy.position.trim()) {
      throw new Error(`Position is required for Work Experience #${idx + 1}.`);
    }
    return copy;
  });

  const education = (state.education || []).map((e, idx) => {
    const itemLabel = `Education #${idx + 1} (${e.institution || 'Untitled'})`;
    const copy = { ...e };
    copy.start_date = processDate(copy.start_date, `${itemLabel} Start Date`);
    copy.end_date = processDate(copy.end_date, `${itemLabel} End Date`);
    if (!copy.institution || !copy.institution.trim()) {
      throw new Error(`Institution is required for Education #${idx + 1}.`);
    }
    if (!copy.degree || !copy.degree.trim()) {
      throw new Error(`Degree is required for Education #${idx + 1}.`);
    }
    return copy;
  });

  const projects = (state.projects || []).map((p, idx) => {
    const itemLabel = `Project #${idx + 1} (${p.title || 'Untitled'})`;
    const copy = { ...p };
    copy.start_date = processDate(copy.start_date, `${itemLabel} Start Date`);
    copy.end_date = processDate(copy.end_date, `${itemLabel} End Date`);
    if (!copy.title || !copy.title.trim()) {
      throw new Error(`Project title is required for Project #${idx + 1}.`);
    }
    return copy;
  });

  const certifications = (state.certifications || []).map((c, idx) => {
    const itemLabel = `Certification #${idx + 1} (${c.name || 'Untitled'})`;
    const copy = { ...c };
    copy.issue_date = processDate(copy.issue_date, `${itemLabel} Issue Date`);
    if (!copy.name || !copy.name.trim()) {
      throw new Error(`Certification name is required for Certification #${idx + 1}.`);
    }
    return copy;
  });

  const custom_sections = (state.custom_sections || []).map((cs, idx) => {
    const copy = { ...cs };
    if (!copy.section_title || !copy.section_title.trim()) {
      throw new Error(`Section title is required for Custom Section #${idx + 1}.`);
    }
    return copy;
  });

  return {
    title: state.title,
    template_id: state.template_id,
    theme_config: state.theme_config,
    personal_info: state.personal_info,
    work_experiences,
    education,
    skills: state.skills || [],
    projects,
    certifications,
    custom_sections,
  };
}

async function saveResume() {
  if (!resumeState.id || isSaving) return;
  isSaving = true;

  const saveBtn = document.getElementById("save-resume-btn");
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";
  }
  setSaveStatus("saving");
  hideBuilderAlert();

  try {
    const payload = preparePayload(resumeState);

    const updated = await api.request(`/resumes/${resumeState.id}`, {
      method: "PUT",
      body: payload,
    });

    if (updated) {
      resumeState = {
        ...resumeState,
        ...updated,
        personal_info: updated.personal_info || resumeState.personal_info,
        work_experiences: updated.work_experiences || [],
        education: updated.education || [],
        skills: updated.skills || [],
        projects: updated.projects || [],
        certifications: updated.certifications || [],
        custom_sections: updated.custom_sections || [],
      };
      bindFormInputs();
    }

    setSaveStatus("saved");
    hideBuilderAlert();
  } catch (err) {
    setSaveStatus("unsaved");
    console.error("Save error:", err);
    handleSaveError(err);
  } finally {
    isSaving = false;
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.textContent = "Save Resume";
    }
  }
}

// -------------------------------------------------------------
// Form Binding & Editing Logic
// -------------------------------------------------------------

function bindFormInputs() {
  const activeElementId = document.activeElement ? document.activeElement.id : null;

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
      renderTemplateRibbon();
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
  renderPhotoControl();
  renderWorkExperiencesForm();
  renderEducationForm();
  renderSkillsForm();
  renderProjectsForm();
  renderCertificationsForm();
  renderCustomSectionsForm();

  renderTemplateRibbon();
  updateLivePreview();

  if (activeElementId) {
    const el = document.getElementById(activeElementId);
    if (el && typeof el.focus === "function") {
      el.focus();
    }
  }
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
        <div class="form-group" style="display: flex; align-items: center; margin-top: 1.5rem;">
          <label class="form-label" style="display: flex; align-items: center; gap: 0.5rem; cursor: pointer; margin-bottom: 0;">
            <input type="checkbox" ${item.is_current ? "checked" : ""} onchange="updateWorkExperience(${idx}, 'is_current', this.checked)">
            Currently Working Here
          </label>
        </div>
      </div>
      <div class="form-grid-2">
        <div class="form-group">
          <label class="form-label">Start Date</label>
          <input type="date" class="form-control" value="${escapeHTML(item.start_date || "")}" oninput="updateWorkExperience(${idx}, 'start_date', this.value)">
        </div>
        <div class="form-group">
          <label class="form-label">End Date</label>
          <input type="date" class="form-control" value="${escapeHTML(item.end_date || "")}" ${item.is_current ? "disabled" : ""} oninput="updateWorkExperience(${idx}, 'end_date', this.value)">
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
    start_date: null,
    end_date: null,
    is_current: false,
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
  if (!resumeState.work_experiences[idx]) return;
  resumeState.work_experiences[idx][field] = val;
  if (field === "is_current" && val) {
    resumeState.work_experiences[idx].end_date = null;
    renderWorkExperiencesForm();
  }
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
      <div class="form-grid-2">
        <div class="form-group">
          <label class="form-label">Start Date</label>
          <input type="date" class="form-control" value="${escapeHTML(item.start_date || "")}" oninput="updateEducation(${idx}, 'start_date', this.value)">
        </div>
        <div class="form-group">
          <label class="form-label">End Date</label>
          <input type="date" class="form-control" value="${escapeHTML(item.end_date || "")}" oninput="updateEducation(${idx}, 'end_date', this.value)">
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
    start_date: null,
    end_date: null,
    gpa: "",
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
  if (!resumeState.education[idx]) return;
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
  if (!resumeState.skills[idx]) return;
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
      <div class="form-grid-2">
        <div class="form-group">
          <label class="form-label">Start Date</label>
          <input type="date" class="form-control" value="${escapeHTML(item.start_date || "")}" oninput="updateProject(${idx}, 'start_date', this.value)">
        </div>
        <div class="form-group">
          <label class="form-label">End Date</label>
          <input type="date" class="form-control" value="${escapeHTML(item.end_date || "")}" oninput="updateProject(${idx}, 'end_date', this.value)">
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
    start_date: null,
    end_date: null,
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
  if (!resumeState.projects[idx]) return;
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
      <div class="form-grid-2">
        <div class="form-group">
          <label class="form-label">Issue Date</label>
          <input type="date" class="form-control" value="${escapeHTML(item.issue_date || "")}" oninput="updateCertification(${idx}, 'issue_date', this.value)">
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
    issue_date: null,
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
  if (!resumeState.certifications[idx]) return;
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
  if (!resumeState.custom_sections[idx]) return;
  resumeState.custom_sections[idx][field] = val;
  updateLivePreview();
  triggerAutosave();
}

// -------------------------------------------------------------
// Real-Time Live Preview & Template Gallery Engine
// -------------------------------------------------------------

const TEMPLATE_LIST = [
  { id: "modern", name: "1. Modern", icon: "🚀", category: "Tech & Software", desc: "Clean layout with bold primary color accents. Perfect for software engineers and tech professionals." },
  { id: "professional", name: "2. Professional", icon: "💼", category: "Corporate & Finance", desc: "Classic corporate design with crisp section divider lines and balanced typography." },
  { id: "minimal", name: "3. Minimal", icon: "✨", category: "Designers & Writers", desc: "Ultra-clean single-column design with generous whitespace and sleek typography." },
  { id: "ats", name: "4. ATS-Friendly", icon: "📄", category: "ATS Optimized", desc: "Plain text, high-contrast single column optimized for applicant tracking system parsers." },
  { id: "creative", name: "5. Creative", icon: "🎨", category: "Creative & Marketing", desc: "Vibrant header banner, creative section divider lines, and skill badge tags." },
  { id: "corporate", name: "6. Corporate", icon: "🏢", category: "Business & Management", desc: "Formal executive block header with shaded section highlight bars." },
  { id: "executive", name: "7. Executive", icon: "👑", category: "Senior Leadership", desc: "Dark top header banner with elegant serif headings for directors and VPs." },
  { id: "student", name: "8. Student / Fresher", icon: "🎓", category: "Entry Level & Freshers", desc: "Structure prioritizing education, academic projects, and skills first." },
  { id: "two_column", name: "9. Two-Column", icon: "📊", category: "Compact Multi-Column", desc: "Space-efficient 2-column layout with a left sidebar for contact details and skills." },
  { id: "elegant", name: "10. Elegant", icon: "🏛️", category: "Law, Academic & Arts", desc: "Refined aesthetic with elegant serif typography and subtle ornamental dividers." },
];

function getMiniTemplatePreviewHTML(tId) {
  switch (tId) {
    case 'modern':
      return `<div class="mini-thumb thumb-modern">
        <div class="thumb-header"><div class="thumb-name-bar"></div><div class="thumb-sub-bar"></div></div>
        <div class="thumb-sec-heading"></div>
        <div class="thumb-line"></div>
        <div class="thumb-line short"></div>
        <div class="thumb-sec-heading"></div>
        <div class="thumb-line"></div>
        <div class="thumb-line short"></div>
      </div>`;
    case 'professional':
      return `<div class="mini-thumb thumb-professional">
        <div class="thumb-header-pro"><div class="thumb-name-center"></div><div class="thumb-sub-center"></div></div>
        <div class="thumb-sec-heading-pro"></div>
        <div class="thumb-line"></div>
        <div class="thumb-line short"></div>
        <div class="thumb-sec-heading-pro"></div>
        <div class="thumb-line"></div>
      </div>`;
    case 'minimal':
      return `<div class="mini-thumb thumb-minimal">
        <div class="thumb-header-min"><div class="thumb-name-min"></div><div class="thumb-sub-min"></div></div>
        <div class="thumb-sec-heading-min"></div>
        <div class="thumb-line thin"></div>
        <div class="thumb-line thin short"></div>
        <div class="thumb-sec-heading-min"></div>
        <div class="thumb-line thin"></div>
      </div>`;
    case 'ats':
      return `<div class="mini-thumb thumb-ats">
        <div class="thumb-header-ats"><div class="thumb-name-ats"></div><div class="thumb-sub-ats"></div></div>
        <div class="thumb-sec-heading-ats"></div>
        <div class="thumb-line dark"></div>
        <div class="thumb-line dark short"></div>
        <div class="thumb-sec-heading-ats"></div>
        <div class="thumb-line dark"></div>
      </div>`;
    case 'creative':
      return `<div class="mini-thumb thumb-creative">
        <div class="thumb-header-banner"><div class="thumb-banner-title"></div></div>
        <div class="thumb-sec-heading-cr"></div>
        <div class="thumb-line"></div>
        <div class="thumb-tags-group"><span class="thumb-tag"></span><span class="thumb-tag"></span><span class="thumb-tag"></span></div>
        <div class="thumb-sec-heading-cr"></div>
        <div class="thumb-line short"></div>
      </div>`;
    case 'corporate':
      return `<div class="mini-thumb thumb-corporate">
        <div class="thumb-header-corp"><div class="thumb-name-corp"></div></div>
        <div class="thumb-sec-heading-corp"></div>
        <div class="thumb-line"></div>
        <div class="thumb-line short"></div>
        <div class="thumb-sec-heading-corp"></div>
        <div class="thumb-line"></div>
      </div>`;
    case 'executive':
      return `<div class="mini-thumb thumb-executive">
        <div class="thumb-header-exec"><div class="thumb-name-exec"></div></div>
        <div class="thumb-sec-heading-exec"></div>
        <div class="thumb-line"></div>
        <div class="thumb-line short"></div>
        <div class="thumb-sec-heading-exec"></div>
        <div class="thumb-line"></div>
      </div>`;
    case 'student':
      return `<div class="mini-thumb thumb-student">
        <div class="thumb-header-st"><div class="thumb-name-st"></div></div>
        <div class="thumb-sec-pill-st"></div>
        <div class="thumb-line"></div>
        <div class="thumb-sec-pill-st"></div>
        <div class="thumb-line short"></div>
        <div class="thumb-line"></div>
      </div>`;
    case 'two_column':
      return `<div class="mini-thumb thumb-two-column">
        <div class="thumb-sidebar">
          <div class="thumb-name-side"></div>
          <div class="thumb-dot-line"></div>
          <div class="thumb-dot-line"></div>
          <div class="thumb-dot-line"></div>
        </div>
        <div class="thumb-mainbar">
          <div class="thumb-sec-heading-tc"></div>
          <div class="thumb-line"></div>
          <div class="thumb-line short"></div>
          <div class="thumb-sec-heading-tc"></div>
          <div class="thumb-line"></div>
        </div>
      </div>`;
    case 'elegant':
      return `<div class="mini-thumb thumb-elegant">
        <div class="thumb-header-el"><div class="thumb-name-el"></div></div>
        <div class="thumb-dash-line"></div>
        <div class="thumb-sec-heading-el"></div>
        <div class="thumb-line"></div>
        <div class="thumb-sec-heading-el"></div>
        <div class="thumb-line short"></div>
      </div>`;
    default:
      return `<div class="mini-thumb"><div class="thumb-header"></div><div class="thumb-line"></div></div>`;
  }
}

function renderTemplateRibbon() {
  const container = document.getElementById("template-ribbon-container");
  if (!container) return;

  const currentTId = (resumeState.template_id || "modern").toLowerCase().replace("-", "_");

  container.innerHTML = TEMPLATE_LIST.map((t) => {
    const isActive = t.id === currentTId;
    return `
      <div class="template-ribbon-card ${isActive ? 'active' : ''}"
           onclick="selectTemplate('${t.id}')"
           onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();selectTemplate('${t.id}');}"
           tabindex="0"
           role="button"
           aria-selected="${isActive}"
           aria-label="${escapeHTML(t.name)} template">
        ${getMiniTemplatePreviewHTML(t.id)}
        <div class="template-ribbon-name">
          <span>${escapeHTML(t.name.split('. ')[1] || t.name)}</span>
          <span class="template-ribbon-check">✓</span>
        </div>
      </div>
    `;
  }).join("");
}

function openTemplateGallery() {
  const modal = document.getElementById("template-gallery-modal");
  const container = document.getElementById("template-grid-container");
  if (!modal || !container) return;

  const currentTId = (resumeState.template_id || "modern").toLowerCase().replace("-", "_");

  container.innerHTML = TEMPLATE_LIST.map((t) => {
    const isActive = t.id === currentTId;
    return `
      <div class="template-card ${isActive ? 'active' : ''}"
           onclick="selectTemplate('${t.id}')"
           onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();selectTemplate('${t.id}');}"
           tabindex="0"
           role="button"
           aria-selected="${isActive}">
        <div>
          <div style="margin-bottom: 10px;">
            ${getMiniTemplatePreviewHTML(t.id)}
          </div>
          <div class="template-card-header">
            <span class="template-card-icon">${t.icon}</span>
            <span class="template-card-name">${escapeHTML(t.name)}</span>
          </div>
          <div class="template-card-badge">${escapeHTML(t.category)}</div>
          <div class="template-card-desc">${escapeHTML(t.desc)}</div>
        </div>
        <button class="template-card-btn" onclick="event.stopPropagation(); selectTemplate('${t.id}')">
          ${isActive ? "✓ Selected" : "Use Template"}
        </button>
      </div>
    `;
  }).join("");

  modal.style.display = "flex";
}

function closeTemplateGallery() {
  const modal = document.getElementById("template-gallery-modal");
  if (modal) modal.style.display = "none";
}

function selectTemplate(tId) {
  resumeState.template_id = tId;
  if (!resumeState.theme_config) resumeState.theme_config = {};
  resumeState.theme_config.template_id = tId;

  const select = document.getElementById("template-select");
  if (select) select.value = tId;

  renderTemplateRibbon();
  updateLivePreview();
  triggerAutosave();
  closeTemplateGallery();
}

function updateLivePreview() {
  const paper = document.getElementById("resume-paper");
  if (!paper) return;

  const rawId = (resumeState.template_id || "modern").toLowerCase().replace("-", "_");
  const tId = rawId;
  const primaryColor = resumeState.theme_config?.primary_color || "#2563eb";

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
  const contactStr = contactParts.join(" &bull; ");

  // Render Section Builders
  const buildSummary = () => {
    if (!p.summary) return "";
    return `
      <div class="preview-section">
        <div class="preview-section-heading">Professional Summary</div>
        <div class="preview-item-desc">${escapeHTML(p.summary)}</div>
      </div>
    `;
  };

  const buildExperience = () => {
    if (!resumeState.work_experiences || resumeState.work_experiences.length === 0) return "";
    let res = `<div class="preview-section"><div class="preview-section-heading">Work Experience</div>`;
    resumeState.work_experiences.forEach((w) => {
      let dateStr = "";
      if (w.start_date && w.end_date) {
        dateStr = `${escapeHTML(w.start_date)} - ${escapeHTML(w.end_date)}`;
      } else if (w.start_date) {
        dateStr = `${escapeHTML(w.start_date)} - ${w.is_current ? 'Present' : ''}`;
      } else if (w.end_date) {
        dateStr = `Until ${escapeHTML(w.end_date)}`;
      } else if (w.description_dates) {
        dateStr = escapeHTML(w.description_dates);
      }

      res += `
        <div class="preview-item">
          <div class="preview-item-header">
            <span>${escapeHTML(w.company)}</span>
            <span>${escapeHTML(w.location || "")}</span>
          </div>
          <div class="preview-item-sub">
            <span>${escapeHTML(w.position)}</span>
            <span>${dateStr}</span>
          </div>
          ${w.description ? `<div class="preview-item-desc">${escapeHTML(w.description)}</div>` : ""}
        </div>
      `;
    });
    res += `</div>`;
    return res;
  };

  const buildEducation = () => {
    if (!resumeState.education || resumeState.education.length === 0) return "";
    let res = `<div class="preview-section"><div class="preview-section-heading">Education</div>`;
    resumeState.education.forEach((e) => {
      let dateStr = "";
      if (e.start_date && e.end_date) dateStr = `${escapeHTML(e.start_date)} - ${escapeHTML(e.end_date)}`;
      else if (e.start_date) dateStr = escapeHTML(e.start_date);
      else if (e.end_date) dateStr = `Until ${escapeHTML(e.end_date)}`;

      res += `
        <div class="preview-item">
          <div class="preview-item-header">
            <span>${escapeHTML(e.institution)}</span>
            <span>${escapeHTML(e.location || "")}</span>
          </div>
          <div class="preview-item-sub">
            <span>${escapeHTML(e.degree)}${e.field_of_study ? ` in ${escapeHTML(e.field_of_study)}` : ""}</span>
            <span>${escapeHTML(e.gpa ? `GPA: ${e.gpa}` : "")}${dateStr ? ` (${dateStr})` : ''}</span>
          </div>
        </div>
      `;
    });
    res += `</div>`;
    return res;
  };

  const buildSkills = () => {
    if (!resumeState.skills || resumeState.skills.length === 0) return "";
    let res = `<div class="preview-section"><div class="preview-section-heading">Skills</div><div class="preview-item-desc">`;
    if (tId === "creative") {
      res += resumeState.skills.map((s) => `<span class="skill-badge">${escapeHTML(s.name)}</span>`).join("");
    } else {
      res += resumeState.skills
        .map((s) => `<strong>${escapeHTML(s.name)}</strong>${s.category ? ` (${escapeHTML(s.category)})` : ""}`)
        .join(" &bull; ");
    }
    res += `</div></div>`;
    return res;
  };

  const buildProjects = () => {
    if (!resumeState.projects || resumeState.projects.length === 0) return "";
    let res = `<div class="preview-section"><div class="preview-section-heading">Projects</div>`;
    resumeState.projects.forEach((proj) => {
      let dateStr = "";
      if (proj.start_date && proj.end_date) dateStr = `${escapeHTML(proj.start_date)} - ${escapeHTML(proj.end_date)}`;
      else if (proj.start_date) dateStr = escapeHTML(proj.start_date);

      res += `
        <div class="preview-item">
          <div class="preview-item-header">
            <span>${escapeHTML(proj.title)}</span>
            <span style="font-weight:normal; font-size:9pt; color:#64748b;">${escapeHTML(proj.tech_stack || "")}${dateStr ? ` | ${dateStr}` : ''}</span>
          </div>
          ${proj.description ? `<div class="preview-item-desc">${escapeHTML(proj.description)}</div>` : ""}
        </div>
      `;
    });
    res += `</div>`;
    return res;
  };

  const buildCertifications = () => {
    if (!resumeState.certifications || resumeState.certifications.length === 0) return "";
    let res = `<div class="preview-section"><div class="preview-section-heading">Certifications</div>`;
    resumeState.certifications.forEach((c) => {
      res += `
        <div class="preview-item">
          <div class="preview-item-header">
            <span>${escapeHTML(c.name)}</span>
            <span style="font-weight:normal; color:#64748b;">${escapeHTML(c.issuing_organization || "")}${c.issue_date ? ` (${escapeHTML(c.issue_date)})` : ''}</span>
          </div>
        </div>
      `;
    });
    res += `</div>`;
    return res;
  };

  const buildCustomSections = () => {
    if (!resumeState.custom_sections || resumeState.custom_sections.length === 0) return "";
    let res = "";
    resumeState.custom_sections.forEach((cs) => {
      res += `
        <div class="preview-section">
          <div class="preview-section-heading">${escapeHTML(cs.section_title)}</div>
          <div class="preview-item-desc">${escapeHTML(cs.content || "")}</div>
        </div>
      `;
    });
    return res;
  };

  const photoUrl = resumeState.theme_config?.photo_url || "";
  const avatarHTML = photoUrl ? `<img src="${escapeHTML(photoUrl)}" alt="Profile Photo" class="preview-avatar">` : "";

  // Assemble HTML by Template Layout
  let html = "";
  if (tId === "two_column") {
    html = `
      <div class="two-column-wrapper">
        <div class="sidebar-col">
          ${avatarHTML}
          <div class="preview-name">${escapeHTML(p.full_name || "Your Name")}</div>
          <div class="preview-contact" style="margin-bottom: 12px;">${contactStr}</div>
          ${buildSkills()}
          ${buildCertifications()}
          ${buildCustomSections()}
        </div>
        <div class="main-col">
          ${buildSummary()}
          ${buildExperience()}
          ${buildEducation()}
          ${buildProjects()}
        </div>
      </div>
    `;
  } else if (tId === "student") {
    html = `
      <div class="preview-header">
        ${avatarHTML}
        <div class="preview-name">${escapeHTML(p.full_name || "Your Name")}</div>
        <div class="preview-contact">${contactStr}</div>
      </div>
      ${buildSummary()}
      ${buildEducation()}
      ${buildProjects()}
      ${buildSkills()}
      ${buildExperience()}
      ${buildCertifications()}
      ${buildCustomSections()}
    `;
  } else {
    html = `
      <div class="preview-header">
        ${avatarHTML}
        <div class="preview-name">${escapeHTML(p.full_name || "Your Name")}</div>
        <div class="preview-contact">${contactStr}</div>
      </div>
      ${buildSummary()}
      ${buildExperience()}
      ${buildEducation()}
      ${buildSkills()}
      ${buildProjects()}
      ${buildCertifications()}
      ${buildCustomSections()}
    `;
  }

  paper.innerHTML = html;
}

// -------------------------------------------------------------
// Profile Photo UI & Image Processing Handlers
// -------------------------------------------------------------

function showPhotoError(msg) {
  const errBox = document.getElementById("photo-error");
  if (errBox) {
    errBox.textContent = msg;
    errBox.style.display = "block";
  }
}

function hidePhotoError() {
  const errBox = document.getElementById("photo-error");
  if (errBox) {
    errBox.textContent = "";
    errBox.style.display = "none";
  }
}

function renderPhotoControl() {
  const photoUrl = resumeState.theme_config?.photo_url;
  const previewImg = document.getElementById("photo-preview-img");
  const placeholder = document.getElementById("photo-placeholder");
  const chooseBtn = document.getElementById("photo-choose-btn");
  const replaceBtn = document.getElementById("photo-replace-btn");
  const removeBtn = document.getElementById("photo-remove-btn");

  if (photoUrl && typeof photoUrl === "string" && photoUrl.trim()) {
    if (previewImg) {
      previewImg.src = photoUrl;
      previewImg.style.display = "block";
    }
    if (placeholder) placeholder.style.display = "none";
    if (chooseBtn) chooseBtn.style.display = "none";
    if (replaceBtn) replaceBtn.style.display = "inline-block";
    if (removeBtn) removeBtn.style.display = "inline-block";
  } else {
    if (previewImg) {
      previewImg.src = "";
      previewImg.style.display = "none";
    }
    if (placeholder) placeholder.style.display = "flex";
    if (chooseBtn) chooseBtn.style.display = "inline-block";
    if (replaceBtn) replaceBtn.style.display = "none";
    if (removeBtn) removeBtn.style.display = "none";
  }
}

function handlePhotoUpload(event) {
  hidePhotoError();
  const fileInput = event.target;
  const file = fileInput.files && fileInput.files[0];
  if (!file) return;

  const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
  if (!allowedTypes.includes(file.type.toLowerCase())) {
    showPhotoError("Invalid file type. Please upload a JPEG, PNG, or WebP image.");
    fileInput.value = "";
    return;
  }

  const maxSizeBytes = 2 * 1024 * 1024; // 2 MB
  if (file.size > maxSizeBytes) {
    showPhotoError("File size exceeds 2 MB limit.");
    fileInput.value = "";
    return;
  }

  const reader = new FileReader();
  reader.onload = function(e) {
    const img = new Image();
    img.onload = function() {
      try {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        const minDim = Math.min(img.width, img.height);
        const sx = (img.width - minDim) / 2;
        const sy = (img.height - minDim) / 2;
        const targetSize = Math.min(minDim, 300);
        
        canvas.width = targetSize;
        canvas.height = targetSize;
        ctx.drawImage(img, sx, sy, minDim, minDim, 0, 0, targetSize, targetSize);
        
        const processedDataUrl = canvas.toDataURL("image/jpeg", 0.85);
        if (!resumeState.theme_config) resumeState.theme_config = {};
        resumeState.theme_config.photo_url = processedDataUrl;
        
        renderPhotoControl();
        updateLivePreview();
        triggerAutosave();
      } catch (err) {
        showPhotoError("Failed to process photo. Please try another image.");
      }
    };
    img.onerror = function() {
      showPhotoError("Could not load image file. Please try another image.");
    };
    img.src = e.target.result;
  };
  reader.onerror = function() {
    showPhotoError("Failed to read image file.");
  };
  reader.readAsDataURL(file);
}

function removePhoto() {
  hidePhotoError();
  if (resumeState.theme_config) {
    delete resumeState.theme_config.photo_url;
  }
  const fileInput = document.getElementById("photo-file-input");
  if (fileInput) fileInput.value = "";
  
  renderPhotoControl();
  updateLivePreview();
  triggerAutosave();
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

function toggleMobileView(view) {
  const editorPane = document.querySelector(".editor-pane");
  const previewPane = document.querySelector(".preview-pane");
  const editTab = document.getElementById("mobile-edit-tab");
  const previewTab = document.getElementById("mobile-preview-tab");

  if (view === "preview") {
    if (editorPane) editorPane.classList.add("mobile-hidden");
    if (previewPane) previewPane.classList.add("mobile-visible");
    if (editTab) editTab.classList.remove("active");
    if (previewTab) previewTab.classList.add("active");
  } else {
    if (editorPane) editorPane.classList.remove("mobile-hidden");
    if (previewPane) previewPane.classList.remove("mobile-visible");
    if (editTab) editTab.classList.add("active");
    if (previewTab) previewTab.classList.remove("active");
  }
}

