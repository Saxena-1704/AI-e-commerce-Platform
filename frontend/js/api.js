import { API_BASE_URL } from "./config.js";

async function apiRequest(path, options = {}) {
  const token = localStorage.getItem("access_token");

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = "Something went wrong";

    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // Ignore JSON parsing errors
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
  },
};