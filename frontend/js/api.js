import { API_BASE_URL } from "./config.js";

// Shared request helper. All backend communication goes through this module.
//
// Handles:
//  - base URL concatenation (page code never contains backend URLs)
//  - JSON content-type when a body is present
//  - automatic JWT attachment from localStorage
//  - HTTP error normalization (FastAPI `detail`, including 422 arrays)
//  - 204 No Content
async function apiRequest(path, options = {}) {
  const token = localStorage.getItem("access_token");

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch (error) {
    throw new Error(
      "Network error: could not reach the server. Check that the backend is running."
    );
  }

  if (response.status === 401 && options.auth !== false) {
    // Token missing/expired/invalid. Drop it so protected redirects work.
    localStorage.removeItem("access_token");
  }

  if (!response.ok) {
    let message = "Something went wrong";

    try {
      const data = await response.json();

      if (Array.isArray(data.detail)) {
        // FastAPI 422 validation: detail is a list of {loc, msg, type}
        message = data.detail
          .map((item) => item.msg || "Invalid value")
          .join("; ");
      } else if (data.detail) {
        message = data.detail;
      } else if (data.message) {
        message = data.message;
      }
    } catch {
      // Non-JSON error body; keep the generic message.
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {

  auth: {
    register: (payload) =>
      apiRequest("/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    login: (payload) =>
      apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
        auth: false,
      }),

    testProtected: () =>
      apiRequest("/auth/test-protected"),
  },

  categories: {
    list: () => apiRequest("/categories/"),

    get: (id) =>
      apiRequest(`/categories/${id}`),
  },

  products: {
    list: () =>
      apiRequest("/products/"),

    get: (id) =>
      apiRequest(`/products/${id}`),
  },

  cart: {
    get: () =>
      apiRequest("/cart/"),

    addItem: (product_id, quantity = 1) =>
      apiRequest("/cart/items", {
        method: "POST",
        body: JSON.stringify({
          product_id,
          quantity,
        }),
      }),

    updateItem: (item_id, quantity) =>
      apiRequest(`/cart/items/${item_id}`, {
        method: "PUT",
        body: JSON.stringify({
          quantity,
        }),
      }),

    removeItem: (item_id) =>
      apiRequest(`/cart/items/${item_id}`, {
        method: "DELETE",
      }),
  },

  orders: {
    checkout: () =>
      apiRequest("/orders/checkout", {
        method: "POST",
      }),

    list: () =>
      apiRequest("/orders/"),

    get: (id) =>
      apiRequest(`/orders/${id}`),
  },

  payments: {
    create: (orderId) =>
      apiRequest(`/payments/create/${orderId}`, {
        method: "POST",
      }),

    verify: (payload) =>
      apiRequest("/payments/verify", {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    fail: (orderId) =>
      apiRequest(`/payments/fail/${orderId}`, {
        method: "POST",
      }),
  },
};
