import { API_BASE_URL } from "./config.js";

// ============================================================
// Shared API request helper
// ============================================================
//
// Handles:
// - API base URL
// - JSON requests
// - JWT authentication
// - HTTP error normalization
// - FastAPI 422 errors
// - 204 No Content
//
async function apiRequest(path, options = {}) {
  const token = localStorage.getItem("access_token");

  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
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

  // ----------------------------------------------------------
  // Unauthorized
  // ----------------------------------------------------------

  if (response.status === 401 && options.auth !== false) {
    localStorage.removeItem("access_token");
  }

  // ----------------------------------------------------------
  // HTTP errors
  // ----------------------------------------------------------

  if (!response.ok) {
    let message = "Something went wrong";

    try {
      const data = await response.json();

      // FastAPI validation error
      if (Array.isArray(data.detail)) {
        message = data.detail
          .map((item) => item.msg || "Invalid value")
          .join("; ");
      }

      // FastAPI normal HTTPException
      else if (data.detail) {
        message =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail);
      }

      // Generic API message
      else if (data.message) {
        message = data.message;
      }
    } catch {
      // Response wasn't JSON.
    }

    throw new Error(message);
  }

  // ----------------------------------------------------------
  // 204 No Content
  // ----------------------------------------------------------

  if (response.status === 204) {
    return null;
  }

  // ----------------------------------------------------------
  // JSON response
  // ----------------------------------------------------------

  return response.json();
}


// ============================================================
// Payment-session request helper
// ============================================================
//
// IMPORTANT:
//
// The Buyer Agent receives a payment URL such as:
//
// /payment.html?payment_id=7#payment_token=abc123
//
// The token is deliberately kept in the URL fragment (#).
// Browsers do NOT send the fragment to the backend.
//
// payment.html extracts the token and sends it explicitly
// to the payment-session endpoints below.
//
// ============================================================

async function paymentSessionRequest(path, options = {}) {
  const token = options.paymentToken;

  if (!token) {
    throw new Error("Missing payment session token.");
  }

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
    "X-Payment-Session": token,
  };

  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch (error) {
    throw new Error(
      "Network error: could not reach the payment server."
    );
  }

  // ----------------------------------------------------------
  // Payment session authentication failure
  // ----------------------------------------------------------

  if (response.status === 401) {
    throw new Error(
      "Payment session is invalid or has expired."
    );
  }

  // ----------------------------------------------------------
  // HTTP errors
  // ----------------------------------------------------------

  if (!response.ok) {
    let message = "Payment request failed.";

    try {
      const data = await response.json();

      if (Array.isArray(data.detail)) {
        message = data.detail
          .map((item) => item.msg || "Invalid value")
          .join("; ");
      } else if (data.detail) {
        message =
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail);
      } else if (data.message) {
        message = data.message;
      }
    } catch {
      // Keep generic error.
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}


// ============================================================
// Public API
// ============================================================

export const api = {

  // ==========================================================
  // AUTH
  // ==========================================================

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


  // ==========================================================
  // CATEGORIES
  // ==========================================================

  categories: {

    list: () =>
      apiRequest("/categories/"),

    get: (id) =>
      apiRequest(`/categories/${id}`),
  },


  // ==========================================================
  // PRODUCTS
  // ==========================================================

  products: {

    list: () =>
      apiRequest("/products/"),

    get: (id) =>
      apiRequest(`/products/${id}`),
  },


  // ==========================================================
  // CART
  // ==========================================================

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


  // ==========================================================
  // ORDERS
  // ==========================================================

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


  // ==========================================================
  // PAYMENTS
  // ==========================================================

  payments: {

    // --------------------------------------------------------
    // Normal website payment flow
    // --------------------------------------------------------

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

    get: (paymentId) =>
      apiRequest(`/payments/${paymentId}`),


    // --------------------------------------------------------
    // Buyer-Agent payment-session flow
    // --------------------------------------------------------
    //
    // These endpoints should be implemented on the backend
    // specifically for the browser payment page.
    //
    // The browser uses the short-lived payment session token
    // instead of requiring the user's normal JWT.
    //
    // --------------------------------------------------------

    session: {

      get: (paymentId, paymentToken) =>
        paymentSessionRequest(
          `/payments/session/${paymentId}`,
          {
            method: "GET",
            paymentToken,
          }
        ),

      verify: (payload, paymentToken) =>
        paymentSessionRequest(
          "/payments/session/verify",
          {
            method: "POST",
            paymentToken,
            body: JSON.stringify(payload),
          }
        ),

      fail: (paymentId, paymentToken) =>
        paymentSessionRequest(
          `/payments/session/fail/${paymentId}`,
          {
            method: "POST",
            paymentToken,
          }
        ),
    },
  },
};
