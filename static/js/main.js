// PFE — Frontend API Client

const API = (() => {
  const BASE_URL = "";

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
      const data = await response.json();

      if (!response.ok) {
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

  async function checkServerStatus() {
    return request("/");
  }

  async function loginEtudiant(email, password) {
    return request("/login/etudiant", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async function loginProfesseur(email, password) {
    return request("/login/professeur", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async function loginAdmin(username, password) {
    return request("/login/admin", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
  }

  function saveSession(role, userData) {
    const session = {
      role,
      ...userData,
      loggedInAt: new Date().toISOString(),
    };
    localStorage.setItem("pfe_session", JSON.stringify(session));
  }

  function getSession() {
    const raw = localStorage.getItem("pfe_session");
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  function clearSession() {
    localStorage.removeItem("pfe_session");
  }

  function isLoggedIn() {
    return getSession() !== null;
  }

  function redirectToDashboard(role) {
    const dashboards = {
      etudiant:   "../templates/dashboard_eleve.html",
      professeur: "../templates/dashboard_prof.html",
      admin:      "../templates/dashboard_admin.html",
    };
    const target = dashboards[role] || "../templates/index.html";
    window.location.href = target;
  }

  function requireAuth() {
    if (!isLoggedIn()) {
      window.location.href = "../templates/login.html";
    }
  }

  function logout() {
    clearSession();
    window.location.href = "../templates/login.html";
  }

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

    if (!result.success) {
      return { success: false, message: result.error };
    }

    const status = result.data.statu || result.data.status;

    if (status && status.toLowerCase().includes("success")) {
      saveSession(role, credentials);
      redirectToDashboard(role);
      return { success: true, message: "Login successful" };
    }

    return { success: false, message: status || "Login failed" };
  }

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

// Auth Guard Functions (Moved from chek-login.js)
function checkAlreadyLoggedIn() {
  const session = API.getSession();
  if (session && session.role) {
    API.redirectToDashboard(session.role);
  }
}

function requireLogin() {
  API.requireAuth();
}

function getCurrentUser() {
  return API.getSession();
}

document.addEventListener("DOMContentLoaded", async () => {
  const res = await API.checkServerStatus();
  if (res.success) {
    console.log("Backend connected:", res.data);
  } else {
    console.warn("Backend unreachable:", res.error);
  }
});
