/**
 * ResumeForge Auth UI Helper Script
 */

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
      <span class="user-badge">Hello, ${user.full_name}</span>
      <button onclick="api.logout()" class="btn btn-secondary" style="width: auto; padding: 0.4rem 0.8rem; font-size: 0.85rem;">Logout</button>
    `;
  } else {
    navContainer.innerHTML = `
      <a href="/login" class="nav-link">Login</a>
      <a href="/register" class="btn btn-primary" style="width: auto; padding: 0.4rem 0.8rem; font-size: 0.85rem;">Sign Up</a>
    `;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  updateNavigation();
});
