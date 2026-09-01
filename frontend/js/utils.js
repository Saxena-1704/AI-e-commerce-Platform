// Shared, framework-free helpers used by page modules.
import { API_BASE_URL } from "./config.js";

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// Backend Decimal values may arrive as numbers or strings (e.g. "2999.00").
// Number() copes with both, so keep the currency formatting here in one place.
export function formatMoney(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "Price unavailable";
  return `₹${number.toLocaleString("en-IN", {
    maximumFractionDigits: 2,
  })}`;
}

// Some list endpoints may wrap payloads; tolerate the common shapes.
export function normalizeList(data) {
  if (Array.isArray(data)) return data;
  const candidate =
    data?.items || data?.products || data?.categories || data?.results;
  return Array.isArray(candidate) ? candidate : [];
}

// Product image paths are stored relative to the API (for example,
// /uploads/products/product_1.jpg). Resolve them against the backend origin
// because the storefront is served from a different development port.
export function resolveImageUrl(imagePath) {
  if (!imagePath) return "";
  try {
    return new URL(imagePath, `${API_BASE_URL}/`).href;
  } catch {
    return "";
  }
}
