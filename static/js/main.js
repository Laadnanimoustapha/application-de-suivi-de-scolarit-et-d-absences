// ============================================================
//  PFE — Frontend API Client
//  Connects to: https://castel47-pfe-backend.hf.space

const API = (() => {

  const BASE_URL = "https://castel47-pfe-backend.hf.space";

  async function request(endpoint, options = {}) {
    const url = `${BASE_URL}${endpoint}`;

    const defaultHeaders = {
      "Content-Type": "application/json",
    };

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);

      // Parse JSON body (FastAPI always returns JSON)
      const data = await response.json();

      if (!response.ok) {
        // FastAPI validation errors (422) carry detail info
        const errorMsg =
          data.detail
            ? (Array.isArray(data.detail)
                ? data.detail.map((e) => e.msg).join(", ")
                : data.detail)
            : `Server error ${response.status}`;
        throw new Error(errorMsg);
      }

      return { success: true, data };
    } catch (error) {
      console.error(`[API] ${endpoint} →`, error.message);
      return { success: false, error: error.message };
    }
  }

  // ── Endpoint methods ───────────────────────────────────────

  /** GET /  —  Check if the backend is alive */
  async function checkServerStatus() {
    return request("/");
  }

  /** POST /login/etudiant  —  Student login */
  async function loginEtudiant(email, password) {
    return request("/login/etudiant", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  /**
   * POST /login/professeur  —  Professor login
   * (Add this route to app.py when ready)
   */
  async function loginProfesseur(email, password) {
    return request("/login/professeur", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  /**
   * POST /login/admin  —  Admin login
   * (Add this route to app.py when ready)
   */
  async function loginAdmin(username, password) {
    return request("/login/admin", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  }

  // ── Session / Auth helpers ─────────────────────────────────

  /** Save user session after successful login */
  function saveSession(role, userData) {
    const session = {
      role,          // "etudiant" | "professeur" | "admin"
      ...userData,
      loggedInAt: new Date().toISOString(),
    };
    localStorage.setItem("pfe_session", JSON.stringify(session));
  }

  /** Retrieve the current session (or null) */
  function getSession() {
    const raw = localStorage.getItem("pfe_session");
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  /** Destroy session (logout) */
  function clearSession() {
    localStorage.removeItem("pfe_session");
  }

  /** Check if a user is currently logged in */
  function isLoggedIn() {
    return getSession() !== null;
  }

  // ── Navigation helpers ─────────────────────────────────────

  /** Redirect to the correct dashboard based on role */
  function redirectToDashboard(role) {
    const dashboards = {
      etudiant:   "../templates/dashboard_eleve.html",
      professeur: "../templates/dashboard_prof.html",
      admin:      "../templates/dashboard_admin.html",
    };
    const target = dashboards[role] || "../templates/index.html";
    window.location.href = target;
  }

  /** Redirect to login page if not authenticated */
  function requireAuth() {
    if (!isLoggedIn()) {
      window.location.href = "../templates/login.html";
    }
  }

  /** Logout and redirect to login page */
  function logout() {
    clearSession();
    window.location.href = "../templates/login.html";
  }

  // ── Unified login handler ──────────────────────────────────

  /**
   * Handles the complete login flow:
   *  1. Calls the right endpoint based on role
   *  2. Checks the response status
   *  3. Saves session & redirects on success
   *  4. Returns an error message on failure
   *
   * @param {"etudiant"|"professeur"|"admin"} role
   * @param {Object} credentials - { email, password } or { username, password }
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async function login(role, credentials) {
    let result;

    switch (role) {
      case "etudiant":
        result = await loginEtudiant(credentials.email, credentials.password);
        break;
      case "professeur":
        result = await loginProfesseur(credentials.email, credentials.password);
        break;
      case "admin":
        result = await loginAdmin(credentials.username, credentials.password);
        break;
      default:
        return { success: false, message: "Unknown role" };
    }

    // Network / server error
    if (!result.success) {
      return { success: false, message: result.error };
    }

    // Backend returned a response — check status field
    const status = result.data.statu || result.data.status;

    if (status && status.toLowerCase().includes("success")) {
      saveSession(role, credentials);
      redirectToDashboard(role);
      return { success: true, message: "Login successful" };
    }

    return { success: false, message: status || "Login failed" };
  }

  // ── Public API ─────────────────────────────────────────────
  return {
    BASE_URL,
    checkServerStatus,
    loginEtudiant,
    loginProfesseur,
    loginAdmin,
    login,
    saveSession,
    getSession,
    clearSession,
    isLoggedIn,
    redirectToDashboard,
    requireAuth,
    logout,
  };
})();

// ── Startup: verify backend connection ───────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  const res = await API.checkServerStatus();
  if (res.success) {
    console.log("✅ Backend connected:", res.data);
  } else {
    console.warn("⚠️  Backend unreachable:", res.error);
  }
});
