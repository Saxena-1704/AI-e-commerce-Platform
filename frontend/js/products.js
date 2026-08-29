import { api } from "./api.js";

const grid = document.querySelector("#productGrid");
const searchInput = document.querySelector("#searchInput");
let products = [];

function money(value) {
  const number = Number(value);
  return Number.isFinite(number) ? `₹${number.toLocaleString("en-IN")}` : "Price unavailable";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

function normalizeList(data) {
  if (Array.isArray(data)) return data;
  return data?.items || data?.products || [];
}

function render(list) {
  if (!list.length) {
    grid.innerHTML = '<p class="muted">No products found.</p>';
    return;
  }

  grid.innerHTML = list.map(product => `
    <article class="product-card">
      <div class="product-image">Product image</div>
      <div class="product-info">
        <div class="product-name">${escapeHtml(product.product_name || product.name)}</div>
        <div class="product-description">${escapeHtml(product.description || "")}</div>
        <div class="product-price">${money(product.price)}</div>
        <div class="product-actions">
          <a class="button secondary" href="./product.html?id=${encodeURIComponent(product.id)}">View</a>
          <button class="button primary" type="button" disabled>Add</button>
        </div>
      </div>
    </article>
  `).join("");
}

searchInput?.addEventListener("input", () => {
  const query = searchInput.value.trim().toLowerCase();
  render(products.filter(product =>
    `${product.product_name || ""} ${product.description || ""}`.toLowerCase().includes(query)
  ));
});

async function init() {
  try {
    products = normalizeList(await api.products.list());
    render(products);
  } catch (error) {
    grid.innerHTML = `<p class="muted">Could not load products: ${escapeHtml(error.message)}</p>`;
  }
}

init();
