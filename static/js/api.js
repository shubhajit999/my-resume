/**
 * ResumeForge API Client Module
 */
const TOKEN_KEY = "resumeforge_token";
const USER_KEY = "resumeforge_user";

class APIClient {
  constructor(baseURL = "/api/v1") {
    this.baseURL = baseURL;
  }

  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  setToken(token) {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  }

  getUser() {
    const raw = localStorage.getItem(USER_KEY);
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  setUser(user) {
    if (user) {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(USER_KEY);
    }
  }

  clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getToken();

    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers,
    };

    if (config.body && typeof config.body === "object") {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      
      if (response.status === 204) {
        return null;
      }

      const data = await response.json();

      if (!response.ok) {
        const error = new Error(data.detail || "An unexpected error occurred.");
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      if (err.status === 401) {
        this.clearSession();
      }
      throw err;
    }
  }

  // Auth Endpoints
  async register(email, fullName, password) {
    return this.request("/auth/register", {
      method: "POST",
      body: { email, full_name: fullName, password },
    });
  }

  async login(email, password) {
    const data = await this.request("/auth/login", {
      method: "POST",
      body: { email, password },
    });
    
    if (data && data.access_token) {
      this.setToken(data.access_token);
      const user = await this.getMe();
      this.setUser(user);
    }
    return data;
  }

  async getMe() {
    return this.request("/auth/me", { method: "GET" });
  }

  async logout() {
    this.clearSession();
    window.location.href = "/login";
  }

  // Resume CRUD Endpoints
  async getResumes() {
    return this.request("/resumes/", { method: "GET" });
  }

  async createResume(title, templateId = "modern") {
    return this.request("/resumes/", {
      method: "POST",
      body: { title, template_id: templateId },
    });
  }

  async exportJSON(resumeId, title = "Resume") {
    const token = this.getToken();
    const response = await fetch(`${this.baseURL}/resumes/${resumeId}/export/json`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!response.ok) {
      throw new Error("Failed to export JSON backup.");
    }
    const data = await response.json();
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.replace(/\s+/g, '_')}_backup.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  async importJSON(jsonPayload) {
    return this.request("/resumes/import", {
      method: "POST",
      body: jsonPayload,
    });
  }

  openPrintView(resumeId) {
    window.open(`${this.baseURL}/resumes/${resumeId}/print`, "_blank");
  }
}

const api = new APIClient();
