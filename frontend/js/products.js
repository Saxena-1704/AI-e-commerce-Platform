import { api } from "./api.js";
import { requireAuth } from "./auth.js";
import { escapeHtml, formatMoney, resolveImageUrl } from "./utils.js";

const grid = document.querySelector("#productGrid");
const searchInput = document.querySelector("#searchInput");
const categoryFilter = document.querySelector("#categoryFilter");
const message = document.querySelector("#productMessage");

let products = [];
let selectedCategory = "";

function showMessage(text = "", type = "error") {
  if (!message) return;
  message.textContent = text;
  message.className = text ? (type === "success" ? "alert alert-success" : "alert alert-error") : "muted";
}

function isInStock(product) {
  return Number(product.stock_quantity) > 0 && product.status !== "inactive";
}

function productCard(product) {
  const inStock = isInStock(product);
  const stockClass = inStock ? "badge-success" : "badge-danger";
  const stockText = inStock ? "In stock" : "Out of stock";
  const imageUrl = resolveImageUrl(product.image_url);

  return `
    <article class="product-card">
      <div class="product-image">${imageUrl ? `<img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(product.product_name)}">` : "Product image"}</div>
      <div class="product-info">
        <div class="product-name">${escapeHtml(product.product_name)}</div>
        <div class="product-description">${escapeHtml(product.description || "No description available.")}</div>
        <div class="price">${formatMoney(product.price)}</div>
        <div class="product-meta">
          <span class="badge ${stockClass}">${stockText}</span>
        </div>
        <div class="product-actions">
          <a class="button button-secondary" href="./product.html?id=${product.id}">View</a>
          <button class="button button-primary" type="button" data-add="${product.id}" ${inStock ? "" : "disabled"}>
            ${inStock ? "Add to Cart" : "Sold out"}
          </button>
        </div>
      </div>
    </article>
  `;
}

function render(list) {
  if (!list.length) {
    grid.innerHTML =
      selectedCategory || searchInput?.value.trim()
        ? '<p class="muted">No products match your filters.</p>'
        : '<p class="muted">No products available yet.</p>';
    return;
  }

  grid.innerHTML = list.map(productCard).join("");
}

function matchesFilters(product) {
  const query = (searchInput?.value || "").trim().toLowerCase();

  if (selectedCategory && Number(product.category_id) !== Number(selectedCategory)) {
    return false;
  }

  if (!query) return true;

  return `${product.product_name} ${product.description || ""}`
    .toLowerCase()
    .includes(query);
}

function applyFilters() {
  render(products.filter(matchesFilters));
}

searchInput?.addEventListener("input", applyFilters);

categoryFilter?.addEventListener("change", () => {
  selectedCategory = categoryFilter.value;
  applyFilters();
});

function fillCategoryFilter(categories) {
  categories.forEach((category) => {
    const option = document.createElement("option");
    option.value = String(category.id);
    option.textContent = category.category_name || category.name || `Category ${category.id}`;
    categoryFilter.appendChild(option);
  });

  const params = new URLSearchParams(window.location.search);
  const fromUrl = params.get("category");

  if (fromUrl && categories.some((category) => String(category.id) === fromUrl)) {
    categoryFilter.value = fromUrl;
    selectedCategory = fromUrl;
  }
}

grid.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-add]");
  if (!button) return;

  if (!requireAuth()) return;

  const product = products.find((entry) => String(entry.id) === button.dataset.add);
  if (!product) return;

  button.disabled = true;

  try {
    await api.cart.addItem(product.id, 1);
    showMessage(`${product.product_name} added to cart.`, "success");
  } catch (error) {
    showMessage(error.message);
    button.disabled = false;
  }
});

async function init() {
  try {
    const data = await api.products.list();
    products = Array.isArray(data) ? data : [];
  } catch (error) {
    grid.innerHTML = `<p class="muted">Could not load products: ${escapeHtml(error.message)}</p>`;
    return;
  }

  try {
    const categoryData = await api.categories.list();
    fillCategoryFilter(Array.isArray(categoryData) ? categoryData : []);
  } catch {
    // Category filtering is optional; the grid still works without it.
  }

  applyFilters();
}

init();
