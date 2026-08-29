import { api } from "./api.js";

const loginForm = document.querySelector("#loginForm");
const registerForm = document.querySelector("#registerForm");
const message = document.querySelector("#formMessage");

function showMessage(text, type = "error") {
  if (!message) return;
  message.textContent = text;
  message.className = `form-message ${type}`;
}

function extractToken(data) {
  // Supports common FastAPI JWT response shapes.
  return data?.access_token || data?.token || data?.data?.access_token || null;
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
      const token = extractToken(data);

      if (!token) {
        throw new Error("Login succeeded but no access token was returned by the backend.");
      }

      localStorage.setItem("access_token", token);
      window.location.href = "../index.html";
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

      showMessage(
        "Account created. Redirecting to login...",
        "success"
      );

      setTimeout(() => {
        window.location.href = "./login.html";
      }, 700);

    } catch (error) {
      showMessage(error.message || "Registration failed.");
    }
  });
}