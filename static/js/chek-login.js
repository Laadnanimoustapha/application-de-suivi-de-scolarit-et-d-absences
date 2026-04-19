// ============================================================
//  PFE — Login Check Guard
//  Must be loaded AFTER main.js (which defines the API object)
// ============================================================

/**
 * Check if the user is logged in.
 * - If yes  → redirect them to their dashboard (skip login page).
 * - If no   → stays on the current page (login / index).
 *
 * Use on pages where an authenticated user should NOT stay
 * (e.g. login.html, index.html).
 */
function checkAlreadyLoggedIn() {
  const session = API.getSession();
  if (session && session.role) {
    API.redirectToDashboard(session.role);
  }
}

/**
 * Protect a page — kick unauthenticated users to login.
 * Use on dashboard pages.
 */
function requireLogin() {
  API.requireAuth();
}

/**
 * Get the current user's info from session.
 * @returns {Object|null}
 */
function getCurrentUser() {
  return API.getSession();
}