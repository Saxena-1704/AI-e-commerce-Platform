import { api } from "./api.js";

// ---------------------------------------------------------------------------
// Shared authentication helpers. Page modules import these rather than poking
// at localStorage directly.
// ---------------------------------------------------------------------------

export function isAuthenticated() {
  return Boolean(localStorage.getItem("access_token"));
}

// The login JWT already includes the user's role_id. This is only used to
// control visibility in the navbar; the backend remains the authority for
// protecting merchant routes.
export function isAdmin() {
  const token = localStorage.getItem("access_token");
  if (!token) return false;

  try {
    const payload = token.split(".")[1];
    const normalized = payload
      .replace(/-/g, "+")
      .replace(/_/g, "/")
      .padEnd(Math.ceil(payload.length / 4) * 4, "=");
    const decoded = JSON.parse(atob(normalized));
    return decoded.role_id === 1 || decoded.role === "admin" || decoded.role_name === "admin";
  } catch {
    return false;
  }
}

// Redirect authenticated-only pages to the login page (remembering the
// intended destination so login can bounce the user back).
export function requireAuth() {
  if (isAuthenticated()) return true;

  const inPages = window.location.pathname.includes("/pages/");
  const loginPage = inPages ? "./login.html" : "./pages/login.html";
  const next = encodeURIComponent(window.location.pathname + window.location.search);

  window.location.href = `${loginPage}?next=${next}`;
  return false;
}

// Remove the JWT, then leave for the home page.
export function logout() {
  localStorage.removeItem("access_token");
  const inPages = window.location.pathname.includes("/pages/");
  window.location.href = inPages ? "../index.html" : "./index.html";
}

// ---------------------------------------------------------------------------
// Auth-aware navbar. Target: <nav>'s <span id="navAuth" data-prefix="...">.
// data-prefix is "" on pages/ and "pages/" on the root index.html so the same
// markup resolves links correctly from both locations.
// ---------------------------------------------------------------------------
function buildAuthLinks(prefix) {
  const loggedIn = isAuthenticated();

  if (loggedIn) {
    const merchantLink = isAdmin()
      ? `<a href="./${prefix}merchant/dashboard.html">Merchant Dashboard</a>`
      : "";

    return `
      <a href="./${prefix}cart.html">Cart</a>
      <a href="./${prefix}orders.html">Orders</a>
      ${merchantLink}
      <button class="nav-button" type="button" data-logout>Logout</button>
    `;
  }

  return `
    <a href="./${prefix}login.html">Login</a>
    <a href="./${prefix}register.html">Register</a>
  `;
}

function initNavbar() {
  const placeholder = document.querySelector("#navAuth");
  if (!placeholder) return;

  const prefix = placeholder.dataset.prefix || "";
  placeholder.innerHTML = buildAuthLinks(prefix);
}

// One delegated listener handles logout buttons injected on any page.
document.addEventListener("click", (event) => {
  if (event.target.closest("[data-logout]")) {
    logout();
  }
});

// ---------------------------------------------------------------------------
// Login / Register form handling (bound only when the form exists).
// ---------------------------------------------------------------------------

const loginForm = document.querySelector("#loginForm");
const registerForm = document.querySelector("#registerForm");
const message = document.querySelector("#formMessage");

function showMessage(text, type = "error") {
  if (!message) return;
  message.textContent = text;
  message.className = `form-message ${type}`;
}

function nextDestination() {
  const next = new URLSearchParams(window.location.search).get("next");
  if (!next) return null;

  // Only allow same-site relative destinations (path + query), never
  // http(s) URLs, so a crafted ?next= cannot redirect offsite.
  if (/^https?:\/\//i.test(next) || next.startsWith("//")) return null;
  return next;
}

if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage("Logging in...", "success");

    const form = new FormData(loginForm);
    const email = form.get("email");
    const password = form.get("password");

    try {
      const data = await api.auth.login({ email, password });
      const token = data?.access_token || data?.token || null;

      if (!token) {
        throw new Error("Login succeeded but no access token was returned by the backend.");
      }

      localStorage.setItem("access_token", token);
      window.location.href = nextDestination() || "../index.html";
    } catch (error) {
      showMessage(error.message || "Login failed.");
    }
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    showMessage("Creating account...", "success");

    const form = new FormData(registerForm);
    const full_name = form.get("full_name");
    const email = form.get("email");
    const password = form.get("password");
    const phone_number = form.get("phone_number");

    try {
      await api.auth.register({
        full_name,
        email,
        password,
        phone_number: phone_number || null,
      });

      showMessage("Account created. Redirecting to login...", "success");

      setTimeout(() => {
        window.location.href = "./login.html";
      }, 700);
    } catch (error) {
      showMessage(error.message || "Registration failed.");
    }
  });
}

// Build the shared navbar on every page that uses this module.
initNavbar();
