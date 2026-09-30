/**
 * MyResume Auth UI Helper & Theme Management Script
 * Preserves all authentication contracts and provides global light/dark theme persistence.
 */

const THEME_KEY = "myresume_theme";

function getTheme() {
  return localStorage.getItem(THEME_KEY) || "light";
}

function setTheme(theme) {
  localStorage.setItem(THEME_KEY, theme);
  applyTheme(theme);
}

function applyTheme(theme) {
  const isDark = theme === "dark";
  document.documentElement.classList.toggle("dark-mode", isDark);
  if (document.body) {
    document.body.classList.toggle("dark-mode", isDark);
  }
  updateThemeToggleButtons(theme);
}

function toggleTheme() {
  const current = getTheme();
  const next = current === "dark" ? "light" : "dark";
  setTheme(next);
}

function updateThemeToggleButtons(theme) {
  const btns = document.querySelectorAll("#theme-toggle-btn");
  if (!btns.length) return;
  const isDark = theme === "dark";
  btns.forEach(btn => {
    btn.setAttribute("aria-label", isDark ? "Switch to Light Mode" : "Switch to Dark Mode");
    btn.innerHTML = `
      <span class="sidebar-nav-icon">${isDark ? '☀️' : '🌙'}</span>
      <span>${isDark ? 'Light Mode' : 'Dark Mode'}</span>
    `;
  });
}

// Immediate theme execution to prevent UI flicker on page load
(function() {
  const currentTheme = localStorage.getItem(THEME_KEY) || "light";
  if (currentTheme === "dark") {
    document.documentElement.classList.add("dark-mode");
  }
})();

function showAlert(elementId, message, type = "error") {
  const alertEl = document.getElementById(elementId);
  if (!alertEl) return;
  alertEl.textContent = message;
  alertEl.className = `alert alert-${type}`;
  alertEl.style.display = "block";
}

function hideAlert(elementId) {
  const alertEl = document.getElementById(elementId);
  if (alertEl) {
    alertEl.style.display = "none";
  }
}

function setBtnLoading(btnId, isLoading, defaultText = "Submit") {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  if (isLoading) {
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Processing...`;
  } else {
    btn.disabled = false;
    btn.textContent = defaultText;
  }
}

function requireAuth() {
  const token = api.getToken();
  if (!token) {
    window.location.href = "/login";
  }
}

function redirectIfAuthenticated() {
  const token = api.getToken();
  if (token) {
    window.location.href = "/dashboard";
  }
}

function updateNavigation() {
  const user = api.getUser();
  const navContainer = document.getElementById("nav-right");
  if (!navContainer) return;

  if (user && api.getToken()) {
    navContainer.innerHTML = `
      <span class="user-badge">Hello, ${escapeHTML(user.full_name)}</span>
      <button onclick="api.logout()" class="btn btn-secondary" style="width: auto; padding: 0.4rem 0.9rem; font-size: 0.85rem;">Logout</button>
    `;
  } else {
    navContainer.innerHTML = `
      <a href="/login" class="nav-link">Login</a>
      <a href="/register" class="btn btn-primary" style="width: auto; padding: 0.4rem 0.9rem; font-size: 0.85rem;">Sign Up</a>
    `;
  }
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

/**
 * Initializes subtle mouse-follow 3D tilt interaction for decorative preview cards
 */
function init3DTilt() {
  const card = document.getElementById("tilt-resume-card");
  if (!card) return;

  // Respect prefers-reduced-motion
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }

  const stage = card.closest(".resume-3d-stage") || card.parentElement;
  if (!stage) return;

  stage.addEventListener("mousemove", (e) => {
    const rect = stage.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -12;
    const rotateY = ((x - centerX) / centerX) * 12;

    card.style.transform = `rotateY(${rotateY.toFixed(2)}deg) rotateX(${rotateX.toFixed(2)}deg)`;
  });

  stage.addEventListener("mouseleave", () => {
    card.style.transform = `rotateY(-8deg) rotateX(6deg)`;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  applyTheme(getTheme());
  updateNavigation();
  init3DTilt();
});
